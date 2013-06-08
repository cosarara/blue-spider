
import binascii
from map_printer import *
import sys
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

#print32bytes = lambda x : print(hexbytes(rom_contents[x:x+32]))

to_int = lambda x : int.from_bytes(x, "little")
get_addr = lambda x : int.from_bytes(x, "little") & 0xFFFFFF

def get_rom_addr(a): # Safer and more useful version
    #a = int.from_bytes(x, "little")
    #print(hex(a))
    if a & 0x8000000 == 0x8000000:
        return a & 0xFFFFFF
    else:
        return -1
        #raise Exception("that wasn't a pointer")

def get_rom_addr_at(x, rom_contents):
    return get_rom_addr(to_int(rom_contents[x:x+4]))

def read_n_bytes(rom, addr, n):
    if addr == -1:
        raise Exception("you are trying to read -1")
    return rom[addr:addr+n]

read_long_at = lambda rom, addr : read_n_bytes(rom, addr, 4)
read_ptr_at = read_long_at
read_short_at = lambda rom, addr : read_n_bytes(rom, addr, 2)
read_byte_at = lambda rom, addr : read_n_bytes(rom, addr, 1)

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

def parse_map_header(rom_contents, map_h):
    map_data_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_h)))
    event_data_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_h+4)))
    level_script_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_h+8)))
    connections_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_h+12)))
    song_index = to_int(read_short_at(rom_contents, map_h+16))
    map_ptr_index = to_int(read_short_at(rom_contents, map_h+18))
    label_index = to_int(read_byte_at(rom_contents, map_h+20))
    is_a_cave = to_int(read_byte_at(rom_contents, map_h+21))
    weather = to_int(read_byte_at(rom_contents, map_h+22))
    map_type = to_int(read_byte_at(rom_contents, map_h+23))
    # Unknown at 24-25
    show_label = to_int(read_byte_at(rom_contents, map_h+26))
    battle_type = to_int(read_byte_at(rom_contents, map_h+27))
    map_header = {
            "map_data_ptr": map_data_ptr,
            "event_data_ptr": event_data_ptr,
            "level_script_ptr": level_script_ptr,
            "connections_ptr": connections_ptr,
            "song_index": song_index,
            "map_ptr_index": map_ptr_index,
            "label_index": label_index,
            "is_a_cave": is_a_cave,
            "weather": weather,
            "map_type": map_type,
            "show_label": show_label,
            "battle_type": battle_type
            }
    return map_header

def parse_map_data(rom_contents, map_data_ptr, game):
    #print(game)
    w = to_int(read_long_at(rom_contents, map_data_ptr+4))
    h = to_int(read_long_at(rom_contents, map_data_ptr))
    border_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_data_ptr+8)))
    tilemap_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_data_ptr+12)))
    global_tileset_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_data_ptr+16)))
    local_tileset_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_data_ptr+20)))
    # applies only to FR:
    border_w = to_int(read_byte_at(rom_contents, map_data_ptr+24))
    border_h = to_int(read_byte_at(rom_contents, map_data_ptr+25))
    map_data = {
            "w" : w,
            "h" : h,
            "border_ptr" : border_ptr,
            "tilemap_ptr" : tilemap_ptr, # The real map data
            "global_tileset_ptr": global_tileset_ptr,
            "local_tileset_ptr": local_tileset_ptr,
            "border_w": border_w,
            "border_h": border_h,
        }
    return map_data

def parse_tileset_header(rom_contents, tileset_header_ptr, game='RS'):
    is_compressed = bool(to_int(read_byte_at(rom_contents, tileset_header_ptr)))
    # "SubColorChoose"?
    tileset_type = to_int(read_byte_at(rom_contents, tileset_header_ptr+1))
    # 0000
    tileset_image_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, tileset_header_ptr+4)))
    palettes_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, tileset_header_ptr+8)))
    block_data_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, tileset_header_ptr+12)))
    if game == 'RS':
        behavior_data_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, tileset_header_ptr+16)))
        animation_data_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, tileset_header_ptr+20)))
    elif game == 'FR':
        animation_data_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, tileset_header_ptr+16)))
        behavior_data_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, tileset_header_ptr+20)))
    tileset_header = {
            "is_compressed": is_compressed,
            "tileset_type": tileset_type,
            "tileset_image_ptr": tileset_image_ptr,
            "palettes_ptr": palettes_ptr,
            "block_data_ptr": block_data_ptr,
            "behavior_data_ptr": behavior_data_ptr,
            "animation_data_ptr": animation_data_ptr
        }
    return tileset_header


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


def parse_block_data(rom_contents, tileset_header, game='RS'):
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
    # 2nd byte's final 4 bits is the flip information TODO: More info needed on that
    #     0b0100 = x flip
    img.save("tileset.png", "PNG")
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




