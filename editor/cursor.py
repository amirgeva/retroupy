class Cursor:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def clamp_x(self, mn, mx):
        if self.x < mn:
            self.x = mn
        if self.x >= mx:
            self.x = mx

    def clamp_y(self, mn, mx):
        if self.y < mn:
            self.y = mn
        if self.y >= mx:
            self.y = mx - 1
