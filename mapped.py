
import binascii
from map_printer import *
import os, sys
import lz77
import Image

axve = {
    'MapHeaders'      : 0x53324
    #Maps            : 0x5326C
    #MapLabels       : 0xFBFE0
}

bpre = {
    'MapHeaders'      : 0x5524C
    #Maps            : 0x55194
    #MapLabels       : 0x3F1CAC
}


def hexbytes(s):
    a = binascii.hexlify(s).decode()
    b = ''
    for i in range(len(s)):
        b += a[i*2:i*2+2] + " "
    b = b.rstrip(" ")
    return b

print32bytes = lambda x, rom_contents : print(hexbytes(rom_contents[x:x+32]))

to_int = lambda x : int.from_bytes(x, "little")
get_addr = lambda x : int.from_bytes(x, "little") & 0xFFFFFF

def get_rom_addr(a): # Safer and more useful version
    #a = int.from_bytes(x, "little")
    #print(hex(a))
    if a & 0x8000000 == 0x8000000:
        return a & 0xFFFFFF
    else:
        return -1

def get_rom_addr_at(x, rom_contents):
    return get_rom_addr(to_int(rom_contents[x:x+4]))

def read_n_bytes(rom, addr, n):
    if addr == -1:
        raise Exception("you are trying to read -1")
    return rom[addr:addr+n]

read_long_at = lambda rom, addr : to_int(read_n_bytes(rom, addr, 4))
read_ptr_at = lambda rom, addr : get_rom_addr(read_long_at(rom, addr))
read_short_at = lambda rom, addr : to_int(read_n_bytes(rom, addr, 2))
read_byte_at = lambda rom, addr : to_int(read_n_bytes(rom, addr, 1))

def write_n_bytes(rom, addr, n, data):
    if len(data) != n:
        raise Exception("data is not the same size as n!")
    rom[addr:addr+n] = data

write_long_at = lambda rom, addr, num : write_n_bytes(rom, addr, 4, num.to_bytes(4, "little"))
write_rom_ptr_at = lambda rom, addr, num : write_long_at(rom, addr, num + 0x8000000)
write_short_at = lambda rom, addr, num : write_n_bytes(rom, addr, 2, num.to_bytes(2, "little"))
write_byte_at = lambda rom, addr, num : write_n_bytes(rom, addr, 1, num.to_bytes(1, "little"))


def get_banks(rom_contents, rom_data=axve, echo=False):
    if echo:
        print("Banks:")
    i = 0
    banks = []
    while True:
        a = get_rom_addr_at(get_rom_addr_at(rom_data['MapHeaders'], rom_contents) + i * 4,
                            rom_contents)
        if a == -1:
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
        a = get_rom_addr_at(maps_addr + i * 4, rom_contents)
        if a == -1 or maps_addr + i * 4 == maps_of_next_bank:
            break
        if echo:
            print(hex(i) + "\t" + hex(a))
        maps.append(a)
        i += 1
    return maps

# That's the kind of thing lisp's macros are useful for, right?
# Dunno, I don't know lisp =P
read_function = lambda size : {
            "byte": read_byte_at,
            "short": read_short_at,
            "ptr": read_ptr_at,
            "long": read_long_at
        }[size]

write_function = lambda size : {
            "byte": write_byte_at,
            "short": write_short_at,
            "ptr": write_rom_ptr_at,
            "long": write_long_at
        }[size]

def parse_data_structure(rom_contents, struct, offset):
    data = {}
    for item in struct:
        name, size, pos = item
        data[name] = read_function(size)(rom_contents, offset+pos)
        if data[name] == -1:
            data[name] = 0
    return data

def parse_map_header(rom_contents, map_h):
    struct = (
            ("map_data_ptr", "ptr", 0),
            ("event_data_ptr", "ptr", 4),
            ("level_script_ptr", "ptr", 8),
            ("connections_ptr", "ptr", 12),
            ("song_index", "short", 16),
            ("map_ptr_index", "short", 18),
            ("label_index", "byte", 20),
            ("is_a_cave", "byte", 21),
            ("weather", "byte", 22),
            ("map_type", "byte", 23),
            # Unknown at 24-25
            ("show_label", "byte", 26),
            ("battle_type", "byte", 27),
            )
    return parse_data_structure(rom_contents, struct, map_h)

def parse_map_data(rom_contents, map_data_ptr, game):
    struct = (
            ("h", "long", 0),
            ("w", "long", 4),
            ("border_ptr", "ptr", 8),
            ("tilemap_ptr", "ptr", 12),
            ("global_tileset_ptr", "ptr", 16),
            ("local_tileset_ptr", "ptr", 20),
            # FR only
            ("border_w", "byte", 24),
            ("border_h", "byte", 25)
            )
    return parse_data_structure(rom_contents, struct, map_data_ptr)

def parse_tileset_header(rom_contents, tileset_header_ptr, game='RS'):
    struct_base = (
            ("is_compressed", "byte", 0),
            ("tileset_type", "byte", 1),
            # 0000
            ("tileset_image_ptr", "ptr", 4),
            ("palettes_ptr", "ptr", 8),
            ("block_data_ptr", "ptr", 12),
            )
    struct_rs = struct_base + (
            ("behavior_data_ptr", "ptr", 16),
            ("animation_data_ptr", "ptr", 20),
            )
    struct_fr = struct_base + (
            ("animation_data_ptr", "ptr", 16),
            ("behavior_data_ptr", "ptr", 20),
            )
    if game == 'RS':
        struct = struct_rs
    elif game == 'FR':
        struct = struct_fr
    else:
        raise Exception("game not supported")
    return parse_data_structure(rom_contents, struct, tileset_header_ptr)

def parse_events_header(rom_contents, events_header_ptr):
    struct = (
            ("n_of_people", "byte", 0),
            ("n_of_warps", "byte", 1),
            ("n_of_triggers", "byte", 2),
            ("n_of_signposts", "byte", 3),
            ("people_events_ptr", "ptr", 4),
            ("warp_events_ptr", "ptr", 8),
            ("trigger_events_ptr", "ptr", 12),
            ("singpost_events_ptr", "ptr", 16)
            )
    return parse_data_structure(rom_contents, struct, events_header_ptr)

def parse_events(rom_contents, events_header):
    person_events = []
    warp_events = []
    trigger_events = []
    signpost_events = []
    # We make this thingy to loop nicely
    parsing_functions = (
            (parse_person_event, "n_of_people", "people_events_ptr", person_events, 24),
            (parse_warp_event, "n_of_warps", "warp_events_ptr", warp_events, 8),
            (parse_trigger_event, "n_of_triggers", "trigger_events_ptr", trigger_events, 16),
            (parse_signpost_event, "n_of_signposts", "singpost_events_ptr", signpost_events, 12)
        )
    for fun, num_key, start_ptr_key, list, event_size in parsing_functions:
        num = events_header[num_key]
        for event in range(num):
            ptr = events_header[start_ptr_key] + event_size * event
            event_data = fun(rom_contents, ptr)
            list.append(event_data)
    print(warp_events)
    return person_events, warp_events, trigger_events, signpost_events

def parse_person_event(rom_contents, ptr):
    struct = (
            ("person_num", "byte", 0),
            ("sprite_num", "byte", 1),
            ("unknown1", "byte", 2),
            ("unknown2", "byte", 3),
            ("x", "short", 4),
            ("y", "short", 6),
            ("unknown3", "byte", 8),
            ("mov_type", "byte", 9),
            ("mov", "byte", 10),
            ("unknown4", "byte", 11),
            ("is_a_trainer", "byte", 12),
            ("unknown5", "byte", 13),
            ("radius", "short", 14),
            ("script_ptr", "ptr", 16),
            ("flag", "short", 20),
            ("unknown6", "byte", 22),
            ("unknown7", "byte", 23),
            )
    return parse_data_structure(rom_contents, struct, ptr)

# s/"\(.\{-}\)" : read_\(.\{-}\)_at(rom_contents, ptr[+]\?/("\1", "\2", /
def parse_warp_event(rom_contents, ptr):
    struct = (
            ("x", "short", 0),
            ("y", "short", 2),
            ("unknown", "byte", 4),
            ("warp_num", "byte", 5),
            ("map_num", "byte", 6),
            ("bank_num", "byte", 7),
        )
    return parse_data_structure(rom_contents, struct, ptr)

def parse_warp_event_old(rom_contents, ptr):
    struct = (
            ("x", "short", 0),
            ("y", "short", 2),
            ("unknown", "byte", 4),
            ("warp_num", "byte", 5),
            ("map_num", "byte", 6),
            ("bank_num", "byte", 7),
        )
    return parse_data_structure(rom_contents, struct, ptr)

def parse_trigger_event(rom_contents, ptr):
    struct = (
            ("x", "short", 0),
            ("y", "short", 2),
            ("unknown", "short", 4),
            ("var_num", "short", 6),
            ("var_value", "short", 8),
            ("unknown2", "byte", 10),
            ("unknown3", "byte", 11),
            ("script_offset", "ptr", 12),
        )
    return parse_data_structure(rom_contents, struct, ptr)

def parse_signpost_event(rom_contents, ptr):
    struct = (
            ("x", "short", 0),
            ("y", "short", 2),
            ("talking_level", "byte", 4),
            ("type", "byte", 5),
            ("unknown", "byte", 6),
            ("unknown", "byte", 7),
        )
    event_header = parse_data_structure(rom_contents, struct, ptr)
    if event_header['type'] < 5:
        #event_header["script_offset"] = read_ptr_at(rom_contents, ptr+8)
        struct = (("script_offset", "ptr", 8),)
        event_header = dict(
                list(event_header.items()) +
                list(parse_data_structure(rom_contents, struct, ptr).items())
                )
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
    return event_header

def get_tileset_img(rom_contents, tileset_header):
    # TODO: Palettes
    tileset_img_ptr = tileset_header["tileset_image_ptr"]
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
    #pixels = len(decompressed_data)*2
    w = tiles_per_line*8
    #h = pixels//w
    h = rows*8
    #print("lalalal", (w, h), len(data))
    im = Image.new("RGB", (w, h))
    #imlist = []
    for pos in range(len(data)):
        tile = pos // (8*4) # At 2 pixels per byte, we have 8*8/2 bytes per tile
        x = ((pos-(tile*8*4))%4)*2+((tile % tiles_per_line)*8)
        y = (pos-(tile*8*4))//4 + (tile//tiles_per_line*8)

        if pos < len(data):
            color2 = ((data[pos] >> 4) & 0xF)
            color1 = data[pos] & 0xF
        else:
            color1 = 0
            color2 = 0
        color1 *= 255//16
        color2 *= 255//16
        color1 = (color1, color1, color1)
        color2 = (color2, color2, color2)
        try:
            #print(pos, tile, x, y, color1)
            im.putpixel((x, y), color1)
            #print(pos, tile, x+1, y, color2)
            im.putpixel((x+1, y), color2)
        except Exception as e:
            print(x, y, w, h, pos, len(data), tile)
            print(e)
            raise Exception()


    #    imlist.append((x, y, color1))
    #    imlist.append((x+1, y, color2))
    #im = Image.new("RGB", (16*8, 400))
    #for pixel in imlist:
    #    im.putpixel((pixel[0], pixel[1]), pixel[2])
    return im


def get_block_data(rom_contents, tileset_header, game='RS'):
    block_data_ptr = tileset_header['block_data_ptr']
    t_type = tileset_header['tileset_type']
    if t_type == 0:
        if game == 'RS':
            num_of_blocks = 512
        else:
            num_of_blocks = 640
    else:
        behavior_data_ptr = tileset_header['behavior_data_ptr']
        num_of_blocks = (behavior_data_ptr - block_data_ptr) // 16
        #raise Exception('TO DO')
    length = num_of_blocks*16
    mem = rom_contents[block_data_ptr:block_data_ptr+length]
    #for block_i in range(num_of_blocks):
    #    pos = block_i*16
    #    block_mem = mem[pos:pos+16]
    #return block_mem
    return mem

def build_block_imgs(blocks_mem, img):
    # Every block is 16 bytes, and holds down and up parts for a tile,
    # composed of 4 subtiles
    # every subtile is 2 bytes
    # 1st byte and 2nd bytes last (two?) bit(s) is the index in the tile img
    # 2nd byte's first 4 bits is the color palette index
    # 2nd byte's final 4 bits is the flip information... and something else, I guess
    #     0b0100 = x flip
    #img.save("tileset.png", "PNG")
    block_imgs = []
    tiles_per_line = 16
    #print('--------')
    #print(len(blocks_mem))
    for block in range(len(blocks_mem)//16):
        block_mem = blocks_mem[block*16:block*16+16]
        block_img = Image.new("RGB", (16, 16))
        #print("---", block)
        # Up/down
        for layer in range(2):
            layer_mem = block_mem[layer*8:layer*8+8]
            for part in range(4):
                part_mem = layer_mem[part*2:part*2+2]
                tile_num = part_mem[0] | ((part_mem[1] & 0b11) << 8)
                #if len(blocks_mem)*16 < 200*16:
                #print(tile_num)
                palette_num = part_mem[1] >> 4
                flips = (part_mem[1] & 0xC) >> 2

                x = tile_num % tiles_per_line
                y = tile_num // tiles_per_line
                x *= 8
                y *= 8
                x2 = x + 8
                y2 = y + 8
                pos = (x, y, x2, y2)
                part_img = img.crop(pos)
                if flips & 1:
                    part_img = part_img.transpose(Image.FLIP_LEFT_RIGHT)
                if flips & 2:
                    part_img = part_img.transpose(Image.FLIP_TOP_BOTTOM)
                # the four positions
                pos = {
                        0: (0,0),
                        1: (1,0),
                        2: (0,1),
                        3: (1,1)
                      }
                x, y = pos[part]
                x *= 8
                y *= 8
                #mask = Image.eval(part_img, lambda a: 255 if a == 0 else 0)
                mask = Image.eval(part_img, lambda a: 255 if a != 0 else 0)
                mask = mask.convert('L')
                #print(mask)
                block_img.paste(part_img, (x, y, x+8, y+8), mask)
                #block_img.paste(part_img, (x, y, x+8, y+8), (0, 0, 0))

                #mask = Image.eval(part_img, lambda a: print(a))
        block_imgs.append(block_img)
    return block_imgs

def get_imgs(path=["data", "mov_perms"], num=0x40):
    base_path = os.path.join(*path)
    alpha = Image.new("L", (16, 16), 150)
    imgs = []
    img_paths = [hex(n)[2:].zfill(2).upper() + '.png' for n in range(num)]
    path = os.path.join(base_path, "N.png")
    if not os.path.exists(path):
        raise IOError("file " + path + " not found")
    else:
        null_image = Image.open(path)
        null_image.putalpha(alpha)
    for img in img_paths:
        path = os.path.join(base_path, img)
        if os.path.exists(path):
            imgs.append(Image.open(path))
            imgs[-1].putalpha(alpha)
            #imgs[-1].save(path + ".alpha.png", "PNG")
        else:
            imgs.append(null_image)
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




