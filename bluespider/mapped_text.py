#!/usr/bin/env python3

# Docs
# ====
# http://datacrystal.romhacking.net/wiki/Pok%C3%A9mon_3rd_Generation#Maps
# Elitemap's PokeRoms.ini
# Elitemap's source code
# http://www.pokecommunity.com/showthread.php?t=156018

import sys
from .mapped import bpre, axve
from .mapped import get_banks, get_map_headers
from .mapped import parse_map_header, parse_map_data
from .map_printer import map_to_text, text_to_mem, print_dict_hex

def main():
    if ((len(sys.argv) < 3) or (sys.argv[2] == "r" and len(sys.argv) < 5)
        or (sys.argv[2] == "w" and len(sys.argv) < 6)):

        print("usage: ./mapped_text.py <rom_filename> <r|w|p> "
              "<bank> <map> [file]")
        sys.exit(1)

    file_name = sys.argv[1]
    mode = sys.argv[2]
    #"axve.gba"
    with open(file_name, "rb") as rom_file:
        rom_contents = rom_file.read()
    rom_code = rom_contents[0xAC:0xAC+4]
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
    if mode == 'p':
        if len(sys.argv) == 4:
            banks = get_banks(rom_contents, rom_data)
            bank_n = int(sys.argv[3], 16)
            get_map_headers(rom_contents, bank_n, banks, echo=True)
        elif len(sys.argv) == 5:
            banks = get_banks(rom_contents, rom_data)
            bank_n = int(sys.argv[3], 16)
            map_header_ptrs = get_map_headers(rom_contents, bank_n, banks)
            map_n = int(sys.argv[4], 16)
            map_header_ptr = map_header_ptrs[map_n]
            map = parse_map_header(rom_contents, map_header_ptr)
            print_dict_hex(map)
        elif len(sys.argv) == 6:
            banks = get_banks(rom_contents, rom_data)
            bank_n = int(sys.argv[3], 16)
            map_header_ptrs = get_map_headers(rom_contents, bank_n, banks)
            map_n = int(sys.argv[4], 16)
            map_header_ptr = map_header_ptrs[map_n]
            map = parse_map_header(rom_contents, map_header_ptr)
            map_data_ptr = map['map_data_ptr']
            map_data = parse_map_data(rom_contents, map_data_ptr)
            t1_ptr = map_data["global_tileset_ptr"]
            t2_ptr = map_data["local_tileset_ptr"]
            t1 = parse_tileset_header(rom_contents, t1_ptr)
            t2 = parse_tileset_header(rom_contents, t2_ptr)
            # Some aliases and stuff
            p = print
            ph = lambda x : print(hexbytes(x))
            rc = rom_contents
            p32b = print32bytes
            gaddrat = get_rom_addr_at
            r = lambda rom, start, length : rom[start:start+length]
            eval(sys.argv[5]) # Yup! Let the user run whatever the fuck he wants
        else:
            get_banks(rom_contents, rom_data, echo=True)
            sys.exit(0)
    elif mode == 'r' or mode == 'w':
        banks = get_banks(rom_contents, rom_data)
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
            #tileset1_data = parse_tileset_header(rom_contents, map_data['global_tileset_ptr'])
            #block_data_ptr = tileset1_data['block_data_ptr']
            #print('tileset1 block data ptr is ', hex(block_data_ptr))
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








