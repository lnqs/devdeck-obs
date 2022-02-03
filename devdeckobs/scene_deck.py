import logging
import os
from devdeck_core.decks.deck_controller import DeckController
import obswebsocket.events
from devdeckobs.scene_control import SceneControl
from devdeckobs.obs import obs, ConnectionEstablished, ConnectionLost

logger = logging.getLogger('devdeck')

class SceneDeck(DeckController):
    def __init__(self, key_no, **kwargs):
        super().__init__(key_no, **kwargs)

    def initialize(self):
        obs.acquire()
        self.update_icon()
        obs.register(self.connection_state_changed, ConnectionEstablished)
        obs.register(self.connection_state_changed, ConnectionLost)
        obs.register(self.scene_switched, obswebsocket.events.SwitchScenes)

    def deck_controls(self):
        for i, scene in enumerate(self.settings['scenes']):
            self.register_control(i, SceneControl, scene=scene, icon=self.settings['icon'])

    def update_icon(self):
        with self.deck_context() as context:
            with context.renderer() as r:
                r.image(os.path.expanduser(self.settings['icon'])) \
                    .width(380) \
                    .height(380) \
                    .center_horizontally() \
                    .end()
                r.text((obs.current_scene or '') if obs.connected else 'disconnected') \
                    .y(380) \
                    .center_horizontally() \
                    .font_size(85) \
                    .end()

                if not obs.connected:
                    r.colorize('#222')

    def connection_state_changed(self, _event):
        self.update_icon()

    def scene_switched(self, _event):
        self.update_icon()

    def settings_schema(self):
        return {
            'icon': {
                'type': 'string',
                'required': True,
            },
            'scenes': {
                'type': 'list',
                'schema': {
                    'type': 'string'
                },
                'required': True,
            }
        }

    def dispose(self):
        obs.release()