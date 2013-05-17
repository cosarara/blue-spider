#!/usr/bin/env python3

# Docs
# ====
# http://datacrystal.romhacking.net/wiki/Pok%C3%A9mon_3rd_Generation#Maps
# Elitemap's PokeRoms.ini
# Elitemap's source code
# http://www.pokecommunity.com/showthread.php?t=156018


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


def main():
    if ((len(sys.argv) < 3) or (sys.argv[2] == "r" and len(sys.argv) < 5)
        or (sys.argv[2] == "w" and len(sys.argv) < 6)):

        print("usage: ./mapped_text.py <rom_filename> <r|w|p> <bank> <map> [file]")
        sys.exit(1)

    file_name = sys.argv[1]
    mode = sys.argv[2]
    #"axve.gba"
    with open(file_name, "rb") as rom_file:
        rom_contents = rom_file.read()
    if mode == 'p':
        if len(sys.argv) == 4:
            banks = get_banks(rom_contents)
            bank_n = int(sys.argv[3])
            get_map_headers(rom_contents, bank_n, banks, echo=True)
        else:
            get_banks(rom_contents, echo=True)
            sys.exit(0)
    elif mode == 'r' or mode == 'w':
        banks = get_banks(rom_contents)
        bank_n = int(sys.argv[3])
        map_n = int(sys.argv[4])
        map_headers = get_map_headers(rom_contents, bank_n, banks)
        map_header_address = map_headers[map_n]
        map_header = parse_map_header(rom_contents, map_header_address)
        map_data_address = map_header['map_data_ptr']
        map_data = parse_map_data(rom_contents, map_data_address)
        tilemap_address = map_data['tilemap_ptr']
        w = map_data['w']
        h = map_data['h']
        if mode == 'r':
            mapmem = rom_contents[tilemap_address:]
            #print(mapmem[:100])
            text_map = map_to_text(mapmem, w, h)
            print(text_map)
        if mode == 'w':
            map_file_name = sys.argv[5]
            with open(map_file_name, "r") as map_text_file:
                map_text = map_text_file.read()
            new_map = text_to_mem(map_text)
            rom_contents = bytearray(rom_contents)
            print("writing from {0} to {1}".format(tilemap_address,
                                                   tilemap_address+len(new_map)))
            print(new_map)
            rom_contents[tilemap_address:
                         tilemap_address+len(new_map)] = new_map
            with open(file_name+'.new.gba', "wb") as rom_file:
                rom_file.write(rom_contents)



if __name__ == '__main__':
    main()








