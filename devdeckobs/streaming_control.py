import logging
import os
from devdeck_core.controls.deck_control import DeckControl
from devdeckobs.obs import obs, ConnectionEstablished, ConnectionLost, EmulatedStreamStatus

logger = logging.getLogger('devdeck')

class StreamingControl(DeckControl):
    def __init__(self, key_no, **kwargs):
        super().__init__(key_no, **kwargs)

    def initialize(self):
        obs.acquire()
        obs.register(self.connection_state_changed, ConnectionEstablished)
        obs.register(self.connection_state_changed, ConnectionLost)
        obs.register(self.status_changed, EmulatedStreamStatus)
        self.update_icon()

    def update_icon(self):
        with self.deck_context() as context:
            with context.renderer() as r:
                if not obs.connected or not obs.stream_status:
                    text = 'disconnected'
                    color = '#222'
                elif obs.stream_status.getStreaming():
                    text = obs.stream_status.getStreamTimecode().rsplit('.', 1)[0]
                    color = 'red'
                else:
                    text = 'stopped'
                    color = 'white'

                r.image(os.path.expanduser(self.settings['icon'])) \
                    .width(380) \
                    .height(380) \
                    .center_horizontally() \
                    .end()
                r.text(text) \
                    .y(380) \
                    .center_horizontally() \
                    .font_size(85) \
                    .end()

                r.colorize(color)

    def connection_state_changed(self, _event):
        self.update_icon()

    def status_changed(self, _event):
        self.update_icon()

    def pressed(self):
        if obs.connected and obs.stream_status:
            if obs.stream_status.getStreaming():
                obs.stop_streaming()
            else:
                obs.start_streaming()

    def dispose(self):
        obs.release()
