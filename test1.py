
"""Reads data from ROM and builds an image map, just like the UI would.
To easely profile mapped.py"""
import mapped
try:
    from PIL import Image
except:
    import Image

game = 'RS'
rom_file = open("testruby.gba", "rb")
rom_contents = rom_file.read()
rom_file.close()

map_n = 0
bank_n = 0

def load_tileset(tileset_header, previous_img=None):
    tileset_img = mapped.get_tileset_img(rom_contents, tileset_header)
    if previous_img:
        w = previous_img.size[0]
        h = previous_img.size[1] + tileset_img.size[1]
        big_img = Image.new("RGB", (w, h))
        pos = (0, 0, previous_img.size[0], previous_img.size[1])
        big_img.paste(previous_img, pos)
        x = 0
        y = previous_img.size[1]
        x2 = x + tileset_img.size[0]
        y2 = y + tileset_img.size[1]
        pos = (x, y, x2, y2)
        big_img.paste(tileset_img, pos)
        tileset_img = big_img
    block_data_mem = mapped.get_block_data(rom_contents,
                                           tileset_header, game)
    blocks_imgs = mapped.build_block_imgs(block_data_mem, tileset_img)
    blocks_imgs += blocks_imgs
    return tileset_img

banks = mapped.get_banks(rom_contents)
maps = mapped.get_map_headers(rom_contents, bank_n, banks)
map_h_ptr = maps[map_n]
map_header = mapped.parse_map_header(rom_contents, map_h_ptr)
map_data_header = mapped.parse_map_data(
    rom_contents, map_header['map_data_ptr'],
    game
    )

blocks_imgs = []

tileset_header = mapped.parse_tileset_header(
    rom_contents,
    map_data_header['global_tileset_ptr'],
    game
    )
tileset2_header = mapped.parse_tileset_header(
    rom_contents,
    map_data_header['local_tileset_ptr'],
    game
    )
t1_img = load_tileset(tileset_header)
load_tileset(tileset2_header, t1_img)

mov_perms_imgs = mapped.get_imgs()
events_header = mapped.parse_events_header(rom_contents,
    map_header['event_data_ptr'])
print(events_header)
events = mapped.parse_events(rom_contents, events_header)

map_size = map_data_header['w'] * map_data_header['h'] * 2 # Every tile is 2 bytes
tilemap_ptr = map_data_header['tilemap_ptr']
map_mem = rom_contents[tilemap_ptr:tilemap_ptr+map_size]
map = mapped.parse_map_mem(map_mem, map_data_header['w'], map_data_header['h'])

