#! /usr/bin/env python
"""
To organize all info about the game/ROM file in one place
"""

from . import mapped

class Game:
    def __init__(self, fn=None):
        self.rom_contents = None
        self.original_rom_contents = None
        self.rom_file_name = None
        self.rom_code = None
        self.rom_data = None
        self.name = None

        self.banks = None
        self.sprites = None

        if fn is not None:
            self.load_rom(fn)

    def load_rom(self, fn):
        with open(fn, "rb") as rom_file:
            self.rom_contents = rom_file.read()
        self.original_rom_contents = bytes(self.rom_contents)

        self.rom_contents = bytearray(self.rom_contents)
        self.rom_file_name = fn
        self.rom_code = self.rom_contents[0xAC:0xAC+4]
        try:
            self.rom_data, self.name = {
                b'AXVE': (mapped.axve, "RS"),
                b'BPRE': (mapped.bpre, "FR"),
                b'BPEE': (mapped.bpee, "EM"),
            }[bytes(self.rom_code)]
        except KeyError:
            raise Exception("ROM code not found")

        self.sprites = mapped.get_ow_sprites(self.rom_contents, self.rom_data)
        self.banks = mapped.get_banks(self.rom_contents, self.rom_data)

