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
        self.sprite.load('rsc/char.json')
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
                    v.y = -120 + 30 * self.ground_dt
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
