import random
import os
import sys

cwd = os.getcwd()
sys.path.append(cwd[0:max(cwd.rfind('/'), cwd.rfind('\\'))])

from engine import *
from sim.kbd import is_pressed


class Player(Entity):
    def __init__(self):
        super().__init__(AnimatedSprite())
        self.sprite = self.anim
        self.sprite.load('char.json')
        self.anim.set_active_sequence('StandRight')
        self.set_position(300, 200)
        # self.set_velocity(0, 100)
        self.set_accel(0, 200)
        self.stopped = True
        self.right = False
        self.on_ground = False

    def check_for_stop(self):
        v = self.get_velocity()
        if 0 < abs(v.x) <= 0.1:
            direction = 'Right' if v.x > 0 else 'Left'
            v.x = 0.0
            self.set_velocity(v)
            self.anim.set_active_sequence(f'Stand{direction}')
            self.stopped = True

    def check_for_motion(self):
        vx = self.get_velocity().x
        right = vx > 0
        if vx != 0 and (self.stopped or right != self.right):
            self.anim.set_active_sequence('WalkLeft' if vx < 0 else 'WalkRight')
            self.stopped = False
            self.right = right

    def check_max_velocity(self):
        v = self.get_velocity()
        if abs(v.x) > 100:
            v.x = 100 if v.x > 0 else -100
            self.set_velocity(v)
        if self.on_ground:
            self.set_external_force(vector2(-3 * v.x, 0))
        else:
            self.set_external_force(vector2(0, 0))

    def handle_events(self):
        a = self.get_accel()
        v = self.get_velocity()
        if self.on_ground:
            if is_pressed('left'):
                a.x = -200
            elif is_pressed('right'):
                a.x = 200
            else:
                a.x = 0
            if is_pressed('up'):
                v.y = -150
                self.on_ground = False
                self.set_velocity(v)
        else:
            a.x = 0
        direction = 'Right' if self.right else 'Left'
        if is_pressed('x'):
            self.anim.set_active_sequence(f'Kick{direction}')
        elif self.anim.get_active_sequence_name().startswith('Kick'):
            act = 'Walk' if abs(v.x) > 0.1 else 'Stand'
            self.anim.set_active_sequence(f'{act}{direction}')
        if is_pressed('z'):
            self.anim.set_active_sequence(f'Punch{direction}')
        elif self.anim.get_active_sequence_name().startswith('Punch'):
            act = 'Walk' if abs(v.x) > 0.1 else 'Stand'
            self.anim.set_active_sequence(f'{act}{direction}')

        self.set_accel(a)

    def advance(self, dt):
        self.check_for_stop()
        self.check_for_motion()
        self.check_max_velocity()
        return super().advance(dt)

    def collision(self, other, col_point):
        if col_point.y > 28 and self.get_velocity().y >= 0:
            self.revert(False, True)
            v = self.get_velocity()
            v.y = 0
            self.set_velocity(v)
            self.on_ground = True


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
        self.add_static_sprites(generate_platform(14), Point(100, 300))
        self.bg = rgb(212, 189, 127)

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
