import random
from engine import *


class Monster(Entity):
    def __init__(self):
        super().__init__(AnimatedSprite())
        names = ['bird', 'mush', 'pig', 'rock', 'slime', 'snail']
        name = names[random.randint(0, len(names) - 1)]
        self.anim.load('rsc/'+name+'.json', {'BaseVelocity': 30.0})
        self.anim.set_active_sequence('WalkRight')
        self.range = (0, 0)
        self.speed = 10
        self.hitpoints = 30

    def set_range(self, mn, mx):
        self.range = (mn, mx)
        self.set_velocity(self.speed, 0)

    def advance(self, dt):
        if self.hitpoints <= 0:
            return False
        p = self.get_position()
        v = self.get_velocity()
        if (p.x >= self.range[1] and v.x > 0) or (p.x < self.range[0] and v.x < 0):
            v.x = -v.x
            direction = 'Right' if v.x > 0 else 'Left'
            self.anim.set_active_sequence('Walk'+direction)
            self.set_velocity(v)
        return super().advance(dt)

    def hit(self, damage, momentum):
        self.hitpoints = self.hitpoints - damage
        pos = self.get_position()
        pos.x = pos.x + momentum
        self.set_position(pos)
