from .line import *


class Document:
    def __init__(self, filename):
        self.lines = [Line('')]
        if filename:
            self.load(filename)

    def load(self, filename):
        try:
            lines = open(filename).readlines()
            self.lines = [Line(s.rstrip()) for s in lines]
        except OSError:
            return False
        return True

    def size(self):
        return len(self.lines)

    def __getitem__(self, item):
        return self.lines[item]

    def delete_line(self, index):
        if 0 <= index < len(self.lines):
            del self.lines[index]

    def insert(self, line, at):
        self.lines.insert(at, line)
