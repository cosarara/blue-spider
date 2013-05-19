#!/usr/bin/env python3

# Docs
# ====
# http://datacrystal.romhacking.net/wiki/Pok%C3%A9mon_3rd_Generation#Maps
# Elitemap's PokeRoms.ini
# Elitemap's source code
# http://www.pokecommunity.com/showthread.php?t=156018


from mapped import *


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
            tileset1_data = parse_tileset_header(rom_contents, map_data['global_tileset_ptr'])
            block_data_ptr = tileset1_data['block_data_ptr']
            print('tileset1 block data ptr is ', hex(block_data_ptr))
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








