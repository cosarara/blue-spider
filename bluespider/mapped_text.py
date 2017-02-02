#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# pylint: disable=unused-variable,unused-import

# Docs
# ====
# http://datacrystal.romhacking.net/wiki/Pok%C3%A9mon_3rd_Generation#Maps
# Elitemap's PokeRoms.ini
# Elitemap's source code
# http://www.pokecommunity.com/showthread.php?t=156018

import sys
from . import mapped
from . import structures
from .mapped import bpre, axve, bpee
from .mapped import get_banks, get_map_headers, hexbytes, print32bytes
from .mapped import parse_map_header, parse_map_data, parse_tileset_header
from .mapped import read_rom_addr_at, get_rom_code, get_rom_data
from .map_printer import map_to_text, text_to_mem, print_dict_hex

# TODO: Use a proper arg-parsing library and clean this shit

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

    rom_code = get_rom_code(rom_contents)
    rom_data, game = get_rom_data(rom_code)

    if mode == 'p':
        if len(sys.argv) == 3:
            get_banks(rom_contents, rom_data, echo=True)
            return
        if sys.argv[3] in ("-h", "--help"):
            print("Usage: p [bank [map [command]]]")
            return
        banks = get_banks(rom_contents, rom_data)
        bank_n = int(sys.argv[3], 16)
        if len(sys.argv) == 4:
            get_map_headers(rom_contents, bank_n, banks, echo=True)
            return
        map_header_ptrs = get_map_headers(rom_contents, bank_n, banks)
        map_n = int(sys.argv[4], 16)
        map_header_ptr = map_header_ptrs[map_n]
        map = parse_map_header(rom_contents, map_header_ptr)
        map_data_ptr = map['map_data_ptr']
        map_data = parse_map_data(rom_contents, map_data_ptr)
        if len(sys.argv) == 5:
            print_dict_hex(map)
            print_dict_hex(map_data)
        elif len(sys.argv) >= 6:
            t1_ptr = map_data["global_tileset_ptr"]
            t2_ptr = map_data["local_tileset_ptr"]
            t1 = parse_tileset_header(rom_contents, t1_ptr)
            t2 = parse_tileset_header(rom_contents, t2_ptr)
            # Some aliases and stuff
            from pprint import pprint
            p = print
            pp = pprint
            ph = lambda x: print(hex(x))
            pdh = lambda x: print_dict_hex(x)
            phb = lambda x: print(hexbytes(x))
            rc = bytearray(rom_contents)
            p32b = print32bytes
            raddrat = read_rom_addr_at
            r = lambda rom, start, length: rom[start:start+length]
            for c in sys.argv[5:]:
                eval(c) # Yup! Let the user run whatever the fuck he wants
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
        tilemap_address = mapped.get_rom_addr(tilemap_address)
        if mode == 'r':
            mapmem = rom_contents[tilemap_address:]
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
            with open(file_name, "wb") as rom_file:
                rom_file.write(rom_contents)


if __name__ == '__main__':
    main()

