import sys
import numpy as np
from PIL import Image


def cvt32to16(color):
    r = color[0]
    g = color[1]
    b = color[2]
    a = color[3]
    res = ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)
    if res == 0x20:
        res = 0
    if a == 0:
        res = 0x20
    return res


def process(input_filename, output_filename):
    pimg = Image.open(input_filename).convert('RGBA')
    image = np.array(pimg)
    h, w = image.shape[0], image.shape[1]
    buffer = bytearray(4 + h * w * 2)
    buffer[0] = w & 255
    buffer[1] = (w >> 8) & 255
    buffer[2] = h & 255
    buffer[3] = (h >> 8) & 255
    i = 4
    for y in range(h):
        for x in range(w):
            color = cvt32to16(image[y, x, :])
            buffer[i] = color & 255
            buffer[i + 1] = (color >> 8) & 255
            i = i + 2
    try:
        with open(output_filename, 'wb') as f:
            f.write(buffer)
        print("Success")
    except OSError:
        print("Failed to write output file")


def main():
    if len(sys.argv) < 3:
        print("Usage: png2raw16.py <input image> <output image>")
    else:
        process(sys.argv[1], sys.argv[2])


if __name__ == '__main__':
    main()
