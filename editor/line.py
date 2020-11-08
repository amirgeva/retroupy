TAB_SIZE = 4


class Token:
    def __init__(self, x, i, text):
        self.x = x
        self.index = i
        self.text = text


class Line:
    def __init__(self, text):
        self.text = ''
        self.tabs = []
        self.tokens = []
        if text:
            self.set_text(text)

    def size(self):
        return len(self.text)

    def append_text(self, text):
        self.text = self.text + text
        if len(self.tokens) > 0:
            self.tokens[-1].text += text
        else:
            self.calc_tokens()

    def insert_text(self, x, text):
        self.text = self.text[0:x] + text + self.text[x:]
        self.calc_tokens()

    def join(self, line):
        self.set_text(self.text + line.text)

    def split(self, x):
        text = self.text[x:]
        self.set_text(self.text[0:x])
        return Line(text)

    def delete_char(self, x):
        self.set_text(self.text[0:x] + self.text[x + 1:])

    def set_text(self, text):
        self.text = text
        self.tabs = []
        for i in range(len(text)):
            if text[i] == '\t':
                self.tabs.append(i)
        self.calc_tokens()

    def calc_tokens(self):
        self.tokens = []
        x = 0
        i = 0
        for tab_index in self.tabs:
            if i == tab_index:
                i = i + 1
                x = x + (TAB_SIZE - i % 4)
            else:
                self.tokens.append(Token(x, i, self.text[i:tab_index]))
                x = x + (tab_index - i)
                i = tab_index + 1
        if i < len(self.text):
            self.tokens.append(Token(x, i, self.text[i:]))
