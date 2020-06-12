#!/usr/bin/env python3
import sys
from random import randint, seed

from .utils import Rect


class RTreeNode(object):
    def __init__(self, parent):
        self.children = []
        self.items = []
        self.rect = None
        self.parent = parent

    def move(self, rid, rect):
        if self.rect.contains(rect):
            for i in range(len(self.items)):
                if self.items[i][0] == rid:
                    self.items[i] = (rid, rect)
                    return True
        return False

    def add_item(self, rid, rect):
        if not self.rect:
            self.rect = Rect(rect)
        else:
            self.rect.union(rect)
        if len(self.children) > 0:
            return self.add_to_child(rid, rect)
        else:
            self.items.append((rid, rect))
            if len(self.items) >= 8:
                return self.split_node()
            return self

    def add_to_child(self, rid, rect):
        min_delta = 99999999
        best_child = None
        for c in self.children:
            r = Rect(rect)
            r.union(c.rect)
            delta = r.area() - c.rect.area()
            if delta < min_delta:
                min_delta = delta
                best_child = c
        if not best_child:
            return self.add_item(rid, rect)
        return best_child.add_item(rid, rect)

    def split_node(self):
        if randint(0, 1) == 0:
            self.items.sort(key=lambda t: t[1].tl.x)
        else:
            self.items.sort(key=lambda t: t[1].tl.y)
        mid = int(len(self.items) / 2)
        self.children.append(RTreeNode(self))
        for i in self.items[0:mid]:
            self.children[-1].add_item(i[0], i[1])
        self.children.append(RTreeNode(self))
        for i in self.items[mid:]:
            self.children[-1].add_item(i[0], i[1])
        self.items = []
        return self.children

    def search(self, rect):
        res = []
        if not self.rect:
            return res
        if rect.overlaps(self.rect):
            for i in self.items:
                if i[1].overlaps(rect):
                    res.append(i)
            for c in self.children:
                res = res + c.search(rect)
        return res

    def remove_item(self, rid):
        for i in range(len(self.items)):
            if self.items[i][0] == rid:
                del self.items[i]
                break
        self.recalc_rect()

    def remove_child(self, child):
        for i in range(0, len(self.children)):
            if self.children[i] == child:
                del self.children[i]
                break
        return True

    def recalc_rect(self):
        if len(self.children) == 0 and len(self.items) == 0 and self.parent:
            return self.parent.remove_child(self)
        self.rect = Rect()
        for c in self.children:
            self.rect.union(c.rect)
        for item in self.items:
            self.rect.union(item[1])
        if self.parent:
            self.parent.recalc_rect()

    def get_depth(self):
        if len(self.children) > 0:
            return self.children[0].get_depth() + 1
        return 1


# EXPORT
class RTree(object):
    def __init__(self):
        self.root = RTreeNode(None)
        self.directory = {}

    def add(self, rid, rect):
        rect = Rect(rect)
        self.remove(rid)
        nodes = self.root.add_item(rid, rect)
        if isinstance(nodes, list):
            for child in nodes:
                for item in child.items:
                    self.directory[item[0]] = child
        else:
            self.directory[rid] = nodes

    def move(self, rid, rect):
        if rid in self.directory:
            node = self.directory.get(rid)
            if not node.move(rid, rect):
                self.add(rid, rect)

    def remove(self, rid):
        if rid in self.directory:
            node = self.directory.get(rid)
            node.remove_item(rid)
            del self.directory[rid]
            return True
        return False

    def search(self, rect):
        return self.root.search(rect)

    def depth(self):
        return self.root.get_depth()


class BFTree(object):
    def __init__(self):
        self.rects = {}

    def add(self, rid, rect):
        self.rects[rid] = rect

    def move(self, rid, rect):
        self.add(rid, rect)

    def remove(self, rid):
        if rid in self.rects:
            del self.rects[rid]

    def search(self, rect):
        res = []
        for rid in self.rects:
            r = self.rects.get(rid)
            if r.overlaps(rect):
                res.append((rid, r))
        return res

    def get_random_id(self):
        if len(self.rects) == 0:
            return 0
        ids = list(self.rects.keys())
        return ids[randint(0, len(ids) - 1)]


def unit_test():
    def rand_rect():
        x = randint(0, 1000)
        y = randint(0, 1000)
        w = randint(16, 64)
        h = randint(16, 64)
        return Rect(x, y, x + w, y + h)

    seed(1)
    t1 = RTree()
    t2 = BFTree()
    fail = False
    rects = 0
    for i in range(10000):
        if (i & 255) == 0:
            sys.stdout.write(f'{i}\r')
        # print(f"{i} {rects} {t1.depth()}")
        if fail:
            break
        act = randint(0, 100)
        if act < 40:
            r = rand_rect()
            rid = i  # randint(0, 10000)
            t1.add(rid, r)
            t2.add(rid, r)
            rects += 1
        elif act < 60:
            rid = t2.get_random_id()
            if t1.remove(rid):
                rects -= 1
            t2.remove(rid)
        elif act < 90:
            r = rand_rect()
            res1 = t1.search(r)
            res2 = t2.search(r)
            if len(res1) != len(res2):
                print(f"{i}: Mismatch result length")
                fail = True
                break
            res1.sort(key=lambda t: t[0])
            res2.sort(key=lambda t: t[0])
            for j in range(len(res1)):
                if res1[j][0] != res2[j][0]:
                    print(f"{i}: Mismatch found ID")
                    fail = True
                    break
        elif act < 100:
            rid = t2.get_random_id()
            r = rand_rect()
            t1.move(rid, r)
            t2.move(rid, r)
    if not fail:
        print("All tests successful")


if __name__ == '__main__':
    try:
        unit_test()
    except RecursionError:
        print("RecursionError")
