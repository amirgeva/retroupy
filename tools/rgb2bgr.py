import sys


def process(filename):
    with open(filename, 'rb') as f:
        data = bytearray(f.read())
    i = 4
    while i < len(data):
        lsb = data[i]
        msb = data[i + 1]
        r = lsb & 0x1F
        lsb = (lsb & 0xE0) | ((msb & 0xF8) >> 3)
        msb = (msb & 0x07) | (r << 3)
        data[i] = lsb
        data[i + 1] = msb
        i = i + 2
    open(filename, 'wb').write(bytes(data))


def main():
    if len(sys.argv) < 2:
        print("Usage: <raw image file>")
    else:
        process(sys.argv[1])


if __name__ == '__main__':
    main()
