from .doc import Document, Line
from .view import View


def main(filename):
    doc = Document(filename)
    view = View(screen, doc)
    view.redraw_all()
    screen.show()
    key = 0
    while True:
        key = wait_for_key()
        # print(key)
        if len(key) == 1:
            view.insert_text(key)
        if key == 'Enter':
            view.enter()
        if key == 'Backspace':
            view.backspace()
        if key == 'Delete':
            view.delete()
        if key == 'Left':
            view.move_cursor(-1,0)
        if key == 'Right':
            view.move_cursor(1,0)
        if key == 'Up':
            view.move_cursor(0,-1)
        if key == 'Down':
            view.move_cursor(0,1)
        if key == 'Home':
            view.move_cursor(-100000, 0)
        if key == 'End':
            view.move_cursor(100000, 0)
        if key == 'Escape':
            break
    screen.stop()


full_python = True
try:
    from sim.screen import screen
    from sim.kbd import wait_for_key
    import sys

    screen.start()
    screen.blink(True)
except ImportError:
    full_python = False
    from gpu.screen import screen

if full_python and __name__ == '__main__':
    filename = ''
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    main(filename)
