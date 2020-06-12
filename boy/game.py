from app import get_screen, Application
from sprite import AnimatedSprite, StaticSprite
from entity import Entity
from utils import Point
from sim_keyboard import is_pressed
import random


class Player(Entity):
    def __init__(self):
        super().__init__(AnimatedSprite())
        self.sprite = self.anim
        self.sprite.load('char.json')
        self.set_position(300, 200)
        self.set_velocity(0, 100)
        # self.set_accel(0,100)

    def collision(self, other, col_point):
        self.revert()
        v = self.get_velocity()
        v.y = 0
        self.set_velocity(v)


def generate_platform(size):
    anim = AnimatedSprite()
    anim.load('platform.json')
    center = anim.get_sequence_by_name('Center')
    res = [None] * size
    res[0] = anim.get_sequence_by_name('Left')[0]
    res[-1] = anim.get_sequence_by_name('Right')[0]
    for i in range(1, size - 1):
        res[i] = center[random.randint(0, len(center) - 1)]
    return res


class GameApplication(Application):
    def __init__(self):
        super().__init__()
        self.player = Player()
        self.scene.add(self.player)
        self.add_static_sprites(generate_platform(6), Point(240, 300))

    def add_static_sprites(self, sprites, pos):
        for sprite in sprites:
            e = Entity(StaticSprite(sprite))
            e.dynamic = False
            e.set_position(pos)
            self.scene.add(e)
            pos = pos + Point(32, 0)

    def handle_events(self):
        v = self.player.get_velocity()
        if is_pressed('left'):
            v.x = -10
        if is_pressed('right'):
            v.x = 10
        self.player.set_velocity(v)
        return super().handle_events()

    def draw(self, view):
        r = view.get_rect()
        scr = get_screen()
        scr.bg_color(0x7D1F)
        scr.fill_rect(r.tl.x, r.tl.y, r.br.x, r.br.y)
        super().draw(view)


app = GameApplication()
app.run()
