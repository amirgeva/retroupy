import json
import os

from .app import get_screen
from .utils import Rect
from .bitmatrix import BitMatrix


class SpritesManager:
    def __init__(self):
        self.free_indices = []
        self.last_used = -1
        self.limit = 160

    def clear(self):
        self.free_indices = []
        self.last_used = -1

    def allocate(self, data):
        if len(self.free_indices) > 0:
            sprite_id = self.free_indices[-1]
            del self.free_indices[-1]
        else:
            sprite_id = self.last_used + 1
            if sprite_id >= self.limit:
                return -1
            self.last_used = sprite_id
        get_screen().set_sprite(sprite_id, data)
        return sprite_id


sprites_manager = SpritesManager()


class SpriteSheet:
    def __init__(self, filename=''):
        self.width = 0
        self.height = 0
        self.data = None
        self.sprites = {}
        self.rect = None
        if filename:
            self.load(filename)

    def load(self, filename):
        try:
            data = open(filename, 'rb').read()
            self.width = (int(data[1]) << 8) | int(data[0])
            self.height = (int(data[3]) << 8) | int(data[2])
            self.data = data[4:]
            self.rect = Rect(0, 0, self.width, self.height)
            return True
        except OSError:
            return False

    def get_sprite_data(self, rect):
        if rect in self.sprites:
            return self.sprites.get(rect)
        if rect.valid() and self.rect.contains(rect) and rect.width() == 32 and rect.height() == 32:
            data = bytearray(32 * 32 * 2)
            src = (rect.tl.y * self.width + rect.tl.x) * 2
            dst = 0
            mask = BitMatrix(32, 32)
            mask.setall(True)
            for i in range(32):
                data[dst:(dst + 64)] = self.data[src:(src + 64)]
                for j in range(32):
                    if data[dst + j * 2] == 0x20 and data[dst + j * 2 + 1] == 0:
                        mask.set(j, i, False)
                dst = dst + 64
                src = src + self.width * 2
            sprite_data = sprites_manager.allocate(data), mask
            self.sprites[rect] = sprite_data
        else:
            sprite_data = -1, None
        return sprite_data


sprite_sheets = {}


def get_sprite_sheet(filename):
    if filename in sprite_sheets:
        return sprite_sheets.get(filename)
    s = SpriteSheet(filename)
    sprite_sheets[filename] = s
    return s


# EXPORT
class Sprite(object):
    def __init__(self, sprite_id, mask, duration=0.0, flags=0):
        self.sprite_id = sprite_id
        self.mask = mask
        self.duration = duration
        self.flags = flags

    def draw(self, position):
        get_screen().draw_sprite(position.x, position.y, self.sprite_id, self.flags)

    @staticmethod
    def get_rect():
        return Rect(0, 0, 32, 32)

    @staticmethod
    def deserialize(filename, obj):
        r = [int(a) for a in obj['Rect'].strip().split(',')]
        dur = obj['Duration']
        flags = 0
        if 'Flags' in obj:
            flags = obj['Flags']
        rect = Rect(r[0], r[1], r[2], r[3])
        sheet = get_sprite_sheet(filename)
        sprite_id, mask = sheet.get_sprite_data(rect)
        return Sprite(sprite_id, mask, dur, flags)


# EXPORT
class AnimationSequence(object):
    def __init__(self, name, base_vel=1.0):
        self.name = name
        self.base_vel = base_vel
        self.sprites = []

    def add_sprite(self, sprite):
        self.sprites.append(sprite)

    def deserialize(self, filename, seq):
        self.sprites = []
        for frame in seq['Frames']:
            self.add_sprite(Sprite.deserialize(filename, frame))

    def __getitem__(self, index):
        return self.sprites[index]

    def __len__(self):
        return len(self.sprites)


# EXPORT
class StaticSprite:
    def __init__(self, sprite=None):
        self.sprite = sprite

    def get_current_sprite(self):
        return self.sprite

    def get_rect(self):
        if self.sprite:
            return self.sprite.get_rect()
        return Rect(0, 0, 32, 32)

    def draw(self, pos):
        if self.sprite:
            self.sprite.draw(pos)


# EXPORT
class AnimatedSprite(object):
    def __init__(self):
        self.sheet = None
        self.sequences = {}
        self.flags = {}
        self.active_sequence = None
        self.cur_sprite = 0
        self.dt = 0.0
        self.anim_dir = ''

    def add_flag(self, name, value):
        if name == 'AnimDir':
            self.anim_dir = value
        self.flags[name] = value

    def get_longest_sequence(self):
        mx = 0
        res = None
        for name in self.sequences:
            seq = self.sequences.get(name)
            if len(seq) > mx:
                mx = len(seq)
                res = seq
        return res

    def get_sequence_by_name(self, name):
        return self.sequences.get(name)

    def get_sequence_by_index(self, index):
        for name in self.sequences.keys():
            if index == 0:
                return self.sequences.get(name)
            index -= 1
        return None

    def get_active_sequence_name(self):
        if not self.active_sequence:
            return ''
        return self.active_sequence.name

    def set_active_sequence(self, name):
        if name != self.get_active_sequence_name() and name in self.sequences:
            self.active_sequence = self.sequences.get(name)
            self.dt = 0.0
            self.cur_sprite = 0

    def add_sequence(self, seq):
        self.sequences[seq.name] = seq
        if not self.active_sequence:
            self.active_sequence = seq

    def calculate_axial_velocity(self, velocity):
        if self.anim_dir == 'X':
            return abs(velocity.x)
        if self.anim_dir == 'Y':
            return abs(velocity.y)
        return velocity.length()

    def advance(self, dt, velocity):
        axial_velocity = self.calculate_axial_velocity(velocity)
        # print "axial={}".format(axial_velocity)
        if self.active_sequence and len(self.active_sequence) > 0:
            mult = 1.0
            if self.active_sequence.base_vel > 0 and axial_velocity > 0.001:
                mult = axial_velocity / self.active_sequence.base_vel
            # print "mult={}".format(mult)
            self.dt = self.dt + dt * mult
            # print "self.dt={}".format(self.dt)
            if self.cur_sprite >= len(self.active_sequence):
                self.cur_sprite = 0
            spr = self.active_sequence[self.cur_sprite]
            while self.dt >= spr.duration:
                self.dt = self.dt - spr.duration
                self.cur_sprite += 1
                if self.cur_sprite >= len(self.active_sequence):
                    self.cur_sprite = 0
        return True

    def get_current_sprite(self):
        if self.active_sequence:
            return self.active_sequence[self.cur_sprite]
        return None

    def get_current_height(self):
        spr = self.get_current_sprite()
        if spr:
            return spr.height()
        return 0

    def draw(self, position):
        spr = self.get_current_sprite()
        if spr:
            spr.draw(position)

    def get_rect(self):
        spr = self.get_current_sprite()
        if spr:
            return spr.get_rect()
        return Rect(0, 0, 1, 1)

    def deserialize(self, obj, overrides):
        filename = obj['Image']
        flags = obj['Flags']
        for key in flags:
            self.add_flag(key, flags[key])
        for seq in obj['Sequences']:
            base_vel = seq['BaseVelocity']
            if 'BaseVelocity' in overrides:
                base_vel = overrides.get('BaseVelocity')
            s = AnimationSequence(seq['Name'], base_vel)
            s.deserialize(filename, seq)
            self.add_sequence(s)

    def load(self, filename, overrides={}):
        return self.deserialize(json.load(open(filename, "r")), overrides)


# EXPORT
def load_json_file(filename):
    obj = json.load(open(filename, "r"))
    a = AnimatedSprite()
    a.deserialize(obj)
    return a


# EXPORT
def load_json_str(s):
    obj = json.loads(s)
    a = AnimatedSprite()
    a.deserialize(obj)
    return a


# EXPORT
def load_file(filename):
    return load_json_file(filename)


# EXPORT
def load_str(s):
    return load_json_str(s)


if __name__ == '__main__':
    print(os.getcwd())
