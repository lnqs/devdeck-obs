import os
import logging
from pathlib import Path
import threading
from time import sleep
from urllib.request import Request
import yaml
from cerberus import Validator
from obswebsocket import obsws, requests
import obswebsocket.exceptions
from devdeck.settings.validation_error import ValidationError

logger = logging.getLogger('devdeck')

settings_schema = {
    'host': { 'type': 'string' },
    'port': { 'type': 'integer' },
    'password': { 'type': 'string' },
}

default_settings = {
    'host': 'localhost',
    'port': 4444,
    'password': ''
}

class ConnectionEstablished(obswebsocket.events.Baseevents):
    def __init__(self):
        obswebsocket.events.Baseevents.__init__(self)
        self.name = 'ConnectionEstablished'


class ConnectionLost(obswebsocket.events.Baseevents):
    def __init__(self):
        obswebsocket.events.Baseevents.__init__(self)
        self.name = 'ConnectionLost'


class EmulatedStreamStatus(obswebsocket.events.Baseevents):
    def __init__(self):
        obswebsocket.events.Baseevents.__init__(self)
        self.name = 'EmulatedStreamStatus'


class OBS:
    def __init__(self):
        settings = self._load_settings()
        self._running = False
        self._was_connected = False
        self._obsws = obsws(settings['host'], settings['port'], settings['password'])
        self._current_scene = None
        self._stream_status = None

    @property
    def connected(self):
        return self._obsws.ws and self._obsws.ws.connected

    @property
    def current_scene(self):
        return self._current_scene
    
    @property
    def stream_status(self):
        return self._stream_status

    def set_current_scene(self, scene):
        logger.info(f'Setting OBS scene to {scene}')
        self._perform_request(requests.SetCurrentScene(scene))

    def start_streaming(self):
        logger.info(f'Starting OBS streaming')
        self._perform_request(requests.StartStreaming())

    def stop_streaming(self):
        logger.info(f'Stopping OBS streaming')
        self._perform_request(requests.StopStreaming())

    def start_recording(self):
        logger.info(f'Starting OBS recording')
        self._perform_request(requests.StartRecording())

    def stop_recording(self):
        logger.info(f'Stopping OBS recording')
        self._perform_request(requests.StopRecording())

    def register(self, function, event=None):
        return self._obsws.register(function, event)

    def unregister(self, function, event=None):
        return self._obsws.unregister(function, event)

    def _initialize(self):
        logger.info('Initializing OBS integration')
        self._running = True
        self.thread = threading.Thread(target=self._connection_loop)
        self.thread.start()
        self._obsws.register(self._scene_switched, obswebsocket.events.SwitchScenes)

    def _dispose(self):
        logger.info('Disposing OBS integration')
        self._running = False
        self.thread.join()
        self._obsws.disconnect()

    def _perform_request(self, request):
        if self.connected:
            self._obsws.call(request)

    def _load_settings(self):
        filename = os.path.join(str(Path.home()), '.devdeck', 'obs.yml')

        try:
            with open(filename, 'r') as stream:
                settings = yaml.safe_load(stream)
                validator = Validator(settings_schema)
                if validator.validate(settings, settings_schema):
                    return settings
                raise ValidationError(validator.errors)
        except FileNotFoundError:
            logger.warning('No settings file detected, writing default one!')
            with open(filename, 'w') as stream:
                stream.write(yaml.dump(default_settings))

        return default_settings

    def _connection_loop(self):
        while self._running:
            if self.connected:
                # For some reason Recording* events aren't triggered. So let's poll.
                status = self._obsws.call(requests.GetStreamingStatus())
                if not self._stream_status or status.datain != self._stream_status.datain:
                    logger.info('Stream status changed')
                    self._stream_status = status
                    self._obsws.eventmanager.trigger(EmulatedStreamStatus())
            else:
                if self._was_connected:
                    logger.info('Connection to OBS lost, trying to reconnect')
                    self._was_connected = False
                    self._obsws.eventmanager.trigger(ConnectionLost())
                try:
                    self._obsws.connect()
                    self._was_connected = True
                    self._current_scene = self._obsws.call(requests.GetCurrentScene()).getName()
                    logger.info('Connection to OBS established')
                    self._obsws.eventmanager.trigger(ConnectionEstablished())
                except obswebsocket.exceptions.ConnectionFailure:
                    pass

            sleep(1.0)

    def _scene_switched(self, event):
        self._current_scene = event.getSceneName()
        logger.info(f'OBS scene switched to {self._current_scene}')


class OBSWrapper:
    def __init__(self):
        self.implementation = None
        self.users = 0

    def acquire(self):
        self.users += 1
        if self.users == 1:
            self.implementation = OBS()
            self.implementation._initialize()

    def release(self):
        self.users -= 1
        if self.users == 0:
            self.implementation._dispose()
            self.implementation = None

    def __getattr__(self, name):
        return getattr(self.implementation, name)


obs = OBSWrapper()