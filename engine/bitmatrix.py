#!/usr/bin/env python3
from .utils import Point, Rect


class BitArray:
    def __init__(self, size):
        self.bit_count = size
        self.mask = 0

    def size(self):
        return self.bit_count

    def setall(self, state):
        if state:
            self.mask = (1 << self.size()) - 1
        else:
            self.mask = 0

    def set(self, index, v):
        if 0 <= index < self.size():
            if v:
                self.mask = self.mask | (1 << index)
            else:
                self.mask = self.mask & ~(1 << index)

    def overlap(self, other, offset):
        mask = 0
        if offset <= 0:
            mask = self.mask & (other.mask >> -offset)
        else:
            mask = self.mask & (other.mask << offset)
        if mask != 0:
            x = 0
            while (mask & 1) == 0:
                x = x + 1
                mask = mask >> 1
            return x

    def __getitem__(self, index):
        if 0 <= index < self.size():
            return (self.mask & (1 << index)) != 0
        return False


# EXPORT
class BitMatrix(object):
    def __init__(self, width, height, init=True):
        self.sizes = (width, height)
        self.rows = [BitArray(width) for _ in range(height)]
        if init:
            self.clear()

    def width(self):
        return self.sizes[0]

    def height(self):
        return self.sizes[1]

    def get(self, x, y):
        if 0 <= x < self.width() and 0 <= y < self.height():
            return self.rows[y][x]
        return False

    def set(self, x, y, v):
        if 0 <= x < self.width() and 0 <= y < self.height():
            self.rows[y].set(x, v)

    def clear(self):
        self.setall(False)

    def setall(self, value=True):
        for row in self.rows:
            row.setall(value)

    def get_rect(self):
        return Rect(0, 0, self.width(), self.height())

    def overlap(self, other, offset):
        r = self.get_rect().intersection(other.get_rect().move(offset))
        for y in range(r.tl.y, r.br.y):
            row = self.rows[y]
            orow = other.rows[y - offset.y]
            x = row.overlap(orow, offset.x)
            if x:
                return Point(x, y)
        return None


class BFBitMatrix(object):
    def __init__(self, width, height):
        self.sizes = (width, height)
        self.data = [False] * (width * height)

    def width(self):
        return self.sizes[0]

    def height(self):
        return self.sizes[1]

    def get(self, x, y):
        if x < 0 or x >= self.width() or y < 0 or y >= self.height():
            return False
        return self.data[y * self.width() + x]

    def set(self, x, y, v):
        if 0 <= x < self.width() and 0 <= y < self.height():
            self.data[y * self.width() + x] = v

    def clear(self):
        self.data = [False] * (self.width() * self.height())

    def setall(self):
        self.data = [True] * (self.width() * self.height())

    def overlap(self, other, offset):
        all_bits = set()
        for i in range(self.height()):
            for j in range(self.width()):
                if self.get(j, i):
                    all_bits.add(Point(j, i))
        for i in range(other.height()):
            for j in range(other.width()):
                if other.get(j, i):
                    p = Point(j + offset.x, i + offset.y)
                    if p in all_bits:
                        return Point(j, i)
        return None


def unit_test():
    def compare(mat1, mat2):
        if mat1.width() != mat2.width():
            return False
        if mat1.height() != mat2.height():
            return False
        for yi in range(0, mat1.height()):
            for xi in range(0, mat1.width()):
                if mat1.get(xi, yi) != mat2.get(xi, yi):
                    return False
        return True

    from random import randint, seed
    seed(1)
    try:
        s = 18
        n = 1000
        m1 = BitMatrix(s, s)
        m2 = BFBitMatrix(s, s)
        for i in range(n):
            if not compare(m1, m2):
                raise Exception(f"Failed {i}")
            x = randint(0, s - 1)
            y = randint(0, s - 1)
            v = (randint(0, 1) > 0)
            m1.set(x, y, v)
            m2.set(x, y, v)
            offset = Point(randint(-40, 40), randint(-40, 40))
            o1 = m1.overlap(m1, offset)
            o2 = m2.overlap(m2, offset)
            if o1 != o2:
                raise Exception(f"Failed overlap {i}")
        raise Exception("Test successful")
    except Exception as e:
        print(e)


if __name__ == '__main__':
    unit_test()
