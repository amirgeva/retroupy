import itertools
import math


# EXPORT
class Point(object):
    def __init__(self, *args):
        if len(args) == 2:
            self.x = args[0]
            self.y = args[1]
        elif len(args) == 1:
            if isinstance(args[0], Point):
                self.x = args[0].x
                self.y = args[0].y
            elif isinstance(args[0], tuple):
                self.x = args[0][0]
                self.y = args[0][1]
            else:
                raise TypeError()

    def as_tuple(self):
        return self.x, self.y

    def __hash__(self):
        return hash(self.as_tuple())

    def __str__(self):
        return f'{self.x},{self.y}'

    def __lt__(self, p):
        if not isinstance(p, Point):
            p = Point(p)
        if self.y < p.y:
            return True
        if self.y > p.y:
            return False
        return self.x < p.x

    def __le__(self, p):
        return self < p or self == p

    def __gt__(self, p):
        return not (self < p or self == p)

    def __ge__(self, p):
        return not (self < p)

    def __eq__(self, p):
        if not isinstance(p, Point):
            p = Point(p)
        return self.x == p.x and self.y == p.y

    def __ne__(self, p):
        return not (self == p)

    def __iadd__(self, p):
        if not isinstance(p, Point):
            p = Point(p)
        self.x += p.x
        self.y += p.y
        return self

    def __isub__(self, p):
        if not isinstance(p, Point):
            p = Point(p)
        self.x -= p.x
        self.y -= p.y
        return self

    def __add__(self, p):
        if not isinstance(p, Point):
            p = Point(p)
        return Point(self.x + p.x, self.y + p.y)

    def __sub__(self, p):
        if not isinstance(p, Point):
            p = Point(p)
        return Point(self.x - p.x, self.y - p.y)

    def __neg__(self):
        return Point(-self.x, -self.y)

    def scaled(self, s):
        return Point(self.x * s, self.y * s)

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def norm(self):
        return self.length()


# EXPORT
def vector2(*args):
    if len(args) == 2:
        return Point(float(args[0]), float(args[1]))
    if len(args) == 1:
        if isinstance(args[0], Point):
            return Point(float(args[0].x), float(args[0].y))
        elif isinstance(args[0], tuple):
            return Point(float(args[0][0]), float(args[0][1]))
        else:
            raise TypeError()


# EXPORT
class Rect(object):
    def __init__(self, *args):
        if len(args) == 2 and isinstance(args[0], Point) and isinstance(args[1], Point):
            self.tl = Point(args[0])
            self.br = Point(args[1])
        elif len(args) == 4:
            self.tl = Point(args[0], args[1])
            self.br = Point(args[2], args[3])
        elif len(args) == 1 and isinstance(args[0], Rect):
            self.tl = Point(args[0].tl)
            self.br = Point(args[0].br)
        else:
            self.tl = Point(0, 0)
            self.br = Point(0, 0)

    def __hash__(self):
        return hash(self.as_tuple())

    def normalized(self):
        return Rect(min(self.tl.x, self.br.x), min(self.tl.y, self.br.y),
                    max(self.tl.x, self.br.x), max(self.tl.y, self.br.y))

    def coords(self):
        return [self.tl.x, self.tl.y, self.br.x, self.br.y]

    def as_tuple(self):
        return self.tl.x, self.tl.y, self.br.x, self.br.y

    def valid(self):
        return self.br.x > self.tl.x and self.br.y > self.tl.y

    def left(self):
        return self.tl.x

    def top(self):
        return self.tl.y

    def right(self):
        return self.br.x

    def bottom(self):
        return self.br.y

    def width(self):
        return self.br.x - self.tl.x

    def height(self):
        return self.br.y - self.tl.y

    def area(self):
        return self.width() * self.height()

    def move(self, offset):
        self.tl = self.tl + offset
        self.br = self.br + offset
        return self

    def inflate(self, d):
        if isinstance(d, Point):
            self.tl -= d
            self.br += d
        else:
            self.tl -= Point(d, d)
            self.br += Point(d, d)
        return self

    def union(self, r):
        if self.tl.x == self.br.x and self.tl.y == self.br.y:
            self.tl = Point(r.tl)
            self.br = Point(r.br)
        else:
            self.tl.x = min(self.tl.x, r.tl.x)
            self.tl.y = min(self.tl.y, r.tl.y)
            self.br.x = max(self.br.x, r.br.x)
            self.br.y = max(self.br.y, r.br.y)
        return self

    def intersection(self, r):
        return Rect(max(self.tl.x, r.tl.x),
                    max(self.tl.y, r.tl.y),
                    min(self.br.x, r.br.x),
                    min(self.br.y, r.br.y))

    def overlaps(self, r):
        intr = self.intersection(r)
        return intr.br.x > intr.tl.x and intr.br.y > intr.tl.y

    def contains(self, r):
        return r.tl.x >= self.tl.x and r.tl.y >= self.tl.y and r.br.x <= self.br.x and r.br.y <= self.br.y

    def is_point_inside(self, p):
        if not isinstance(p, Point):
            p = Point(p)
        return self.br.x > p.x >= self.tl.x and self.br.y > p.y >= self.tl.y

    def __eq__(self, r):
        if not isinstance(r, Rect):
            return False
        return self.tl == r.tl and self.br == r.br

    def __ne__(self, r):
        return not (self == r)

    def __repr__(self):
        return f'{self.tl.x},{self.tl.y},{self.br.x},{self.br.y}'


# EXPORT
def parse_rect(s):
    try:
        c = tuple([int(p) for p in s.split(',')])
        return Rect(*c)
    except ValueError:
        return Rect(0, 0, 1, 1)


# EXPORT
def parse_float(s):
    try:
        return float(s)
    except ValueError:
        return 0.0


# EXPORT
def is_transparent(s):
    w = s.width()
    h = s.height()
    for y in range(h):
        for x in range(w):
            c = s.get_at((x, y))
            if c.a < 255:
                return True
    return False


# EXPORT
def parse_point(s):
    c = s.split(',')
    return Point(int(c[0]), int(c[1]))


# EXPORT
def parse_color(s):
    c = s.split(',')
    a = 255
    if len(c) > 3:
        a = int(c[3])
    return int(c[0]), int(c[1]), int(c[2]), a


# EXPORT
def all_pixels(s):
    return itertools.product(range(s.width()), range(s.height()))
