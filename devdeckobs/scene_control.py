import logging
import os
from devdeck_core.controls.deck_control import DeckControl
import obswebsocket.events
from devdeckobs.obs import obs, ConnectionEstablished, ConnectionLost

logger = logging.getLogger('devdeck')

class SceneControl(DeckControl):
    def __init__(self, key_no, **kwargs):
        super().__init__(key_no, **kwargs)

    def initialize(self):
        obs.acquire()
        obs.register(self.connection_state_changed, ConnectionEstablished)
        obs.register(self.connection_state_changed, ConnectionLost)
        obs.register(self.scene_switched, obswebsocket.events.SwitchScenes)
        self.update_icon()

    def update_icon(self):
        with self.deck_context() as context:
            with context.renderer() as r:
                r.image(os.path.expanduser(self.settings['icon'])) \
                    .width(380) \
                    .height(380) \
                    .center_horizontally() \
                    .end()
                r.text(self.settings['scene']) \
                    .y(380) \
                    .center_horizontally() \
                    .font_size(85) \
                    .end()
                if not obs.connected:
                    r.colorize('#222')
                elif obs.current_scene == self.settings['scene']:
                    r.colorize('red')

    def connection_state_changed(self, _event):
        self.update_icon()

    def scene_switched(self, _event):
        self.update_icon()

    def pressed(self):
        obs.set_current_scene(self.settings['scene'])

    def dispose(self):
        obs.release()
