import sys
import cv2
import numpy as np


def load(filename):
    data = open(filename, 'rb').read()
    w = (data[1] << 8) | data[0]
    h = (data[3] << 8) | data[2]
    image = np.zeros((h, w, 3), dtype=np.uint8)
    i = 4
    for y in range(h):
        for x in range(w):
            msb = data[i]
            lsb = data[i + 1]
            image[y, x, 0] = (lsb & 0x1F) << 3
            image[y, x, 1] = ((lsb & 0xE0) >> 5) | ((msb & 7) << 5)
            image[y, x, 2] = (msb & 0xF8)
            i=i+2
    return image


def main():
    if len(sys.argv) < 2:
        print("Usage: showraw.py <raw image file>")
    else:
        cv2.imshow('image', load(sys.argv[1]))
        cv2.waitKey()


if __name__ == '__main__':
    main()
