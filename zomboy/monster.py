import random
import os
import sys

cwd = os.getcwd()
sys.path.append(cwd[0:max(cwd.rfind('/'), cwd.rfind('\\'))])

from engine import *


class Monster(Entity):
    def __init__(self):
        super().__init__(AnimatedSprite())
        names = ['bird', 'mush', 'pig', 'rock', 'slime', 'snail']
        name = names[random.randint(0, len(names) - 1)]
        self.anim.load(f'rsc/{name}.json', {'BaseVelocity': 30.0})
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
