#!/usr/bin/env python3

# Docs
# ====
# http://datacrystal.romhacking.net/wiki/Pok%C3%A9mon_3rd_Generation#Maps
# Elitemap's PokeRoms.ini
# Elitemap's source code
# http://www.pokecommunity.com/showthread.php?t=156018


import binascii
from map_printer import *

MapHeaders      = 0x53324
Maps            = 0x5326C
MapLabels       = 0xFBFE0

with open("axve.gba", "rb") as rom_file:
    rom_contents = rom_file.read()

def hexbytes(s):
    a = binascii.hexlify(s).decode()
    b = ''
    for i in range(len(s)):
        b += a[i*2:i*2+2] + " "
    b = b.rstrip(" ")
    return b

print32bytes = lambda x : print(hexbytes(rom_contents[x:x+32]))

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

def get_rom_addr_at(x):
    return get_rom_addr(to_int(rom_contents[x:x+4]))

def read_n_bytes(rom, addr, n):
    if addr == -1:
        raise Exception("you are trying to read -1")
    return rom[addr:addr+n]

read_long_at = lambda rom, addr : read_n_bytes(rom, addr, 4)
read_ptr_at = read_long_at
read_short_at = lambda rom, addr : read_n_bytes(rom, addr, 2)
read_byte_at = lambda rom, addr : read_n_bytes(rom, addr, 1)

print(hexbytes(rom_contents[MapHeaders:MapHeaders+32]))
addr = get_addr(rom_contents[MapHeaders:MapHeaders+4])
print("Banks:")
i = 0
banks = []
while True:
    a = get_rom_addr_at(get_rom_addr_at(MapHeaders) + i * 4)
    if a == -1:
        break
    print(hex(i) + "\t" + hex(a))
    banks.append(a)
    i += 1

print(banks)

print("enter a bank num.:")
n = int(input("> "))
print("Maps in bank ", n)
maps_addr = banks[n]
maps_of_next_bank = banks[n+1]
maps = []
i = 0
while True:
    a = get_rom_addr_at(maps_addr + i * 4)
    if a == -1 or maps_addr + i * 4 == maps_of_next_bank:
        break
    print(hex(i) + "\t" + hex(a))
    maps.append(a)
    i += 1

print("enter a map num.:")
n = int(input("> "))
print32bytes(maps[n])
map_h = maps[n]
print("map info:")
map_data_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_h)))
print("\tmap data:", hex(map_data_ptr))
event_data_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_h+4)))
print("\tevent data:", hex(event_data_ptr))
level_script_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_h+8)))
print("\tlevelscript:", hex(level_script_ptr))
connections_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_h+12)))
print("\tconnections:", hex(connections_ptr))
print("\tsong:", hex(to_int(rom_contents[maps[n]+16:maps[n]+18])))
print("\tmap ptr index?:", hex(to_int(rom_contents[maps[n]+18:maps[n]+20])))
print("\tlabel index:", hex(to_int(rom_contents[maps[n]+20:maps[0]+21])))
print("\tis a cave:", hex(to_int(rom_contents[maps[n]+21:maps[n]+22])))
print("\tweather:", hex(to_int(rom_contents[maps[n]+22:maps[n]+23])))
print("\ttype:", hex(to_int(rom_contents[maps[n]+23:maps[n]+24])))
print("\tname of map when entering:", hex(to_int(rom_contents[maps[n]+26:maps[n]+27])))
print("\tcombat type (?):", hex(to_int(rom_contents[maps[n]+27:maps[n]+28])))

w = to_int(read_long_at(rom_contents, map_data_ptr))
h = to_int(read_long_at(rom_contents, map_data_ptr+4))
print("map w", hex(w))
print("map h", hex(h))
border_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_data_ptr+8)))
actual_tilemap_ptr = get_rom_addr(to_int(read_ptr_at(rom_contents, map_data_ptr+12)))
print("pointer to I don't know what about parallelepipeds",
      hex(border_ptr))
print("pointer to tilemap data",
      hex(actual_tilemap_ptr))
print32bytes(actual_tilemap_ptr)

mapmem = rom_contents[actual_tilemap_ptr:]
#w = to_int(rom_contents[map_addr:map_addr+4])
#h = to_int(rom_contents[map_addr+4:map_addr+8])
text_map = map_to_text(mapmem, w, h)
print(text_map)

#text_map_2 = map_to_text(text_to_mem(text_map), w, h)
#print(text_map_2)

#print32bytes(get_rom_addr_at(maps[0]))
#print32bytes(get_rom_addr_at(maps[0] + 4))
#print32bytes(get_rom_addr_at(get_rom_addr_at(maps[0] + 4)))
#print(rom_contents.find(b'\x0C\xB7\x14'))
#print32bytes(rom_contents.find(b'\x0C\xB7\x14'))





