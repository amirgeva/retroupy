import random
import os
import sys

cwd = os.getcwd()
sys.path.append(cwd[0:max(cwd.rfind('/'), cwd.rfind('\\'))])

from engine import *
from sim.kbd import is_pressed


class Monster(Entity):
    def __init__(self):
        super().__init__(AnimatedSprite())
        names = ['bird', 'mush', 'pig', 'rock', 'slime', 'snail']
        name = names[random.randint(0, len(names) - 1)]
        self.anim.load(name + '.json', {'BaseVelocity': 30.0})
        self.anim.set_active_sequence('WalkRight')
        self.range = (0, 0)
        self.speed = 10

    def set_range(self, mn, mx):
        self.range = (mn, mx)
        self.set_velocity(self.speed, 0)

    def advance(self, dt):
        p = self.get_position()
        v = self.get_velocity()
        if (p.x >= self.range[1] and v.x > 0) or (p.x < self.range[0] and v.x < 0):
            v.x = -v.x
            direction = 'Right' if v.x > 0 else 'Left'
            self.anim.set_active_sequence(f'Walk{direction}')
            self.set_velocity(v)
        return super().advance(dt)


class Player(Entity):
    def __init__(self):
        super().__init__(AnimatedSprite())
        self.sprite = self.anim
        self.sprite.load('char.json')
        self.anim.set_active_sequence('StandRight')
        self.set_position(300, 200)
        self.set_accel(0, 200)
        self.stopped = True
        self.right = False
        self.on_ground = False
        self.ground_dt = 1000

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
        a = self.get_accel()
        max_vel = 150
        if abs(v.x) > max_vel:
            v.x = max_vel if v.x > 0 else -max_vel
            self.set_velocity(v)
        if self.on_ground:
            m = -3
            if a.x == 0:
                m = -8
            self.set_external_force(vector2(m * v.x, 0))
        else:
            self.set_external_force(vector2(0, 0))

    def handle_events(self):
        a = self.get_accel()
        v = self.get_velocity()
        if self.on_ground:
            if is_pressed('left'):
                a.x = -250
            elif is_pressed('right'):
                a.x = 250
            else:
                a.x = 0
        else:
            a.x = 0
        if is_pressed('up'):
            if self.on_ground:
                self.ground_dt = 0.0
                v.y = -120
            else:
                if self.ground_dt < 0.5:
                    v.y = -120+30*self.ground_dt
            self.on_ground = False
            self.set_velocity(v)
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
        if self.ground_dt < 0.5:
            self.ground_dt = self.ground_dt + dt
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
