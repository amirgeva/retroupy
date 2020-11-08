from .cursor import Cursor
from .line import TAB_SIZE


class View:
    def __init__(self, screen, doc=None):
        self.screen = screen
        self.doc = doc
        self.line_offset = 0
        self.xoffset = 0
        self.line_width = screen.width() // 8
        self.view_lines = screen.height() // 16
        self.cursor = Cursor()

    def move_cursor(self, dx, dy):
        self.cursor.move(dx, dy)
        self.cursor.clamp_y(0, self.doc.size())
        line = self.doc[self.cursor.y]
        self.cursor.clamp_x(0, line.size())
        self.place_cursor()

    def place_cursor(self):
        x, y = self.doc2scr(self.cursor)
        self.screen.text_cursor(x, y)

    def insert_text(self, text):
        line = self.doc[self.cursor.y]
        if self.cursor.x >= line.size():
            line.append_text(text)
        else:
            line.insert_text(self.cursor.x, text)
        self.cursor.move(1, 0)
        self.draw_cursor_line()
        self.place_cursor()

    def draw_cursor_line(self):
        line = self.doc[self.cursor.y]
        self.draw_line(self.cursor.y - self.line_offset)
        x, y = self.doc2scr(Cursor(line.size(), self.cursor.y))
        self.screen.fill_rect(x * 8, y * 16, self.screen.width() - x * 8, 16)
        x, y = self.doc2scr(self.cursor)
        self.screen.text_cursor(x, y)

    def enter(self):
        line = self.doc[self.cursor.y]
        line = line.split(self.cursor.x)
        self.doc.insert(line, self.cursor.y + 1)
        self.cursor = Cursor(0, self.cursor.y + 1)
        self.redraw_all()

    def delete(self):
        line = self.doc[self.cursor.y]
        if self.cursor.x < line.size():
            line.delete_char(self.cursor.x)
            self.draw_cursor_line()
        elif self.cursor.y < (self.doc.size() - 1):
            next_line = self.doc[self.cursor.y + 1]
            line.join(next_line)
            self.doc.delete_line(self.cursor.y + 1)
            self.redraw_all()

    def backspace(self):
        line = self.doc[self.cursor.y]
        if self.cursor.x > 0:
            line.delete_char(self.cursor.x - 1)
            self.cursor.move(-1, 0)
            self.draw_cursor_line()
            self.place_cursor()
        elif self.cursor.y > 0:
            prev_line = self.doc[self.cursor.y - 1]
            x = prev_line.size()
            prev_line.join(line)
            self.doc.delete_line(self.cursor.y)
            self.cursor = Cursor(x, self.cursor.y - 1)
            self.redraw_all()

    def draw_line(self, y: int):
        line_index = y + self.line_offset
        if line_index >= self.doc.size():
            return
        line = self.doc[line_index]
        for token in line.tokens:
            text = token.text
            x0 = token.x - self.xoffset
            x1 = x0 + len(text)
            if x1 > 0:
                if x0 < 0:
                    text = text[-x0:]
                    x0 = 0
                if x1 > self.line_width:
                    text = text[0:(self.line_width - x1)]
                    x1 = self.line_width
                self.screen.text_cursor(x0, y)
                self.screen.text(text)

    def doc2scr(self, c: Cursor):
        y = c.y - self.line_offset
        line = self.doc[c.y]
        last = None
        x = 0
        for t in line.tokens:
            if t.index <= c.x <= (t.index + len(t.text)):
                x = t.x + (c.x - t.index)
                break
            if c.x < t.index:
                x = t.x
                for i in range(t.index - c.x):
                    x = x - TAB_SIZE
                    if last and x <= (last.x + len(last.text)):
                        x = last.x + len(last.text)
                        break
                break
            last = t
        return x, y

    def redraw_all(self):
        self.screen.cls()
        for y in range(self.view_lines):
            self.draw_line(y)
        x, y = self.doc2scr(self.cursor)
        self.screen.text_cursor(x, y)
