#! /usr/bin/env python
# -*- coding: utf-8 -*-

from . import mapped
from PIL import Image


def decode_block_part(part, layer_mem, palettes, cropped_imgs):
    offset = part*2
    byte1 = layer_mem[offset]
    byte2 = layer_mem[offset+1]
    tile_num = byte1 | ((byte2 & 0b11) << 8)

    palette_num = byte2 >> 4
    if palette_num >= 13: # XXX
        palette_num = 0
    palette = mapped.GRAYSCALE or palettes[palette_num]

    if tile_num >= len(cropped_imgs[0]):
        tile_num = 0
    part_img = cropped_imgs[palette_num][tile_num].copy()
    flips = (byte2 & 0xC) >> 2
    if flips & 1:
        part_img = part_img.transpose(Image.FLIP_LEFT_RIGHT)
    if flips & 2:
        part_img = part_img.transpose(Image.FLIP_TOP_BOTTOM)
    return part_img, palette


def build_block_imgs_(blocks_mem, cropped_imgs, palettes):
    ''' Build images from the block information and tilesets.
     Every block is 16 bytes, and holds down and up parts for a tile,
     composed of 4 subtiles
     every subtile is 2 bytes
     1st byte and 2nd bytes last (two?) bit(s) is the index in the tile img
     2nd byte's first 4 bits is the color palette index
     2nd byte's final 4 bits is the flip information... and something else,
     I guess
         0b0100 = x flip
     '''
    # TODO: Optimize. A lot.
    block_imgs = []
    base_block_img = Image.new("RGB", (16, 16))
    mask = Image.new("L", (8, 8))
    POSITIONS = {
        0: (0, 0),
        1: (8, 0),
        2: (0, 8),
        3: (8, 8)
    }
    for block in range(len(blocks_mem)//16):
        block_mem = blocks_mem[block*16:block*16+16]
        # Copying is faster than creating
        block_img = base_block_img.copy()
        # Up/down
        for layer in range(2):
            layer_mem = block_mem[layer*8:layer*8+8]
            for part in range(4):
                part_img, pal = decode_block_part(part, layer_mem, palettes, cropped_imgs)
                x, y = POSITIONS[part]
                # Transparency
                #mask = Image.eval(part_img, lambda a: 255 if a else 0)
                if layer:
                    mask.putdata([0 if i == pal[0] else 255 for i in part_img.getdata()])
                    block_img.paste(part_img, (x, y, x+8, y+8))#, mask)
                else:
                    block_img.paste(part_img, (x, y, x+8, y+8))

        block_imgs.append(block_img)
    return block_imgs

try:
    from .fast import build_block_imgs
except ImportError:
    # print("Using slow build_block_imgs function")
    build_block_imgs = build_block_imgs_

"""
# To store the variables regarding the current loaded map
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

        # self.events = [[], [], [], []]
        self.events = None

        self.tileset1 = TilesetData()
        self.tileset2 = TilesetData()
        self.complete_tilesets = None
        self.cropped_tileset = None

        self.blocks = BlocksData()

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

        self.tileset1.set_header(mapped.parse_tileset_header(
            game.rom_contents,
            self.data_header['global_tileset_ptr'],
            game.name))

        self.tileset2.set_header(mapped.parse_tileset_header(
            game.rom_contents,
            self.data_header['local_tileset_ptr'],
            game.name))

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

    def get_palettes(self):
        return self.tileset1.palettes + self.tileset2.palettes

    def load_tileset_images(self, rom_contents):
        pals = self.get_palettes()
        imgs = []
        t1data, w, h1 = mapped.get_tileset_imgdata(rom_contents, self.tileset1.header)
        t2data, _, h2 = mapped.get_tileset_imgdata(rom_contents, self.tileset2.header)
        img1 = Image.new("RGB", (w, h1))
        img2 = Image.new("RGB", (w, h2))
        big_img = Image.new("RGB", (w, h1 + h2))
        pos1 = (0, 0, w, h1)
        pos2 = (0, h1, w, h1 + h2)
        col1data = mapped.color(pals, t1data)
        col2data = mapped.color(pals, t2data)

        # TODO: Make this in just one loop
        for i in range(len(pals)):
            colored1 = col1data[i]
            colored2 = col2data[i]
            img1.putdata(colored1)
            img2.putdata(colored2)
            colored_img = big_img.copy()
            colored_img.paste(img1, pos1)
            colored_img.paste(img2, pos2)
            imgs.append(colored_img)

        cropped_imgs = []
        # t1_imgs = []
        # t2_imgs = []
        w_tiles = w // 8
        # h_t1_tiles = h1 // 8
        h_tiles = (h1 + h2) // 8
        for img in imgs:
            cropped_img = []
            # t1_tiles = []
            # t2_tiles = []
            for i in range(h_tiles):
                for j in range(w_tiles):
                    tile = img.crop((j * 8, i * 8, (j + 1) * 8, (i + 1) * 8))
                    # if i < h_t1_tiles:
                        # t1_tiles.append(tile)
                    # else:
                        # t2_tiles.append(tile)
                    cropped_img.append(tile)
            cropped_imgs.append(cropped_img)
            # t1_imgs.append(t1_tiles)
            # t2_imgs.append(t2_tiles)

        self.complete_tilesets = imgs
        self.cropped_tileset = cropped_imgs
        # self.tileset1.set_tiles(t1_imgs)
        # self.tileset2.set_tiles(t2_imgs)

    def load_tilesets(self, game, previous_map=None):
        do_not_load_1 = False
        if previous_map and previous_map.tileset1.header == self.tileset1.header:
            num_of_blocks = (640, 512)[game.name in ('RS', 'EM')]
            if previous_map.tileset2.header != self.tileset2.header or \
                            num_of_blocks > len(previous_map.blocks.images):
                self.blocks.set_block_images(previous_map.blocks.images[:num_of_blocks])
                do_not_load_1 = True
            else:
                self.blocks = previous_map.blocks
                return

        self.tileset1.load_palettes(game)
        self.tileset2.load_palettes(game)

        # Half of the time this function runs is spent here
        self.load_tileset_images(game.rom_contents)

        if do_not_load_1:
            to_load = (self.tileset2,)
        else:
            to_load = (self.tileset1, self.tileset2)
        pals = self.get_palettes()
        for tileset_n in to_load:
            block_data_mem = tileset_n.get_block_data(game.rom_contents, game.name)
            # Half of the time this function runs is spent here
            self.blocks.load(block_data_mem, pals, self.cropped_tileset)


class TilesetData:
    def __init__(self):
        self.header = None
        self.palettes = None
        # self.tiles = None

    def set_header(self, header):
        self.header = header

    # def set_tiles(self, tiles):
        # self.tiles = tiles

    def load_palettes(self, game):
        pals_ptr = mapped.get_rom_addr(self.header["palettes_ptr"])

        # Emerald and ruby have 6 palettes for tileset 1 and 7 for tileset 2
        # Fire red is the opposite
        num_of_pals = (7, 6)[(game.name in ('RS', 'EM')) ^ self.header['tileset_type']]
        pals = []
        for pal_n in range(num_of_pals):
            # I really have no clue of why tileset 2 palettes are shifted but...
            # It works!
            palette = mapped.get_pal_colors(game.rom_contents, pals_ptr,
                                            pal_n if not self.header['tileset_type'] else pal_n + 13 - num_of_pals)
            pals.append(palette)
        self.palettes = pals

    def get_block_data(self, rom_contents, game):
        block_data_ptr = mapped.get_rom_addr(self.header['block_data_ptr'])
        t_type = self.header['tileset_type']
        if t_type == 0:
            if game == 'RS' or game == 'EM':
                num_of_blocks = 512
            else:
                num_of_blocks = 640
        else:
            behavior_data_ptr = mapped.get_rom_addr(self.header['behavior_data_ptr'])
            num_of_blocks = (behavior_data_ptr - block_data_ptr) // 16
        length = num_of_blocks * 16
        mem = rom_contents[block_data_ptr:block_data_ptr + length]
        return mem


def decode_block(data):
    # [layer1, layer2]
    block = []
    for i in range(2):
        # [tile1, tile2, tile3, tile4]
        layer = []
        layer_data = data[i * 8:(i + 1) * 8]
        for j in range(4):
            byte1 = layer_data[j * 2]
            byte2 = layer_data[j * 2 + 1]
            tile_num = byte1 | ((byte2 & 0b11) << 8)
            tile_palette = byte2 >> 4
            if tile_palette > 13:
                tile_palette = 0
            flips = (byte2 & 0xC) >> 2
            flip_x = flips & 1
            flip_y = flips & 2

            # Each tile is:
            layer.append([tile_num, tile_palette, flip_x, flip_y])
        block.append(layer)
    return block

class BlocksData:
    def __init__(self):
        self.images = []
        self.images_wide = 16 * 8  # 8 tiles per row

    def set_block_images(self, images):
        self.images = images

    def load(self, blocks_data, palettes, tiles):
        ''' Build images from the block information and tilesets.
             Every block is 16 bytes, and holds down and up parts for a tile,
             composed of 4 subtiles
             every subtile is 2 bytes
             1st byte and 2nd bytes last (two?) bit(s) is the index in the tile img
             2nd byte's first 4 bits is the color palette index
             2nd byte's final 4 bits is the flip information... and something else,
             I guess
                 0b0100 = x flip
             '''
        # TODO: Optimize. A lot.
        block_imgs = []
        base_block_img = Image.new("RGB", (16, 16))
        mask = Image.new("L", (8, 8))
        tiles_length = len(tiles[0])
        POSITIONS = (
            (0, 0),
            (8, 0),
            (0, 8),
            (8, 8)
        )
        for i in range(len(blocks_data) // 16):
            block_data = blocks_data[i * 16:i * 16 + 16]
            # Copying is faster than creating
            block_img = base_block_img.copy()
            block = decode_block(block_data)
            # Up/down
            for j in range(2):
                for k in range(4):
                    tile_num, pal, flip_x, flip_y = block[j][k]
                    if tile_num >= tiles_length:
                        tile_num = 0
                    part_img = tiles[pal][tile_num].copy()
                    if flip_x:
                        part_img = part_img.transpose(Image.FLIP_LEFT_RIGHT)
                    if flip_y:
                        part_img = part_img.transpose(Image.FLIP_TOP_BOTTOM)
                    pal = palettes[pal]
                    x, y = POSITIONS[k]
                    # Transparency
                    # mask = Image.eval(part_img, lambda a: 255 if a else 0)
                    if j:
                        mask.putdata([0 if i == pal[0] else 255 for i in part_img.getdata()])
                        block_img.paste(part_img, (x, y, x + 8, y + 8), mask)
                    else:
                        block_img.paste(part_img, (x, y, x + 8, y + 8))

            block_imgs.append(block_img)
        self.images += block_imgs


class Block:
    def __init__(self, data):
        # [layer1, layer2]
        self.data = []
        for i in range(2):
            # [tile1, tile2, tile3, tile4]
            tiles = []
            layer_data = data[i * 8:(i + 1) * 8]
            for j in range(4):
                byte1 = layer_data[j * 2]
                byte2 = layer_data[j * 2 + 1]
                tile_num = byte1 | ((byte2 & 0b11) << 8)
                tile_palette = byte2 >> 4
                if tile_palette > 13:
                    tile_palette = 0
                flips = (byte2 & 0xC) >> 2
                flip_x = flips & 1
                flip_y = flips & 2
                tiles.append([tile_num, tile_palette, flip_x, flip_y])


    def to_bytes(self):
        pass


def decode_block_part(part, layer_mem, palettes, cropped_imgs):
    offset = part*2
    byte1 = layer_mem[offset]
    byte2 = layer_mem[offset+1]
    tile_num = byte1 | ((byte2 & 0b11) << 8)

    palette_num = byte2 >> 4
    if palette_num >= 13: # XXX
        palette_num = 0
    palette = mapped.GRAYSCALE or palettes[palette_num]

    if tile_num >= len(cropped_imgs[0]):
        tile_num = 0
    part_img = cropped_imgs[palette_num][tile_num].copy()
    flips = (byte2 & 0xC) >> 2
    if flips & 1:
        part_img = part_img.transpose(Image.FLIP_LEFT_RIGHT)
    if flips & 2:
        part_img = part_img.transpose(Image.FLIP_TOP_BOTTOM)
    return part_img, palette
