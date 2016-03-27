# -*- coding: utf-8 -*-

# types
u8 = "u8"
u16 = "u16"
u32 = "u32"
s32 = "s32"
ptr = "ptr"

bytes_in_size = {
    u8: 1,
    u16: 2,
    u32: 4,
    s32: 4,
    ptr: 4
}

def calculate_offsets(*structure):
    """
    take this:
(
    ("x", u16),
    ("y", u16),
    ("talking_level", u8),
    ("type", u8),
    ("unknown1", u8),
    ("unknown2", u8),
)
    and make this (add offset for every field):
(
    ("x", u16, 0),
    ("y", u16, 2),
    ("talking_level", u8, 4),
    ("type", u8, 5),
    ("unknown1", u8, 6),
    ("unknown2", u8, 7),
)
    """
    i = 0
    out = []
    for name, btype in structure:
        out.append((name, btype, i))
        i += bytes_in_size[btype]
    return tuple(out)

def to_dict(structure):
    d = {}
    for element in structure:
        key, size, pos = element
        d[key] = (size, pos)
    return d

def size_of(structure):
    total = 0
    for _, size, _ in structure:
        total += bytes_in_size[size]
    return total
