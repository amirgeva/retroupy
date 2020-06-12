#!/usr/bin/env python3
from typing import Tuple

import cv2
import numpy as np
import threading
import time
from app import app
# import sim_uoscore
from sim_font import Font
from utils import Rect, Point

N_SPRITES = 160


def cvt16to32(c):
    return (c & 0x1F) << 3, (c >> 3) & 0xFC, (c >> 8) & 0xF8, 255


class Screen:
    Cursor: Tuple[int, int]

    def __init__(self):
        self.Image = np.ndarray((480, 640, 4), dtype=np.uint8)
        self.Sprites = [np.ndarray((32, 32, 4), dtype=np.uint8) for _ in range(N_SPRITES)]
        self.Sprites16 = [np.ndarray((32, 32), dtype=np.uint16) for _ in range(N_SPRITES)]
        for i in range(N_SPRITES):
            sprite = self.Sprites[i]
            sprite[:] = (0, 0, 0, 255)
            sprite = self.Sprites16[i]
            sprite[:] = 0
            self.Sprites16[i] = sprite
        self.transparency = False
        self.transparent = 0
        self.updated = True
        self.Scaling = 2
        self.blinking = False
        self.fg = 255, 255, 255, 255
        self.bg = 0, 0, 0, 255
        self.Cursor = 0, 0
        self.CursorStack = []
        self.font = Font()
        self.cls()
        self.cursor_block = np.ones((16, 8, 4), dtype=np.uint8)
        self.cursor_block[:] = 255, 255, 255, 255
        cv2.namedWindow('vis')

    def flush(self):
        pass

    def nop(self):
        pass

    def draw_cursor(self):
        x, y = self.Cursor
        c = self.cursor_block
        sub = self.Image[y:y + c.shape[0], x:x + c.shape[1]]
        sub = cv2.bitwise_xor(sub, c)
        self.Image[y:y + c.shape[0], x:x + c.shape[1]] = sub

    def toggle_blink(self):
        if self.blinking:
            self.draw_cursor()
            self.updated = True

    def cls(self):
        self.Image[:] = (0, 0, 0, 255)
        self.fg = 255, 255, 255, 255
        self.bg = 0, 0, 0, 255
        self.Cursor = 0, 0
        self.updated = True

    def flip(self):
        self.show()

    def height(self):
        return self.Image.shape[0]

    def width(self):
        return self.Image.shape[1]

    def scroll(self):
        h = self.height()
        w = self.width()
        th = self.font.height()
        self.Image[0:(h - th), 0:w] = self.Image[th:h, 0:w]

    def text_newline(self):
        y = self.Cursor[1] + self.font.height()
        if y >= self.height():
            self.scroll()
            y = y - self.font.height()
        self.Cursor = (0, y)

    def pixel_cursor(self, x, y):
        if 0 <= x < self.width() and 0 <= y < self.height():
            self.Cursor = (x, y)

    def text_cursor(self, x, y):
        x = x * self.font.width()
        y = y * self.font.height()
        self.pixel_cursor(x, y)

    def fg_color(self, c):
        self.fg = cvt16to32(c)

    def bg_color(self, c):
        self.bg = cvt16to32(c)

    def text(self, s):
        x, y = self.Cursor
        for c in s:
            if x > self.width() - self.font.width():
                break
            i = ord(c)
            p = np.copy(self.font.get(i))
            p[p[:, :, 0] == 0] = self.bg
            p[p[:, :, 0] == 255] = self.fg
            self.Image[y:(y + self.font.height()), x:(x + self.font.width())] = p
            x = x + self.font.width()
        self.pixel_cursor(x, y)
        self.updated = True

    def println(self, s):
        self.text(s)
        self.text_newline()

    def push_cursor(self):
        self.CursorStack.append(self.Cursor)

    def pop_cursor(self):
        if len(self.CursorStack) > 0:
            self.Cursor = self.CursorStack[-1]
            del self.CursorStack[-1]

    def blink(self, on):
        self.blinking = on

    def fill_rect(self, x, y, w, h):
        self.pixel_cursor(x, y)
        self.Image[y:(y + h), x:(x + w)] = self.bg
        self.updated = True

    def horz_line(self, x0, x1, y):
        cv2.line(self.Image, (x0, y), (x1, y), self.fg)
        self.updated = True

    def vert_line(self, x, y0, y1):
        cv2.line(self.Image, (x, y0), (x, y1), self.fg)
        self.updated = True

    def horz_pixels(self, pixels):
        x, y = self.Cursor
        for p in pixels:
            if y < 0 or y >= self.height() or x < 0 or x >= self.width():
                break
            self.Image[y, x, :] = cvt16to32(p)
            x = x + 1
        self.updated = True

    def set_sprite(self, index, pixels):
        if 0 <= index < N_SPRITES:
            i = 0
            spr = self.Sprites[index]
            spr16 = self.Sprites16[index]
            for y in range(spr.shape[0]):
                for x in range(spr.shape[1]):
                    pixel = (int(pixels[i * 2 + 1]) << 8) | int(pixels[i * 2])
                    c = cvt16to32(pixel)
                    alpha = 255
                    if self.transparency:
                        alpha = 0 if pixel == self.transparent else 255
                    spr[y, x, :] = c[0], c[1], c[2], alpha
                    spr16[y, x] = pixel
                    i = i + 1

    def draw_partial(self, x, y, index):
        s = self.Sprites[index]
        rdst = Rect(x, y, x + 32, y + 32).intersection(Rect(0, 0, self.width(), self.height()))
        rsrc = Rect(rdst)
        rsrc.move(Point(-x, -y))
        dst = self.Image[rdst.tl.y:rdst.br.y, rdst.tl.x:rdst.br.x, :]
        src = s[rsrc.tl.y:rsrc.br.y, rsrc.tl.x:rsrc.br.x, :]
        alpha = (src[:, :, 3] == 255)
        for c in range(3):
            np.copyto(dst[:, :, c], src[:, :, c], where=alpha)

    def draw_sprite(self, x, y, index):
        if 0 <= index < N_SPRITES:
            x = int(x)
            y = int(y)
            if x >= self.width() or (x + 32) <= 0 or y >= self.height() or (y + 32) <= 0:
                return
            if x < 0 or y < 0 or (x + 32) > self.width() or (y + 32) > self.height():
                self.draw_partial(x, y, index)
            else:
                self.pixel_cursor(x, y)
                s = self.Sprites[index]
                alpha = (s[:, :, 3] == 255)
                for c in range(3):
                    np.copyto(self.Image[y:(y + s.shape[0]), x:(x + s.shape[1]), c], s[:, :, c], where=alpha)
            self.updated = True

    def set_transparent_color(self, enabled, color):
        self.transparency = enabled
        self.transparent = color
        for index in range(N_SPRITES):
            spr = self.Sprites[index]
            spr16 = self.Sprites16[index]
            for y in range(spr.shape[0]):
                for x in range(spr.shape[1]):
                    spr[y, x, 3] = 0 if (enabled and spr16[y, x] == color) else 255

    def show(self):
        self.font.write(self.Image, 0, 0, f'FPS: {int(app.fps)}')
        w = int(self.Scaling * self.Image.shape[1])
        h = int(self.Scaling * self.Image.shape[0])
        img = cv2.resize(self.Image, (w, h), interpolation=cv2.INTER_NEAREST)
        cv2.imshow("vis", img)
        cv2.waitKey(1)

    @staticmethod
    def wait(ms):
        cv2.waitKey(ms)

    @staticmethod
    def start():
        global show_thread
        show_thread = threading.Thread(target=show_loop)
        show_thread.start()

    @staticmethod
    def stop():
        global terminate
        global show_thread
        if not terminate:
            terminate = True
            if show_thread:
                # noinspection PyUnresolvedReferences
                show_thread.join()


screen = Screen()
terminate = False
show_thread = None


def show_loop():
    count = 0
    while not terminate:
        if screen.updated:
            screen.updated = False
            screen.show()
        time.sleep(0.05)
        count = count + 1
        # uoscore.timer()
        if count >= 10:
            count = 0
            screen.toggle_blink()


def get_test_sprite_data():
    data = [
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0000, 0x0000,
        0x0000, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0000, 0x0000, 0x0000,
        0x0000, 0x0000, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0000, 0x0000, 0x0000,
        0x0000, 0x0000, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0000, 0x0000, 0x0000,
        0x0000, 0x0000, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0000, 0x0000, 0x0000,
        0x0000, 0x0000, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0000, 0x0000,
        0x0000, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x06df, 0x06df,
        0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x06df, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020,
        0x0020, 0x0020, 0x0020, 0x0020,
    ]
    return data


def unit_test():
    screen.start()
    screen.cls()
    screen.set_sprite(0, get_test_sprite_data())
    screen.set_transparent_color(True, 0x20)
    screen.bg_color(0x07E0)
    screen.fill_rect(320, 0, 320, 240)
    screen.bg_color(0x001F)
    screen.fill_rect(0, 240, 320, 240)
    screen.bg_color(0xF00F)
    screen.fill_rect(320, 240, 320, 240)
    screen.bg_color(0xF800)
    screen.fill_rect(0, 0, 320, 240)
    screen.fg_color(0xFFFF)
    screen.text_cursor(0, 2)
    screen.text('Hello')
    screen.text_newline()
    screen.text_newline()
    screen.text("Press any key")
    screen.draw_sprite(300, 100, 0)
    screen.show()
    screen.wait(0)
    screen.stop()


if __name__ == '__main__':
    unit_test()
