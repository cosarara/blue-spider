
import binascii
import os, sys
try:
    import Image
    import ImageQt
except:
    try:
        from PIL import Image, ImageQt
    except:
        print("Warning: Couldn't import PIL")

from . import lz77
from . import structures
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

print32bytes = lambda x, rom_contents : print(hexbytes(rom_contents[x:x+32]))

to_int = lambda x : int.from_bytes(x, "little")
get_addr = lambda x : int.from_bytes(x, "little") #& 0xFFFFFF

def get_rom_addr(x):
    if x >= 0x8000000:
        x -= 0x8000000
    #if x < 0:
    #    raise Exception("Address < 0 (%s)" % x)
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

read_long_at = lambda rom, addr : to_int(read_n_bytes(rom, addr, 4))
read_ptr_at = read_long_at
read_rom_addr_at = lambda rom, addr : get_rom_addr(
    check_rom_addr(read_long_at(rom, addr))
    )
read_short_at = lambda rom, addr : to_int(read_n_bytes(rom, addr, 2))
read_byte_at = lambda rom, addr : to_int(read_n_bytes(rom, addr, 1))

def write_n_bytes(rom, addr, n, data):
    if len(data) != n:
        raise Exception("data is not the same size as n!")
    rom[addr:addr+n] = data

write_long_at = (lambda rom, addr, num :
        write_n_bytes(rom, addr, 4, num.to_bytes(4, "little")))
write_rom_ptr_at = (lambda rom, addr, num :
        write_long_at(rom, addr, (num + 0x8000000 if num < 0x1000000 and
                                                     num != 0 else num)))
write_short_at = (lambda rom, addr, num :
        write_n_bytes(rom, addr, 2, num.to_bytes(2, "little")))
write_byte_at = (lambda rom, addr, num :
        write_n_bytes(rom, addr, 1, num.to_bytes(1, "little")))


def get_banks(rom_contents, rom_data=axve, echo=False):
    if echo:
        print("Banks:")
    i = 0
    banks = []
    banks_base_off = read_rom_addr_at(rom_contents, rom_data['MapHeaders'])
    while True:
        a = read_rom_addr_at(rom_contents, banks_base_off + i * 4)
        if a == -1:
            if echo: print("-1!")
            break
        if echo:
            print(hex(i) + "\t" + hex(a))
        banks.append(a)
        i += 1
    return banks

def get_map_headers(rom_contents, n, banks, echo=False):
    # TODO: I think we stop loading maps too late,
    #       on the last bank
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

get_read_function = lambda size : {
            "byte": read_byte_at,
            "short": read_short_at,
            "ptr": read_ptr_at,
            "long": read_long_at
        }[size]

get_write_function = lambda size : {
            "byte": write_byte_at,
            "short": write_short_at,
            "ptr": write_rom_ptr_at,
            "long": write_long_at
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
        if name in data and name not in ("self", "clear", "null"):
            get_write_function(size)(rom_contents, offset+pos, data[name])

def parse_map_header(rom_contents, map_h):
    struct = structures.map_header
    return parse_data_structure(rom_contents, struct, map_h)

def parse_map_data(rom_contents, map_data_ptr, game='RS'):
    struct = structures.map_data
    return parse_data_structure(rom_contents, struct, map_data_ptr)

def parse_tileset_header(rom_contents, tileset_header_ptr, game='RS'):
    struct_rs = structures.tileset_header_rs
    struct_fr = structures.tileset_header_fr
    if game == 'RS' or game == 'EM':
        struct = struct_rs
    elif game == 'FR':
        struct = struct_fr
    else:
        raise Exception("game not supported")
    return parse_data_structure(rom_contents, struct, tileset_header_ptr)

def parse_events_header(rom_contents, events_header_ptr):
    struct = structures.events_header
    return parse_data_structure(rom_contents, struct, events_header_ptr)

def write_events_header(rom_contents, data):
    struct = structures.events_header
    return write_data_structure(rom_contents, struct, data)

write_map_header = lambda rom_contents, data : write_data_structure(
        rom_contents, structures.map_header, data)

write_map_data_header = lambda rom_contents, data : write_data_structure(
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
        event_header["ammount"] = 0
    else:
        struct = (
            ("item_number", "short", 8),
            ("hidden_item_id", "byte", 10),
            ("ammount", "byte", 11),
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
            ("item_number", "short", 8),
            ("hidden_item_id", "byte", 10),
            ("ammount", "byte", 11),
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

def build_imgdata(data, size, palette, w):
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

def build_img(data, im, palette, w):
    imdata = build_imgdata(data, im.size, palette, w)
    im.putdata(imdata)
    return im

def build_tileset_img(data, im, palette):
    return build_img(data, im, palette, 16)

def build_sprite_img(data, im, palette=grayscale_pal2):
    return build_img(data, im, palette, 2)

def get_tileset_imgdata(rom_contents, tileset_header, pal):
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
    h = rows*8
    return build_imgdata(data, (w, h), pal, 16), w, h

def get_tileset_img(rom_contents, tileset_header, pal):
    data, w, h = get_tileset_imgdata(rom_contents, tileset_header, pal)
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

def build_block_imgs(blocks_mem, imgs, palettes):
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
    tiles_per_line = 16
    base_block_img = Image.new("RGB", (16, 16))
    mask = Image.new("L", (8, 8))
    positions = {
            0: (0,0),
            1: (8,0),
            2: (0,8),
            3: (8,8)
          }
    for block in range(len(blocks_mem)//16):
        block_mem = blocks_mem[block*16:block*16+16]
        # Copying is faster than creating
        block_img = base_block_img.copy()
        # Up/down
        for layer in range(2):
            layer_mem = block_mem[layer*8:layer*8+8]
            for part in range(4):
                d = part*2
                byte1 = layer_mem[d]
                byte2 = layer_mem[d+1]
                tile_num = byte1 | ((byte2 & 0b11) << 8)
                palette_num = byte2 >> 4
                palette = GRAYSCALE or palettes[palette_num]
                img = imgs[palette_num]
                flips = (byte2 & 0xC) >> 2
                x = (tile_num % tiles_per_line) * 8
                y = (tile_num // tiles_per_line) * 8
                pos = (x, y, x+8, y+8)
                part_img = img.crop(pos)
                if flips & 1:
                    part_img = part_img.transpose(Image.FLIP_LEFT_RIGHT)
                if flips & 2:
                    part_img = part_img.transpose(Image.FLIP_TOP_BOTTOM)
                x, y = positions[part]
                # Transparency
                #mask = Image.eval(part_img, lambda a: 255 if a else 0)
                t = palette[0]
                if layer:
                    img_data = tuple(part_img.getdata())
                    #mask_data = tuple(map(lambda p : (0 if p == t else 255),
                    #                  img_data))
                    mask_data = [0 if i == t else 255 for i in img_data]
                    mask.putdata(mask_data)
                    block_img.paste(part_img, (x, y, x+8, y+8), mask)
                else:
                    block_img.paste(part_img, (x, y, x+8, y+8))

        block_imgs.append(block_img)
    return block_imgs

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
        get = lambda x : pkgutil.get_data('bluespider', x)
        import io
        makeimg = lambda x : Image.open(io.BytesIO(x))
        get_img = lambda x : makeimg(get(x))
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
    if size == "long" or size == "ptr":
        return num <= 0xFFFFFFFF
    #elif size == "ptr":
    #    return num <= 0xFFFFFF
    elif size == "short":
        return num <= 0xFFFF
    elif size == "byte":
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

def add_event(rom_memory, events_header, type):
    # Everything should be saved to rom_memory before calling this function,
    # and re-read afterwards.
    # We'll move the memory and update the header, but events will remain
    # with old offsets, so they have to be re-read.
    stype = singular_name[type]
    num_key = 'n_of_' + type
    ptr_key = stype + "_events_ptr"
    old_offset = get_rom_addr(events_header[ptr_key])
    backup = bytearray(rom_memory)
    num_of_events = events_header[num_key]
    base_size = structures.size_of(structures.events[stype])
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
    stype = singular_name[type]
    num_key = 'n_of_' + type
    ptr_key = stype + "_events_ptr"
    base_size = structures.size_of(structures.events[stype])
    offset = events_header[ptr_key]
    num_of_events = events_header[num_key]
    old_size = base_size * num_of_events
    rom_memory[offset+old_size:offset+old_size+base_size] = b'\xFF'*base_size
    events_header[num_key] -= 1

def get_map_labels(rom_memory, game=axve, type='RS'):
    labels = []
    #labels_ptr = read_ptr_at(rom_memory, game["MapLabels"])
    labels_ptr = get_rom_addr(game["MapLabels"])
    add = (type == 'RS' and 4) or (type == 'EM' and 4) or (type == 'FR' and 0)
    for i in range(0x59 if type=='RS' else 0x6D): # Magic!
        # RS: [4 unknown bytes][ptr to label][4 unknown bytes][ptr to label]...
        # FR: [ptr to label][ptr to label]...
        ptr = get_rom_addr(read_ptr_at(rom_memory, labels_ptr+i*(4+add)+add))
        end = ptr + rom_memory[ptr:].find(b'\xff')
        mem = rom_memory[ptr:end].replace(b'\xfc', b'')
        label = text_translate.hex_to_ascii(mem).replace("  ", " ")
        labels.append(label)
    return labels


def get_sprite_palette_ptr(rom_memory, pal_num, game=axve):
    base_offset = get_rom_addr(game["SpritePalettes"])
    i = 0
    while True:
        offset = base_offset + 8*i
        if read_byte_at(rom_memory, offset + 4) == pal_num:
            return read_ptr_at(rom_memory, offset)
        if read_byte_at(rom_memory, offset + 5) == 0:
            raise Exception("End of palettes, pal num %s not found" % pal_num)
        if i > 20:
            raise Exception("Security break")
        i += 1

def get_ow_sprites(rom_memory, game=axve):
    # get_pal_colors SpritePalettes
    sprites_table_ptr = get_rom_addr(game['Sprites'])
    sprite_imgs = []
    for i in range(152): # XXX
        header_fullptr = read_long_at(rom_memory, sprites_table_ptr+i*4)
        if (header_fullptr & 0x8000000 != 0x8000000 and
            header_fullptr & 0x9000000 != 0x9000000):
            break
        header_ptr = get_rom_addr(
                read_ptr_at(rom_memory, sprites_table_ptr+i*4))
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

# This listcomp takes 0.127 seconds in my slow atom, which accumulates
# to 3.3 sec. total for every map load. Numpy, C, whatever?
#color = lambda c, data : [c[i] if i in c else (0, 0, 0) for i in data]

def load_tilesets(rc, game, t1_header, t2_header, pals):
    imgs = []
    #palette = grayscale_pal
    palette = [i for i in range(16)]
    t1data, w, h1 = get_tileset_imgdata(rc, t1_header, palette)
    t2data, _, h2 = get_tileset_imgdata(rc, t2_header, palette)
    img1 = Image.new("RGB", (w, h1))
    img2 = Image.new("RGB", (w, h2))
    big_img = Image.new("RGB", (w, h1+h2))
    pos1 = (0, 0, w, h1)
    pos2 = (0, h1, w, h1+h2)
    for pal in pals:
        c = {}
        for i in range(16):
            c[palette[i]] = pal[i]
        colored1 = [c[i] if i in c else (0, 0, 0) for i in t1data]
        #color(c, t1data)
        img1.putdata(colored1)
        colored2 = [c[i] if i in c else (0, 0, 0) for i in t2data]
        #color(c, t2data)
        img2.putdata(colored2)
        colored_img = big_img.copy()
        colored_img.paste(img1, pos1)
        colored_img.paste(img2, pos2)
        imgs.append(colored_img)

    return imgs

def add_banks(rom_memory, banks_ptr, old_len, new_len):
    # The bank table is just a link of offsets terminated by (long) 0x2
    old_ptr = get_rom_addr(banks_ptr)
    new_size = new_len * 4 + 4
    new_ptr = find_free_space(rom_memory, new_size)
    try:
        new_ptr = find_free_space(rom_memory, new_size)
    except ValueError:
        raise Exception("Your ROM is full!")
    new = new_len-old_len
    mem = (rom_memory[old_ptr:old_ptr+old_len*4]
            + b'\x08\0\0\0'*new
            + b'\x02\0\0\0')
    print("********")
    print(len(rom_memory[new_ptr:new_ptr+new_size]), len(mem))
    rom_memory[new_ptr:new_ptr+new_size] = mem
    return new_ptr

