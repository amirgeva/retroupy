from .physics import RigidBody
from .utils import Rect

ids = 0


def generate_id():
    global ids
    ids += 1
    return ids


# EXPORT
class Entity(RigidBody):
    def __init__(self, anim):
        super().__init__()
        self.anim = anim
        self.eid = generate_id()
        self.dynamic = True

    @property
    def get_type(self):
        return 'Entity'

    @property
    def is_dynamic(self):
        return self.dynamic

    def advance(self, dt):
        super().advance(dt)
        if self.is_dynamic:
            self.anim.advance(dt, self.velocity)
        return True

    def draw(self, view):
        self.anim.draw(view.relative_position(self.get_position()))

    def get_rect(self):
        r = Rect(self.anim.get_rect())
        ofs = self.get_position()
        r.move(ofs)
        return r

    def get_id(self):
        return self.eid

    def collision(self, other, col_point):
        pass
