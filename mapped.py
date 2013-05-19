
import binascii
from map_printer import *
import sys

MapHeaders      = 0x53324
Maps            = 0x5326C
MapLabels       = 0xFBFE0


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

def get_banks(rom_contents, echo=False):
    if echo:
        print("Banks:")
    i = 0
    banks = []
    while True:
        a = get_rom_addr_at(get_rom_addr_at(MapHeaders, rom_contents) + i * 4,
                            rom_contents)
        if a == -1:
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
    maps_of_next_bank = banks[n+1]
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

def parse_map_data(rom_contents, map_data_ptr):
    w = to_int(read_long_at(rom_contents, map_data_ptr))
    h = to_int(read_long_at(rom_contents, map_data_ptr+4))
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
            "tilemap_ptr" : tilemap_ptr,
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










