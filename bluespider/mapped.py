# -*- coding: utf-8 -*-

import binascii
import os
try:
    import Image
except ImportError:
    try:
        from PIL import Image
    except ImportError:
        print("Warning: Couldn't import PIL")

from . import lz77
from . import structures
from . import structure_utils
from . import text_translate

axve = {
    'MapHeaders'      : 0x53324,
    'MapLabels'       : 0x3e73c4,
    'Sprites'         : 0x36DC58,
    'SpritePalettes'  : 0x37377C,
}

bpre = {
    'MapHeaders'      : 0x5524C,
    'MapLabels'       : 0x3F1CAC,
    'Sprites'         : 0x39FDB0,
    'SpritePalettes'  : 0x3A5158,
}

bpee = {
    'MapHeaders'      : 543396,
    #'MapLabels'       : 1194820,
    'MapLabels'       : 0x5a147c,
    'Sprites'         : 0x505620,
    'SpritePalettes'  : 0x50BBC8,
}

grayscale_pal = [(i, i, i) for i in range(0, 255, 16)]
grayscale_pal2 = [(i, i, i) for i in range(255, 0, -16)]
GRAYSCALE = False

def hexbytes(s):
    a = binascii.hexlify(s).decode()
    b = ''
    for i in range(len(s)):
        b += a[i*2:i*2+2] + " "
    b = b.rstrip(" ")
    return b

print32bytes = lambda x, rom_contents: print(hexbytes(rom_contents[x:x+32]))

to_int = lambda x: int.from_bytes(x, "little")
to_signed = lambda x: int.from_bytes(x, "little", signed=True)
get_addr = lambda x: int.from_bytes(x, "little") #& 0xFFFFFF

def get_rom_addr(x):
    if x >= 0x8000000:
        x -= 0x8000000
    return x

def rom_addr_to_gba(x):
    if x <= 0x8000000:
        x += 0x8000000
    return x

def check_rom_addr(a):
    if a & 0x8000000 == 0x8000000 or a & 0x9000000 == 0x9000000:
        return a
    else:
        return -1

def read_n_bytes(rom, addr, n):
    addr = get_rom_addr(addr)
    if addr == -1:
        raise Exception("you are trying to read -1")
    return rom[addr:addr+n]

read_u32_at = lambda rom, addr: to_int(read_n_bytes(rom, addr, 4))
read_s32_at = lambda rom, addr: to_signed(read_n_bytes(rom, addr, 4))
read_ptr_at = read_u32_at
read_rom_addr_at = lambda rom, addr: get_rom_addr(
    check_rom_addr(read_u32_at(rom, addr)))
read_u16_at = lambda rom, addr: to_int(read_n_bytes(rom, addr, 2))
read_u8_at = lambda rom, addr: to_int(read_n_bytes(rom, addr, 1))

def write_n_bytes(rom, addr, n, data):
    if len(data) != n:
        raise Exception("data is not the same size as n!")
    rom[addr:addr+n] = data

write_u32_at = (lambda rom, addr, num:
                write_n_bytes(rom, addr, 4, num.to_bytes(4, "little")))
write_rom_ptr_at = (lambda rom, addr, num:
                    write_u32_at(rom, addr, (num + 0x8000000 if num < 0x1000000 and
                                             num != 0 else num)))
write_u16_at = (lambda rom, addr, num:
                write_n_bytes(rom, addr, 2, num.to_bytes(2, "little")))
write_u8_at = (lambda rom, addr, num:
               write_n_bytes(rom, addr, 1, num.to_bytes(1, "little")))

def get_rom_data(rom_code):
    if rom_code == b'AXVE':
        rom_data = axve
        game = 'RS'
    elif rom_code == b'BPRE':
        rom_data = bpre
        game = 'FR'
    elif rom_code == b'BPEE':
        rom_data = bpee
        game = 'EM'
    else:
        raise Exception("ROM code not found")
    return rom_data, game

def get_rom_code(rom_contents):
    return rom_contents[0xAC:0xAC+4]

def get_banks(rom_contents, rom_data=axve, echo=False):
    if echo:
        print("Banks:")
    i = 0
    banks = []
    banks_base_off = read_rom_addr_at(rom_contents, rom_data['MapHeaders'])
    if echo:
        print(hex(banks_base_off))
    while True:
        a = read_rom_addr_at(rom_contents, banks_base_off + i * 4)
        if a == -1:
            if echo:
                print("-1!")
            break
        if echo:
            print(hex(i) + "\t" + hex(a))
        banks.append(a)
        i += 1
    return banks

def get_map_headers(rom_contents, n, banks, echo=False):
    if echo:
        print("Maps in bank {0}:".format(n))
    maps_addr = banks[n]
    if len(banks) > n+1:
        maps_of_next_bank = banks[n+1]
    else:
        maps_of_next_bank = 0
    maps = []
    i = 0
    while True:
        # FIXME: We read too many maps at the end of FR
        addr_offset = maps_addr + i * 4
        if addr_offset == maps_of_next_bank:
            break
        a = read_rom_addr_at(rom_contents, addr_offset)
        if a == -1:
            break
        if echo:
            print(hex(i) + "\t" + hex(a))
        maps.append(a)
        i += 1
    return maps

get_read_function = lambda size: {
    "u8": read_u8_at,
    "u16": read_u16_at,
    "ptr": read_ptr_at,
    "u32": read_u32_at,
    "s32": read_s32_at
}[size]

get_write_function = lambda size: {
    "u8": write_u8_at,
    "u16": write_u16_at,
    "ptr": write_rom_ptr_at,
    "u32": write_u32_at
}[size]

def parse_data_structure(rom_contents, struct, offset):
    data = {}
    for item in struct:
        name, size, pos = item
        data[name] = get_read_function(size)(rom_contents, offset+pos)
        if data[name] == -1:
            data[name] = 0
    data["self"] = get_rom_addr(offset)
    return data

def write_data_structure(rom_contents, struct, data, offset=None):
    if not offset:
        offset = data["self"]
    for item in struct:
        name, size, pos = item
        # ("self", "clear", "null"):
        if name in data and name not in ("self",):
            get_write_function(size)(rom_contents, offset+pos, data[name])

def parse_map_header(rom_contents, map_h):
    struct = structures.map_header
    return parse_data_structure(rom_contents, struct, map_h)

def parse_map_data(rom_contents, map_data_ptr, game='RS'):
    struct = structures.map_data
    return parse_data_structure(rom_contents, struct, map_data_ptr)

def parse_connections_header(rom_contents, connections_header_ptr):
    struct = structures.connections_header
    return parse_data_structure(rom_contents, struct, connections_header_ptr)

def parse_connection_data(rom_contents, connections_header):
    connections = []
    struct = structures.connection_data
    num = connections_header['n_of_connections']
    for connection in range(num):
        ptr = get_rom_addr(connections_header['connection_data_ptr'])
        ptr += structure_utils.size_of(struct) * connection
        connection_data = parse_data_structure(rom_contents, struct, ptr)
        connections.append(connection_data)
    return connections

def get_tileset_header_struct(gamename):
    if gamename == 'RS' or gamename == 'EM':
        return structures.tileset_header_rs
    elif gamename == 'FR':
        return structures.tileset_header_fr
    else:
        raise Exception("game not supported")

def parse_tileset_header(rom_contents, tileset_header_ptr, gamename='RS'):
    struct = get_tileset_header_struct(gamename)
    return parse_data_structure(rom_contents, struct, tileset_header_ptr)

def parse_events_header(rom_contents, events_header_ptr):
    struct = structures.events_header
    return parse_data_structure(rom_contents, struct, events_header_ptr)

def write_events_header(rom_contents, data):
    struct = structures.events_header
    return write_data_structure(rom_contents, struct, data)

write_map_header = lambda rom_contents, data: write_data_structure(
    rom_contents, structures.map_header, data)

write_map_data_header = lambda rom_contents, data: write_data_structure(
    rom_contents, structures.map_data, data)

def parse_events(rom_contents, events_header):
    person_events = []
    warp_events = []
    trigger_events = []
    signpost_events = []
    # We make this thingy to loop nicely
    parsing_functions = (
        (parse_person_event, "n_of_people", "person_events_ptr",
         person_events, 24),
        (parse_warp_event, "n_of_warps", "warp_events_ptr",
         warp_events, 8),
        (parse_trigger_event, "n_of_triggers", "trigger_events_ptr",
         trigger_events, 16),
        (parse_signpost_event, "n_of_signposts", "signpost_events_ptr",
         signpost_events, 12)
    )
    for fun, num_key, start_ptr_key, list, event_size in parsing_functions:
        num = events_header[num_key]
        for event in range(num):
            ptr = get_rom_addr(events_header[start_ptr_key])
            ptr += event_size * event
            event_data = fun(rom_contents, ptr)
            list.append(event_data)
    return person_events, warp_events, trigger_events, signpost_events

def write_events(rom_contents, events_header, events):
    person_events, warp_events, trigger_events, signpost_events = events
    parsing_functions = (
        (write_person_event, "person_events_ptr", person_events, 24),
        (write_warp_event, "warp_events_ptr", warp_events, 8),
        (write_trigger_event, "trigger_events_ptr", trigger_events, 16),
        (write_signpost_event, "signpost_events_ptr", signpost_events, 12)
    )
    for fun, start_ptr_key, list, event_size in parsing_functions:
        for n, event in enumerate(list):
            ptr = get_rom_addr(events_header[start_ptr_key])
            ptr += event_size * n
            fun(rom_contents, event, ptr)

def write_event(rom_contents, event, type, offset=None):
    writing_functions = {
        "person" : write_person_event,
        "warp" : write_warp_event,
        "trigger" : write_trigger_event,
        "signpost" : write_signpost_event,
    }
    writing_functions[type](rom_contents, event, offset)

def parse_person_event(rom_contents, ptr):
    struct = structures.person_event
    return parse_data_structure(rom_contents, struct, ptr)

def write_person_event(rom_contents, event, offset=None):
    struct = structures.person_event
    write_data_structure(rom_contents, struct, event, offset)

def parse_warp_event(rom_contents, ptr):
    struct = structures.warp_event
    return parse_data_structure(rom_contents, struct, ptr)

def write_warp_event(rom_contents, event, offset=None):
    struct = structures.warp_event
    write_data_structure(rom_contents, struct, event, offset)

def parse_trigger_event(rom_contents, ptr):
    struct = structures.trigger_event
    return parse_data_structure(rom_contents, struct, ptr)

def write_trigger_event(rom_contents, event, offset=None):
    struct = structures.trigger_event
    write_data_structure(rom_contents, struct, event, offset)

def parse_signpost_event(rom_contents, ptr):
    struct = structures.signpost_event
    event_header = parse_data_structure(rom_contents, struct, ptr)
    if event_header['type'] < 5:
        struct = (("script_ptr", "ptr", 8),)
        event_header = dict(
            list(event_header.items()) +
            list(parse_data_structure(rom_contents, struct, ptr).items())
        )
        event_header["item_number"] = 0
        event_header["hidden_item_id"] = 0
        event_header["amount"] = 0
    else:
        struct = (
            ("item_number", "u16", 8),
            ("hidden_item_id", "u8", 10),
            ("amount", "u8", 11),
        )
        event_header = dict(
            list(event_header.items()) +
            list(parse_data_structure(rom_contents, struct, ptr).items())
        )
        event_header["script_ptr"] = 0
    return event_header

def write_signpost_event(rom_contents, event, offset=None):
    struct = list(structures.signpost_event)
    if event['type'] < 5:
        struct += (("script_ptr", "ptr", 8),)
    else:
        struct += (
            ("item_number", "u16", 8),
            ("hidden_item_id", "u8", 10),
            ("amount", "u8", 11),
        )
    write_data_structure(rom_contents, struct, event, offset)

def get_pal_colors(rom_contents, pals_ptr, num=0):
    mem = rom_contents[pals_ptr+32*num:pals_ptr+32*(1+num)]
    colors = []
    for i in range(0, 32, 2):
        color_bytes = mem[i:i+2]
        color = int.from_bytes(color_bytes, "little")
        r = (color & 0b11111) * 8
        g = ((color & 0b1111100000) >> 5) * 8
        b = ((color & 0b111110000000000) >> 10) * 8
        colors.append((r, g, b))
    return colors

def build_imgdata_pal(data, size, palette, w):
    ''' With pal '''
    if GRAYSCALE:
        palette = GRAYSCALE
    tiles_per_line = w
    imw, imh = size
    imdata = [0]*imw*imh
    for pos in range(len(data)):
        tile = pos // (8*4) # At 2 pixels per byte, we have 8*8/2 bytes per tile
        x = ((pos-(tile*8*4))%4)*2+((tile % tiles_per_line)*8)
        y = (pos-(tile*8*4))//4 + (tile//tiles_per_line*8)

        color2 = ((data[pos] >> 4) & 0xF)
        color1 = data[pos] & 0xF
        color1 = palette[color1]
        color2 = palette[color2]
        imdata[x+y*imw] = color1
        imdata[x+y*imw+1] = color2
    return imdata

def build_imgdata(data, size, w):
    ''' With no pal '''
    tiles_per_line = w
    imw, imh = size
    imdata = [0]*imw*imh
    for pos in range(len(data)):
        tile = pos // (8*4) # At 2 pixels per byte, we have 8*8/2 bytes per tile
        x = ((pos-(tile*8*4))%4)*2+((tile % tiles_per_line)*8)
        y = (pos-(tile*8*4))//4 + (tile//tiles_per_line*8)

        color2 = ((data[pos] >> 4) & 0xF)
        color1 = data[pos] & 0xF
        imdata[x+y*imw] = color1
        imdata[x+y*imw+1] = color2
    return imdata

def build_img(data, im, palette, w):
    imdata = build_imgdata_pal(data, im.size, palette, w)
    im.putdata(imdata)
    return im

def build_tileset_img(data, im, palette):
    return build_img(data, im, palette, 16)

def build_sprite_img(data, im, palette=grayscale_pal2):
    return build_img(data, im, palette, 2)

def get_tileset_imgdata(rom_contents, tileset_header):
    tileset_img_ptr = tileset_header["tileset_image_ptr"]
    tileset_img_ptr = get_rom_addr(tileset_img_ptr)
    tiles_per_line = 16
    if tileset_header["is_compressed"]:
        decompressed_data = lz77.decompress(rom_contents[
            tileset_img_ptr:tileset_img_ptr+0x8000
        ])
        data = decompressed_data
    else:
        # FIXME: Where do I cut this?
        data = rom_contents[tileset_img_ptr:tileset_img_ptr+0x8000]

    if len(data)*2//(8*8) % tiles_per_line != 0:
        rows = len(data)*2//(8*8)//tiles_per_line + 1
    else:
        rows = len(data)*2//(8*8)//tiles_per_line
    w = tiles_per_line*8
    #h = 0x100
    #if get_rom_code(rom_contents) == b'BPRE':
    #    h = 0x140
    h = rows*8
    return build_imgdata(data, (w, h), 16), w, h

def get_tileset_img(rom_contents, tileset_header):
    ''' Not called from the code, for debugging purposes and future use '''
    data, w, h = get_tileset_imgdata(rom_contents, tileset_header)
    data = color([grayscale_pal], data)[0]
    im = Image.new("RGB", (w, h))
    im.putdata(data)
    return im

def get_block_data(rom_contents, tileset_header, game='RS'):
    block_data_ptr = get_rom_addr(tileset_header['block_data_ptr'])
    t_type = tileset_header['tileset_type']
    if t_type == 0:
        if game == 'RS' or game == 'EM':
            num_of_blocks = 512
        else:
            num_of_blocks = 640
    else:
        behavior_data_ptr = get_rom_addr(tileset_header['behavior_data_ptr'])
        num_of_blocks = (behavior_data_ptr - block_data_ptr) // 16
    length = num_of_blocks*16
    mem = rom_contents[block_data_ptr:block_data_ptr+length]
    return mem

def decode_block_part(part, layer_mem, palettes, imgs):
    TILES_PER_LINE = 16

    offset = part*2
    byte1 = layer_mem[offset]
    byte2 = layer_mem[offset+1]
    tile_num = byte1 | ((byte2 & 0b11) << 8)
    x = (tile_num % TILES_PER_LINE) * 8
    y = (tile_num // TILES_PER_LINE) * 8

    palette_num = byte2 >> 4
    if palette_num >= 13: # XXX
        palette_num = 0
    palette = GRAYSCALE or palettes[palette_num]
    part_img = imgs[palette_num].crop((x, y, x+8, y+8))
    flips = (byte2 & 0xC) >> 2
    if flips & 1:
        part_img = part_img.transpose(Image.FLIP_LEFT_RIGHT)
    if flips & 2:
        part_img = part_img.transpose(Image.FLIP_TOP_BOTTOM)
    return part_img, palette

def build_block_imgs_(blocks_mem, imgs, palettes):
    ''' Build images from the block information and tilesets.
     Every block is 16 bytes, and holds down and up parts for a tile,
     composed of 4 subtiles
     every subtile is 2 bytes
     1st byte and 2nd bytes last (two?) bit(s) is the index in the tile img
     2nd byte's first 4 bits is the color palette index
     2nd byte's final 4 bits is the flip information... and something else,
     I guess
         0b0100 = x flip
     '''
    # TODO: Optimize. A lot.
    block_imgs = []
    base_block_img = Image.new("RGB", (16, 16))
    mask = Image.new("L", (8, 8))
    POSITIONS = {
        0: (0, 0),
        1: (8, 0),
        2: (0, 8),
        3: (8, 8)
    }
    for block in range(len(blocks_mem)//16):
        block_mem = blocks_mem[block*16:block*16+16]
        # Copying is faster than creating
        block_img = base_block_img.copy()
        # Up/down
        for layer in range(2):
            layer_mem = block_mem[layer*8:layer*8+8]
            for part in range(4):
                part_img, pal = decode_block_part(part, layer_mem, palettes, imgs)
                x, y = POSITIONS[part]
                # Transparency
                #mask = Image.eval(part_img, lambda a: 255 if a else 0)
                if layer:
                    mask.putdata([0 if i == pal[0] else 255 for i in part_img.getdata()])
                    block_img.paste(part_img, (x, y, x+8, y+8), mask)
                else:
                    block_img.paste(part_img, (x, y, x+8, y+8))

        block_imgs.append(block_img)
    return block_imgs

try:
    from .fast import build_block_imgs
except ImportError:
    #print("Using slow build_block_imgs function")
    build_block_imgs = build_block_imgs_

def get_imgs(path=["data", "mov_perms"], num=0x40, usepackagedata=True):
    ''' load png images to show in GUI '''
    alpha = Image.new("L", (16, 16), 150)
    img_names = [hex(n)[2:].zfill(2).upper() + '.png' for n in range(num)]
    imgs = []
    if not usepackagedata:
        base_path = os.path.join(*path)
        path = os.path.join(base_path, "N.png")
        if not os.path.exists(path):
            raise IOError("file " + path + " not found")
        else:
            null_image = Image.open(path)
            null_image.putalpha(alpha)
        for img in img_names:
            path = os.path.join(base_path, img)
            if os.path.exists(path):
                imgs.append(Image.open(path))
                imgs[-1].putalpha(alpha)
                #imgs[-1].save(path + ".alpha.png", "PNG")
            else:
                imgs.append(null_image)
    else:
        import pkgutil
        get = lambda x: pkgutil.get_data('bluespider', x)
        import io
        makeimg = lambda x: Image.open(io.BytesIO(x))
        get_img = lambda x: makeimg(get(x))
        base_path = os.path.join(*path)
        null_image = get_img(os.path.join(base_path, "N.png"))
        for img in img_names:
            path = os.path.join(base_path, img)
            try:
                imgs.append(get_img(path))
            except FileNotFoundError:
                imgs.append(null_image)
            imgs[-1].putalpha(alpha)

    return imgs


def parse_map_mem(mem, h, w):
    map = [[0 for i in range(w)] for j in range(h)]
    i = 0
    for row in range(h):
        for tile in range(w):
            # Each tile is 16 bit, 9 bits for tile num. and 7 for attributes
            tbytes = mem[i*2:i*2+2]
            #char = tbytes[0] + tbytes[1]
            tile_num = tbytes[0] | (tbytes[1] & 0b11) << 8
            behavior = (tbytes[1] & 0b11111100) >> 2
            #print(row, tile, h, w)
            map[row][tile] = [tile_num, behavior]
            i += 1

    return map


def map_to_mem(map):
    mem = bytearray(len(map)*len(map[0]))
    i = 0
    for row in map:
        for tile in row:
            [tile_num, behavior] = tile
            byte_1 = 0
            byte_2 = 0
            byte_1 = tile_num & 0xFF
            byte_2 = (tile_num & 0b1100000000) >> 8
            byte_2 |= behavior << 2
            # Each tile is 16 bit, 9 bits for tile num. and 7 for attributes
            mem[i*2:i*2+2] = (byte_1, byte_2)
            i += 1

    return mem


def fits(num, size):
    if size == "u32" or size == "s32" or size == "ptr":
        return num <= 0xFFFFFFFF
    #elif size == "ptr":
    #    return num <= 0xFFFFFF
    elif size == "u16":
        return num <= 0xFFFF
    elif size == "u8":
        return num <= 0xFF

def find_free_space(rom_memory, size, start_pos=None):
    if start_pos is None:
        start_pos = 0x6B0000
    new_offset = rom_memory[start_pos:].index(b'\xFF'*size) + start_pos
    return new_offset

singular_name = {
    "people": "person",
    "warps": "warp",
    "triggers": "trigger",
    "signposts": "signpost",
}

def get_event_data_for_type(type):
    return {
        "person": ("n_of_people", "person_events_ptr"),
        "warp": ("n_of_warps", "warp_events_ptr"),
        "trigger": ("n_of_triggers", "trigger_events_ptr"),
        "signpost": ("n_of_signposts", "signpost_events_ptr"),
    }[type]

def add_event(rom_memory, events_header, type):
    # Everything should be saved to rom_memory before calling this function,
    # and re-read afterwards.
    # We'll move the memory and update the header, but events will remain
    # with old offsets, so they have to be re-read.
    num_key, ptr_key = get_event_data_for_type(type)
    old_offset = get_rom_addr(events_header[ptr_key])
    backup = bytearray(rom_memory)
    num_of_events = events_header[num_key]
    base_size = structure_utils.size_of(structures.events[type])
    size = base_size * num_of_events
    events_memory = bytes(rom_memory[old_offset:old_offset+size])
    print(events_memory)
    rom_memory[old_offset:old_offset+size] = b'\xFF'*size
    new_size = size + base_size
    try:
        new_offset = find_free_space(rom_memory, new_size)
    except ValueError:
        rom_memory[:] = backup
        raise Exception("Your ROM is full!")
    # New event will be zeroed, because it's better than being FF'ed.
    rom_memory[new_offset:new_offset+new_size] = (events_memory +
                                                  b'\x00' * base_size)
    events_header[ptr_key] = new_offset + 0x8000000
    events_header[num_key] += 1

def rem_event(rom_memory, events_header, type):
    num_key, ptr_key = get_event_data_for_type(type)
    base_size = structure_utils.size_of(structures.events[type])
    offset = events_header[ptr_key]
    num_of_events = events_header[num_key]
    old_size = base_size * num_of_events
    rom_memory[offset+old_size:offset+old_size+base_size] = b'\xFF'*base_size
    events_header[num_key] -= 1

def get_map_labels(rom_memory, game, type):
    labels = []
    labels_ptr = get_rom_addr(game["MapLabels"])
    add = (type == 'RS' and 4) or (type == 'EM' and 4) or (type == 'FR' and 0)
    for i in range(0x59 if type == 'RS' else 0x6D): # Magic!
        # RS: [4 unknown bytes][ptr to label][4 unknown bytes][ptr to label]...
        # FR: [ptr to label][ptr to label]...
        ptr = get_rom_addr(read_ptr_at(rom_memory, labels_ptr+i*(4+add)+add))
        end = ptr + rom_memory[ptr:].find(b'\xff')
        mem = rom_memory[ptr:end].replace(b'\xfc', b'')
        label = text_translate.hex_to_ascii(mem).replace("  ", " ")
        labels.append(label)
    return labels


def get_sprite_palette_ptr(rom_memory, pal_num, game):
    #base_offset = read_rom_addr_at(rom_memory, game["SpritePalettes"])
    base_offset = get_rom_addr(game["SpritePalettes"])
    i = 0
    while i < 70:
        offset = base_offset + 8*i
        if read_u8_at(rom_memory, offset + 4) == pal_num:
            return read_ptr_at(rom_memory, offset)
        if read_u8_at(rom_memory, offset + 5) == 0:
            raise Exception("End of palettes, pal num %s not found" % pal_num)
        i += 1
    raise Exception("Security break")

def get_ow_sprites(rom_memory, game):
    # get_pal_colors SpritePalettes
    sprites_table_ptr = get_rom_addr(game['Sprites'])
    sprite_imgs = []
    for i in range(152): # XXX: We need the real number of sprites
        header_ptr = read_rom_addr_at(rom_memory, sprites_table_ptr+i*4)
        if header_ptr == -1:
            break
        header = parse_data_structure(rom_memory, structures.sprite, header_ptr)
        header2_ptr = get_rom_addr(header['header2_ptr'])
        header2 = parse_data_structure(rom_memory, structures.sprite2,
                                       header2_ptr)
        img_ptr = get_rom_addr(header2['img_ptr'])
        pal_ptr = get_rom_addr(get_sprite_palette_ptr(
            rom_memory, header["palette_num"], game
            ))
        pal = get_pal_colors(rom_memory, pal_ptr)
        data = rom_memory[img_ptr:img_ptr+0x100] # XXX
        im = Image.new("RGB", (16, 32)) # XXX
        im = build_sprite_img(data, im, pal)
        sprite_imgs.append(im)
    return sprite_imgs

def get_pals(rc, game, pals1_ptr, pals2_ptr):
    pals = []
    if game == 'RS' or game == 'EM':
        num_of_pals1 = 6
        num_of_pals2 = 7
    else:
        num_of_pals1 = 7
        num_of_pals2 = 6
    for pal_n in range(num_of_pals1):
        palette = get_pal_colors(rc, pals1_ptr, pal_n)
        pals.append(palette)
    for pal_n in range(num_of_pals2):
        palette = get_pal_colors(rc, pals2_ptr,
                                 pal_n+num_of_pals1)
        pals.append(palette)
    return pals

def load_tilesets(rc, game, t1_header, t2_header, pals):
    imgs = []
    t1data, w, h1 = get_tileset_imgdata(rc, t1_header)
    t2data, _, h2 = get_tileset_imgdata(rc, t2_header)
    img1 = Image.new("RGB", (w, h1))
    img2 = Image.new("RGB", (w, h2))
    big_img = Image.new("RGB", (w, h1+h2))
    pos1 = (0, 0, w, h1)
    pos2 = (0, h1, w, h1+h2)
    col1data = color(pals, t1data)
    col2data = color(pals, t2data)

    for i in range(len(pals)):
        colored1 = col1data[i]
        colored2 = col2data[i]
        img1.putdata(colored1)
        img2.putdata(colored2)
        colored_img = big_img.copy()
        colored_img.paste(img1, pos1)
        colored_img.paste(img2, pos2)
        imgs.append(colored_img)

    return imgs

def color(pals, tsdata):
    return [[c[i] for i in tsdata] for c in pals]

def add_banks(rom_memory, banks_ptr, old_len, new_len):
    # The bank table is just a link of offsets terminated by (u32) 0x2
    old_ptr = read_rom_addr_at(rom_memory, banks_ptr)
    # The +4 is for the 02 00 00 00 at the end
    new_size = new_len * 4 + 4
    old_size = old_len * 4 + 4
    new_ptr = find_free_space(rom_memory, new_size)
    try:
        new_ptr = find_free_space(rom_memory, new_size)
    except ValueError:
        raise Exception("Your ROM is full!")
    new = new_len-old_len
    mem = (rom_memory[old_ptr:old_ptr+old_len*4]
           + b'\0\0\0\x08'*new
           + b'\x02\0\0\0')
    rom_memory[new_ptr:new_ptr+new_size] = mem
    rom_memory[old_ptr:old_ptr+old_size] = b'\xFF'*old_size
    return new_ptr

def apply_replacement(replacements, value):
    rvalue = get_rom_addr(value)
    if replacements is not None and rvalue in replacements:
        return replacements[rvalue]
    else:
        return hex(value)

def export_data_structure_pks(struct, data, org=True, replacements=None):
    ''' replacements must be a dict mapping addresses to
    labels which shall replace them in the script '''
    if org is True:
        text = "#org {}\n".format(apply_replacement(replacements, data["self"]))
    elif org is False:
        text = ""
    else:
        text = org
    for name, size, pos in struct:
        if name in data and name != "self":
            text += {"u8": "#byte",
                     "u16": "#hword",
                     "ptr": "#word",
                     "u32": "#word"}[size]
            if size == "ptr":
                value = apply_replacement(replacements, data[name])
            else:
                value = hex(data[name])

            text += " {} '{}\n".format(value, name)
    return text

def export_events_pks(game, events, events_header, replacements=None):
    text = ""
    person_events, warp_events, trigger_events, signpost_events = events
    types = (
        (structures.person_event, "person_events_ptr", person_events, 24),
        (structures.warp_event, "warp_events_ptr", warp_events, 8),
        (structures.trigger_event, "trigger_events_ptr", trigger_events, 16),
        (structures.signpost_event, "signpost_events_ptr", signpost_events, 12)
    )
    for struct, start_ptr_key, events, event_size in types:
        ptr = get_rom_addr(events_header[start_ptr_key])
        text += "'{}\n".format(start_ptr_key.replace("_ptr", ""))
        text += "#org {}\n".format(apply_replacement(replacements, ptr))
        for n, event in enumerate(events):
            text += "'{}\n".format(n+1)
            struct_ = struct
            if struct == structures.signpost_event:
                if event["type"] < 5:
                    struct_ = struct + (("script_ptr", "ptr", 8),)
                else:
                    struct_ = struct + (
                        ("item_number", "u16", 8),
                        ("hidden_item_id", "u8", 10),
                        ("amount", "u8", 11),
                    )
            text += export_data_structure_pks(
                struct_, event, org=False, replacements=replacements)
        text += '\n'
    return text

def export_lscript_table_pks(game, ptr, org=True, replacements=None):
    text = ""
    struct = structures.lscript_entry
    for i in range(20): # safety
        lscript_h = parse_data_structure(game.rom_contents, struct, ptr)
        text += export_data_structure_pks(struct, lscript_h, org, replacements)
        if (lscript_h["type"] == 0):
            break
        ptr += structure_utils.size_of(struct)
    else:
        raise Exception("Too many level scripts (>=20), something is wrong")
    return text

def export_banks_script(game, org=True, label=False):
    text = ""
    if org is True:
        banks_base_off = read_rom_addr_at(game.rom_contents, game.rom_data['MapHeaders'])
        text = "#org {}\n".format(hex(banks_base_off))
    elif org is not False:
        text = "#org {}\n".format(org)

    for bank_n, bank in enumerate(game.banks):
        if label:
            text += "#word @bank_{}\n".format(bank_n)
        else:
            text += "#word {}\n".format(hex(rom_addr_to_gba(bank)))

    return text

def export_maps_script(game, bank_n, org=True, label=False, map_hs=None):
    text = ""
    bank = game.banks[bank_n]
    if org is True:
        text = "#org {}\n".format(hex(bank))
    elif org is not False:
        text = "#org {}\n".format(org)
    if map_hs is None:
        map_hs = get_map_headers(game.rom_contents, bank_n, game.banks)
    for map_n, map_h in enumerate(map_hs):
        if label:
            text += "#word @map_{}_{}_map_header\n".format(bank_n, map_n)
        else:
            text += "#word {}\n".format(hex(rom_addr_to_gba(map_h)))

    return text

def export_script(game, map_data, name_prefix="", label=True):
    replacements = {
        map_data.header['self']: '@map_header',
        map_data.data_header['self']: '@map_data_header',
        map_data.events_header['self']: '@events_header',
        map_data.t1_header['self']: '@t1_header',
        map_data.t2_header['self']: '@t2_header',
        get_rom_addr(map_data.events_header['person_events_ptr']): '@person_events',
        get_rom_addr(map_data.events_header['warp_events_ptr']): '@warp_events',
        get_rom_addr(map_data.events_header['trigger_events_ptr']): '@trigger_events',
        get_rom_addr(map_data.events_header['signpost_events_ptr']): '@signpost_events',
        get_rom_addr(map_data.header['level_script_ptr']): '@level_scripts',
    }
    if name_prefix:
        for r in replacements:
            replacements[r] = name_prefix+replacements[r].replace("@", "")

    if not label:
        replacements = {}

    export = export_data_structure_pks
    text = """'map exported from red alien
'bank n.: {bank_n}
'map n.: {map_n}

'map header
{map_header}
'map data header
{map_data}
't1 header
{t1}
't2 header
{t2}
'events header
{events_header}
'events
{events}
'level scripts
{lscripts}
""".format(bank_n=map_data.bank_n,
           map_n=map_data.map_n,
           map_header=export(structures.map_header,
                             map_data.header, True, replacements),
           map_data=export(structures.map_data,
                           map_data.data_header,
                           True,
                           replacements),
           events_header=export(structures.events_header,
                                map_data.events_header,
                                True,
                                replacements),
           events=export_events_pks(game, map_data.events, map_data.events_header,
                                    replacements),
           lscripts=export_lscript_table_pks(game, map_data.header["level_script_ptr"],
                                             True, replacements),
           t1=export(get_tileset_header_struct(game.name), map_data.t1_header,
                     True, replacements),
           t2=export(get_tileset_header_struct(game.name), map_data.t2_header,
                     True, replacements))
    return text

