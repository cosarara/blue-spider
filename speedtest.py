#!/usr/bin/env python3
# -*- coding: utf8 -*-
# python speedtest.py ~/RH/tmp/FR.gba 0x82d4bb4 0x82d4c44

from PyQt5 import QtWidgets
from bluespider import mapped, mapped_gui
import sys
import time

PROFILE = True

print("imported things")

app = QtWidgets.QApplication(sys.argv)
print("created stupid app")
window = mapped_gui.Window(no_argv=True)
print("created stupid window")
window.load_rom(sys.argv[1])
print("loaded stupid rom")
print(window.game)
bank_n = int(sys.argv[2])
map_n = int(sys.argv[3])
rom_contents = window.rom_contents
rom_data = window.rom_data
banks = mapped.get_banks(rom_contents, rom_data)
map_header_ptr = mapped.get_map_headers(rom_contents, bank_n, banks)[map_n]
map = mapped.parse_map_header(rom_contents, map_header_ptr)
h = mapped.parse_map_data(rom_contents, map['map_data_ptr'])
t1_header = mapped.parse_tileset_header(
        window.rom_contents,
        h['global_tileset_ptr'],
        #int(sys.argv[2], 16),
        window.game
        )
t2_header = mapped.parse_tileset_header(
        window.rom_contents,
        #int(sys.argv[3], 16),
        h['local_tileset_ptr'],
        window.game
        )
print("parsed stupid headers")
print("running real test now")
x = time.time()
#window.load_tilesets(t1_header, t1_header, t1_imgs=None)
if PROFILE:
   import cProfile
   import re
   cProfile.run('window.get_tilesets(t1_header, t2_header, t1_imgs=None)')
else:
    window.get_tilesets(t1_header, t2_header, t1_imgs=None)
print(time.time() - x)
print("done")


