import keyboard
import cv2


# EXPORT
def is_pressed(name):
    return keyboard.is_pressed(name)


key_names = {13: 'Enter', 27: 'Escape', 9: 'Tab', 8: 'Backspace',
             0x250000: 'Left', 0x260000: 'Up', 0x270000: 'Right', 0x280000: 'Down',
             0x210000: 'PageUp', 0x220000: 'PageDown', 0x230000: 'End', 0x240000: 'Home',
             0x2d0000: 'Insert', 0x2e0000: 'Delete'
             }


def wait_for_key():
    prefix = ''
    name = ''
    while len(name) == 0:
        key = cv2.waitKeyEx()
        if is_pressed('shift'):
            prefix = prefix + "Shift+"
        if is_pressed('ctrl'):
            prefix = prefix + "Ctrl+"
        if is_pressed('alt'):
            prefix = prefix + "Alt+"
        if key >= 32 and key < 127:
            name = chr(key)
        elif key in key_names:
            name = key_names.get(key)
        #print(f'key={prefix}{key}  {hex(key)}')
    return prefix + name
