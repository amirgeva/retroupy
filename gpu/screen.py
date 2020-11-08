from machine import UART
from fpioa_manager import fm
from board import board_info

N_SPRITES = 160

CMD_NOP = 0
CMD_CLS = 1
CMD_FLIP = 2
CMD_TEXT_NEWLINE = 4
CMD_PIXEL_CURSOR = 5
CMD_TEXT_CURSOR = 6
CMD_FG_COLOR = 7
CMD_BG_COLOR = 8
CMD_PUSH_CURSOR = 9
CMD_POP_CURSOR = 10
CMD_BLINK_CURSOR = 11
CMD_FILL_RECT = 20
CMD_HORZ_LINE = 21
CMD_VERT_LINE = 22
CMD_HORZ_PIXELS = 23
CMD_TEXT = 30
CMD_SET_SPRITE = 40
CMD_DRAW_SPRITE = 41
CMD_TRANSPARENT_COLOR = 42


# EXPORT
class Screen:
    def __init__(self):
        fm.register(25, fm.fpioa.UART2_RX)
        fm.register(24, fm.fpioa.UART2_TX)
        self.uart = UART(UART.UART2, 460800)
        self.byte_count = 0
        self.nop(16)

    def reset_count(self):
        self.byte_count = 0

    def send(self, data):
        self.byte_count = self.byte_count + len(data)
        self.uart.write(data)

    def nop(self, n=1):
        self.send(bytes([CMD_NOP] * n))
        self.uart.read(4096)

    def cls(self):
        self.send(bytes([CMD_CLS]))

    def flip(self, double_buffer=1):
        db = 1 if double_buffer else 0
        self.send(bytes([CMD_FLIP, db]))

    def text_newline(self):
        self.send(bytes([CMD_TEXT_NEWLINE]))

    def pixel_cursor(self, x, y):
        x = int(x)
        y = int(y)
        self.send(bytes([CMD_PIXEL_CURSOR, (x & 255), (x >> 8) & 255, (y & 255), (y >> 8) & 255]))

    def text_cursor(self, x, y):
        x = int(x)
        y = int(y)
        self.send(bytes([CMD_TEXT_CURSOR, x, y]))

    def fg_color(self, c):
        self.send(bytes([CMD_FG_COLOR, (c & 255), (c >> 8) & 255]))

    def bg_color(self, c):
        self.send(bytes([CMD_BG_COLOR, (c & 255), (c >> 8) & 255]))

    def text(self, s):
        if len(s) < 256:
            self.send(bytes([CMD_TEXT, len(s)]))
            self.send(bytes(s, 'ascii'))

    def println(self, s):
        self.text(s)
        self.text_newline()

    def push_cursor(self):
        self.send(bytes([CMD_PUSH_CURSOR]))

    def pop_cursor(self):
        self.send(bytes([CMD_POP_CURSOR]))

    def blink(self, on):
        state = 1 if on else 0
        self.send(bytes([CMD_BLINK_CURSOR, state]))

    def fill_rect(self, x, y, w, h):
        self.pixel_cursor(x, y)
        w = int(w)
        h = int(h)
        self.send(bytes([CMD_FILL_RECT, (w & 255), (w >> 8) & 255, (h & 255), (h >> 8) & 255]))

    def horz_line(self, x0, x1, y):
        self.pixel_cursor(x0, y)
        w = int(x1 - x0)
        self.send(bytes([CMD_HORZ_LINE, (w & 255), (w >> 8) & 255]))

    def vert_line(self, x, y0, y1):
        self.pixel_cursor(x, y0)
        h = int(y1 - y0)
        self.send(bytes([CMD_VERT_LINE, (h & 255), (h >> 8) & 255]))

    @staticmethod
    def pixels2bytes(pixels):
        if isinstance(pixels, bytes):
            return pixels
        vals = [None] * (len(pixels) * 2)
        for i in range(len(pixels)):
            vals[i * 2] = pixels[i] & 255
            vals[i * 2 + 1] = (pixels[i] >> 8) & 255
        # vals[::2] = [p & 255 for p in pixels]
        # vals[1::2] = [(p >> 8) & 255 for p in pixels]
        return bytes(vals)

    def horz_pixels(self, pixels):
        pixels = self.pixels2bytes(pixels)
        n = (len(pixels) >> 1)
        if n < 256:
            self.send(bytes[CMD_HORZ_PIXELS, n])
            self.send(pixels)

    def set_sprite(self, index, pixels):
        if 0 <= index < N_SPRITES:
            pixels = self.pixels2bytes(pixels)
            if len(pixels) == (32 * 32 * 2):
                print("Setting sprite " + str(index))
                self.send(bytes([CMD_SET_SPRITE, (index & 255), (index >> 8) & 255]))
                self.send(pixels)
            else:
                print("Failed to set sprite " + str(index) + "  len(pixels)=" + str(len(pixels)))

    def draw_sprite(self, x, y, index, flags):
        if 0 <= index < N_SPRITES:
            self.pixel_cursor(x, y)
            index = int(index)
            flags = int(flags)
            self.send(bytes([CMD_DRAW_SPRITE, (index & 255), (index >> 8) & 255, flags]))

    def set_transparent_color(self, enabled, color):
        en = 1 if enabled else 0
        self.send(bytes([CMD_TRANSPARENT_COLOR, en, color & 255, (color >> 8) & 255]))

    @staticmethod
    def start():
        pass

    @staticmethod
    def stop():
        pass


screen = Screen()
