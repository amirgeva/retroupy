from rtree import RTree
from utils import Point


# EXPORT
class Scene(object):
    def __init__(self):
        self.entities = {}
        self.dynamics = set()
        self.statics = set()
        self.rtree = RTree()

    def add(self, entity):
        eid = entity.get_id()
        self.entities[eid] = entity
        if entity.is_dynamic:
            self.dynamics.add(eid)
        else:
            self.statics.add(eid)
        r = entity.get_rect()
        self.rtree.add(eid, r)

    def advance(self, dt):
        ids = set(self.dynamics)  # Copy to allow deletions
        for eid in ids:
            e = self.entities.get(eid)
            before = e.get_rect()
            if not e.advance(dt):
                self.rtree.remove(eid)
                self.dynamics.remove(eid)
                del self.entities[eid]
            else:
                after = e.get_rect()
                if before != after:
                    self.check_collisions(e, after)
                    after = e.get_rect()
                    self.rtree.move(e.get_id(), after)

    def draw(self, view):
        visible = self.rtree.search(view.get_rect())
        vis_id = [v[0] for v in visible]
        ids = [eid for eid in vis_id if eid in self.statics]
        ids.extend([eid for eid in vis_id if eid not in self.statics])
        for eid in ids:
            e = self.entities.get(eid)
            if e:
                e.draw(view)

    def check_collisions(self, entity, rect):
        eid = entity.get_id()
        spr1 = entity.anim.get_current_sprite()
        cands = self.rtree.search(rect)
        for (cand_id, cand_rect) in cands:
            if cand_id != eid:
                cand = self.entities.get(cand_id)
                spr2 = cand.anim.get_current_sprite()
                offset = cand.get_position() - entity.get_position()
                ox = int(offset.x)
                oy = int(offset.y)
                pt = spr1.mask.overlap(spr2.mask, Point(ox, oy))
                if pt:
                    dx, dy = pt.x, pt.y
                    entity.collision(cand, Point(dx, dy))
                    cand.collision(entity, Point(dx - ox, dy - oy))
