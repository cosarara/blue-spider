#! /usr/bin/env python
# -*- coding: utf-8 -*-

from . import mapped
from PIL import Image


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
        map_header = mapped.parse_map_header(game, map_h_ptr)
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
        w_tiles = w // 8
        h_tiles = (h1 + h2) // 8
        for img in imgs:
            cropped_img = []
            for i in range(h_tiles):
                for j in range(w_tiles):
                    tile = img.crop((j * 8, i * 8, (j + 1) * 8, (i + 1) * 8))
                    cropped_img.append(tile)
            cropped_imgs.append(cropped_img)

        self.complete_tilesets = imgs
        self.cropped_tileset = cropped_imgs

    def load_tilesets(self, game, previous_map=None):
        do_not_load_1 = False
        if previous_map and previous_map.tileset1.header == self.tileset1.header:
            num_of_blocks = (640, 512)[game.name in ('RS', 'EM')]
            if previous_map.tileset2.header != self.tileset2.header or \
                            num_of_blocks > len(previous_map.blocks.images):
                self.tileset1 = previous_map.tileset1
                self.blocks.set_block_data(previous_map.blocks.blocks[:num_of_blocks])
                self.blocks.set_block_images(previous_map.blocks.images[:num_of_blocks])
                do_not_load_1 = True
            else:
                self.tileset1 = previous_map.tileset1
                self.tileset2 = previous_map.tileset2
                self.complete_tilesets = previous_map.complete_tilesets
                self.cropped_tileset = previous_map.cropped_tileset
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
        behback_data_lenght = (4, 2)[game.name in ('EM', 'RS')]
        for tileset_n in to_load:
            block_img_data, block_behback_data = tileset_n.get_block_data(game.rom_contents, game.name)
            # Half of the time this function runs is spent here
            self.blocks.load(block_img_data, pals, self.cropped_tileset, block_behback_data,
                             behback_data_lenght)

    def update_block_img(self, block_num, layer, tile, tile_num, pal, flip_x, flip_y):
        tileset_num = self.tileset1.block_amount <= block_num
        self.blocks.blocks[block_num][layer][tile] = [tile_num, pal, flip_x, flip_y]
        if not self.blocks.were_modified(tileset_num):
            self.blocks.set_tileset_modified_state(tileset_num, True)

    def update_block_behback(self, block_num, *behback_bytes):
        tileset_num = self.tileset1.block_amount <= block_num
        # behbacks order: behaviour1, background1, behaviour2, background2
        block = self.blocks.blocks[block_num]
        ints = []
        for b in behback_bytes:
            try:
                x = int(b, base=16)
                if x > 0xff:
                    raise Exception('"{}" is not a valid value.\nIt should be '
                                    'smaller than "0xff"'.format(hex(x)))
                ints.append(x)
            except (TypeError, ValueError):
                raise Exception('"{}" is not a valid hex number.'.format(b))

        if len(ints) == 4:
            block.behaviour2 = ints[2]
            block.background2 = ints[3]
        block.behaviour1 = ints[0]
        block.background1 = ints[1]

        if not self.blocks.were_modified(tileset_num):
            self.blocks.set_tileset_modified_state(tileset_num, True)


    def get_block_layers(self, block_num):
        return self.blocks.draw_block_layers(block_num, self.get_palettes(), self.cropped_tileset)

    def save_blocks(self, rom_contents):
        t1_block_amount = self.tileset1.block_amount
        if self.blocks.were_modified(0):
            img_data, behback_data = self.blocks.to_bytes(end_block=t1_block_amount)
            self.tileset1.save_blocks_data(rom_contents, img_data, behback_data)
            self.blocks.set_tileset_modified_state(0, False)
        if self.blocks.were_modified(1):
            img_data, behback_data = self.blocks.to_bytes(start_block=t1_block_amount)
            self.tileset2.save_blocks_data(rom_contents, img_data, behback_data)
            self.blocks.set_tileset_modified_state(1, False)


class TilesetData:
    def __init__(self):
        self.header = None
        self.palettes = None
        self.block_amount = None
        self.behback_data_size = None

    def set_header(self, header):
        self.header = header

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
        behaviour_data_ptr = mapped.get_rom_addr(self.header['behaviour_data_ptr'])
        t_type = self.header['tileset_type']
        if t_type == 0:
            if game == 'RS' or game == 'EM':
                num_of_blocks = 512
            else:
                num_of_blocks = 640
        else:
            num_of_blocks = (behaviour_data_ptr - block_data_ptr) // 16
        length = num_of_blocks * 16
        img_data = rom_contents[block_data_ptr:block_data_ptr + length]
        self.behback_data_size = (4, 2)[game in ('RS', 'EM')]
        behaviour_data = rom_contents[behaviour_data_ptr:behaviour_data_ptr + length * self.behback_data_size]

        self.block_amount = num_of_blocks

        return img_data, behaviour_data

    def save_blocks_data(self, rom_contents, img_data, behback_data):
        img_data_ptr = mapped.get_rom_addr(self.header['block_data_ptr'])
        behback_data_ptr = mapped.get_rom_addr(self.header['behaviour_data_ptr'])
        mapped.write_n_bytes(rom_contents, img_data_ptr, self.block_amount * 16, img_data)
        mapped.write_n_bytes(rom_contents, behback_data_ptr, self.block_amount * self.behback_data_size,
                             behback_data)


class BlocksData:
    # Block loading utilities
    base_block_img = Image.new("RGB", (16, 16))
    mask = Image.new("L", (8, 8))
    POSITIONS = (
        (0, 0),
        (8, 0),
        (0, 8),
        (8, 8)
    )

    def __init__(self):
        self.images = []
        self.images_wide = 16 * 8  # 8 tiles per row
        self.blocks = []

        self.t1_modified = False
        self.t2_modified = False

    def set_tileset_modified_state(self, tileset, bool):
        if tileset:
            self.t2_modified = bool
        else:
            self.t1_modified = bool

    def were_modified(self, tileset):
        if tileset == 0:
            return self.t1_modified
        elif tileset == 1:
            return self.t2_modified
        else:
            return self.t1_modified or self.t2_modified

    def set_block_images(self, images):
        self.images = images

    def set_block_data(self, blocks):
        self.blocks = blocks

    def draw_block_layers(self, block_num, palettes, tiles):
        block = self.blocks[block_num]
        block_img = BlocksData.base_block_img.copy()
        layers = []
        # Up/down
        for i in range(2):
            layer = BlocksData.base_block_img.copy()
            for j in range(4):
                tile_num, pal, flip_x, flip_y = block[i][j]
                try:
                    part_img = tiles[pal][tile_num]
                except IndexError:
                    part_img = tiles[pal][0]
                if flip_x:
                    part_img = part_img.transpose(Image.FLIP_LEFT_RIGHT)
                if flip_y:
                    part_img = part_img.transpose(Image.FLIP_TOP_BOTTOM)
                pal = palettes[pal]
                x, y = BlocksData.POSITIONS[j]
                if i:
                    # Transparency
                    BlocksData.mask.putdata([0 if i == pal[0] else 255 for i in part_img.getdata()])
                    block_img.paste(part_img, (x, y, x + 8, y + 8), BlocksData.mask)
                else:
                    block_img.paste(part_img, (x, y, x + 8, y + 8))
                layer.paste(part_img, (x, y, x + 8, y + 8))
            layers.append(layer)
        self.images[block_num] = block_img
        return layers

    def load(self, img_data, palettes, tiles, behback_data, beback_lenght):
        '''
        Build images from the block information and tilesets.
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
        for i in range(len(img_data) // 16):
            # Copying is faster than creating
            block_img = BlocksData.base_block_img.copy()
            block = Block(img_data[i * 16:i * 16 + 16], *behback_data[i * beback_lenght:(i + 1) * beback_lenght])
            # Up/down
            for j in range(2):
                for k in range(4):
                    tile_num, pal, flip_x, flip_y = block[j][k]
                    try:
                        part_img = tiles[pal][tile_num]
                    except IndexError:
                        part_img = tiles[pal][0]
                    if flip_x:
                        part_img = part_img.transpose(Image.FLIP_LEFT_RIGHT)
                    if flip_y:
                        part_img = part_img.transpose(Image.FLIP_TOP_BOTTOM)
                    pal = palettes[pal]
                    x, y = BlocksData.POSITIONS[k]
                    if j:
                        # Transparency
                        # mask = Image.eval(part_img, lambda a: 255 if a else 0)
                        BlocksData.mask.putdata([0 if i == pal[0] else 255 for i in part_img.getdata()])
                        block_img.paste(part_img, (x, y, x + 8, y + 8), BlocksData.mask)
                    else:
                        block_img.paste(part_img, (x, y, x + 8, y + 8))
            self.blocks.append(block)
            self.images.append(block_img)

    def to_bytes(self, start_block=0, end_block=None):
        if end_block is None:
            end_block = len(self.blocks)
        img_data = behback_data = b''
        for i in range(start_block, end_block):
            block_img, block_beback = self.blocks[i].to_bytes()
            img_data += block_img
            behback_data += block_beback
        return img_data, behback_data


class Block:
    def __init__(self, img_data, beh1, beh2, back2=None, back1=None):
        if back1 is None:
            beh2, back1 = back1, beh2
        self.behaviour1 = beh1
        self.behaviour2 = beh2
        self.background1 = back1
        self.background2 = back2
        # [layer1, layer2]
        layers = []
        for i in range(2):
            # [tile1, tile2, tile3, tile4]
            layer = []
            layer_data = img_data[i * 8:(i + 1) * 8]
            for j in range(4):
                byte1 = layer_data[j * 2]
                byte2 = layer_data[j * 2 + 1]
                tile_num = byte1 | ((byte2 & 0b11) << 8)
                tile_palette = byte2 >> 4
                if tile_palette > 13:
                    tile_palette = 0
                flips = (byte2 >> 2) & 0b11
                flip_x = flips & 1
                flip_y = flips >> 1

                # Each tile is:
                layer.append([tile_num, tile_palette, flip_x, flip_y])
            layers.append(layer)
        self.layers = layers

    def __getitem__(self, item):
        return self.layers[item]

    def to_bytes(self):
        if self.behaviour2 is None:
            behback_data = bytes((self.behaviour1, self.background1))
        else:
            behback_data = bytes((self.behaviour1, self.behaviour2,
                                  self.background2, self.background1))

        img_data = b''
        for layer in self.layers:
            for tile in layer:
                # The first byte are the least significant 8 bits from the tile num
                byte1 = tile[0] & 0xff

                # The remaining 2 bits go to byte 2
                # Then 2 bits for the flips
                # And the most significant 4 bits are for the palette
                byte2 = (tile[0] >> 8) | (tile[2] << 2) | (tile[3] << 3) | (tile[1] << 4)
                img_data += bytes((byte1, byte2))

        return [img_data, behback_data]



