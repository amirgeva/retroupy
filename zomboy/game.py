import random
import os
import sys

cwd = os.getcwd()
sys.path.append(cwd[0:max(cwd.rfind('/'), cwd.rfind('\\'))])

from engine import *
from sim.kbd import is_pressed
from monster import Monster
from player import Player


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
        # self.add_static_sprites(generate_platform(14), Point(100, 320))
        # self.add_static_sprites(generate_platform(6), Point(300, 320 - 64))
        self.generate_level()
        self.bg = rgb(212, 189, 127)

    def generate_level(self):
        rows = BitMatrix(30, 6)
        rows.setall(False)
        for _ in range(100):
            platform = generate_platform(random.randint(3, 7))
            row_index = random.randint(0, 5)
            col_index = random.randint(0, 19 - len(platform))
            failed = False
            for i in range(col_index - 2, col_index + len(platform) + 2):
                if rows.get(i, row_index):
                    failed = True
            if not failed:
                for i in range(len(platform)):
                    rows.set(i + col_index, row_index, True)
                self.add_static_sprites(platform, Point(col_index * 32, row_index * 64 + 32))
                if random.randint(0, 2) > 0:
                    m = Monster()
                    m.set_position(col_index * 32 + 32, row_index * 64)
                    m.set_range(col_index * 32 + 16, (col_index + len(platform) - 1) * 32 - 16)
                    self.scene.add(m)
        self.add_static_sprites(generate_platform(18), Point(32, 416))

    def add_static_sprites(self, sprites, pos):
        for sprite in sprites:
            e = Entity(StaticSprite(sprite))
            e.dynamic = False
            e.set_position(pos)
            self.scene.add(e)
            pos = pos + Point(32, 0)

    def handle_events(self):
        self.player.handle_events()
        if is_pressed('escape'):
            return False
        return super().handle_events()

    def draw(self, view):
        r = view.get_rect()
        scr = get_screen()
        scr.bg_color(self.bg)
        scr.fill_rect(r.tl.x, r.tl.y, r.br.x, r.br.y)
        super().draw(view)


def main():
    app = GameApplication()
    app.run()


if __name__ == '__main__':
    main()
