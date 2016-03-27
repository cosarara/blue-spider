#! /usr/bin/env python
# -*- coding: utf-8 -*-

from . import mapped

"""
To store the variables regarding the current loaded map
"""

class MapData:
    def __init__(self):
        # TODO extract header
        self.header = None
        self.data_header = None

        self.tilemap = None

        self.events_header = None
        self.tilemap_ptr = None

        self.bank_n = None

        self.map_n = None

        self.event_n = None

        #self.events = [[], [], [], []]
        self.events = None

        self.t1_header = None
        self.t2_header = None

    def load(self, game, bank_n, map_n):
        self.bank_n = bank_n
        self.map_n = map_n
        maps = mapped.get_map_headers(game.rom_contents, bank_n, game.banks)
        map_h_ptr = mapped.get_rom_addr(maps[map_n])
        map_header = mapped.parse_map_header(game.rom_contents, map_h_ptr)
        self.header = map_header

        self.data_header = mapped.parse_map_data(
            game.rom_contents, map_header['map_data_ptr'],
            game.name)

        self.t1_header = mapped.parse_tileset_header(
            game.rom_contents,
            self.data_header['global_tileset_ptr'],
            game.name)

        self.t2_header = mapped.parse_tileset_header(
            game.rom_contents,
            self.data_header['local_tileset_ptr'],
            game.name)

        # Every tile is 2 bytes
        map_size = self.data_header['w'] * self.data_header['h'] * 2
        tilemap_ptr = self.data_header['tilemap_ptr']
        tilemap_ptr = mapped.get_rom_addr(tilemap_ptr)
        self.tilemap_ptr = tilemap_ptr
        map_mem = game.rom_contents[tilemap_ptr:tilemap_ptr+map_size]
        if self.data_header['h'] + self.data_header['w'] > 20000:
            #self.ui.statusbar.showMessage("Map bugged (too big)")
            raise Exception("Bad map: h & w way too big")
        self.tilemap = mapped.parse_map_mem(map_mem, self.data_header['h'],
                                            self.data_header['w'])

        self.events_header = mapped.parse_events_header(game.rom_contents,
                                                        self.header['event_data_ptr'])
        self.events = mapped.parse_events(game.rom_contents, self.events_header)

