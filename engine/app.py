import time
from scene import Scene
from view import View

app = None
app_screen = None


def get_screen_size():
    if not app_screen:
        return 640, 480
    return app_screen.width(), app_screen.height()


def get_screen():
    global app_screen
    if app_screen:
        return app_screen
    try:
        import os.path  # Test for full python (simulation) vs. platform micropython
        from sim_screen import screen
        app_screen = screen
        screen.start()
        return screen
    except ImportError:  # os.path is not implemented on micropython
        from gpu_screen import screen
        pass
        # from screen import
    return None


class Application(object):
    def __init__(self, scale=1.0):
        global app
        app = self
        self.scene = Scene()
        self.view = View()
        self.fps = 30
        self.keys = []
        self.last_ts = time.time()
        get_screen().set_transparent_color(True, 0x20)

    def calc_dt(self):
        cur = time.time()
        dt = cur - self.last_ts
        self.last_ts = cur
        if dt>0:
            self.fps = 0.9 * self.fps + 0.1 / dt
        return dt

    @staticmethod
    def flip():
        get_screen().flip()

    def clear(self, color=(192, 128, 255)):
        pass

    def on_key(self, key):
        pass

    def on_click(self, pos):
        pass

    def handle_events(self):
        return True

    def draw(self, view):
        self.scene.draw(view)

    def loop(self, dt):
        self.scene.advance(dt)
        self.draw(self.view)
        return True

    def run(self):
        while self.handle_events():
            if not self.loop(self.calc_dt()):
                break
            self.flip()

# EXPORT
# def key_down(key_name):
#     if key_name not in KeyCodes:
#        return False
#     code = KeyCodes.get(key_name)
#     return app.keys[code]
