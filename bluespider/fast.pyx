
from .mapped import GRAYSCALE

def color(list pals, list t1data, list t2data):
    col1data = []
    col2data = []
    for c in pals:
        colored1 = [c[i] for i in t1data]
        col1data.append(colored1)
        colored2 = [c[i] for i in t2data]
        col2data.append(colored2)
    return col1data, col2data

def build_imgdata(data, size, palette, w):
    if GRAYSCALE:
        palette = GRAYSCALE
    tiles_per_line = w
    imw, imh = size
    imdata = [0]*imw*imh
    for pos in range(len(data)):
        tile = pos // (8*4) # At 2 pixels per byte, we have 8*8/2 bytes per tile
        x = ((pos-(tile*8*4))%4)*2+((tile % tiles_per_line)*8)
        y = (pos-(tile*8*4))//4 + (tile//tiles_per_line*8)

        color2 = ((data[pos] >> 4) & 0xF)
        color1 = data[pos] & 0xF
        color1 = palette[color1]
        color2 = palette[color2]
        imdata[x+y*imw] = color1
        imdata[x+y*imw+1] = color2
    return imdata

try:
    import Image
    import ImageQt
except:
    try:
        from PIL import Image, ImageQt
    except:
        print("Warning: Couldn't import PIL")

TILES_PER_LINE = 16
positions = {
        0: (0,0),
        1: (8,0),
        2: (0,8),
        3: (8,8)
      }

def build_subtile(int byte1, int byte2, list palettes, list imgs, int part):
    cdef int tile_num, palette_num, flips, x, y
    cdef list palette
    cdef tuple pos, t
    tile_num = byte1 | ((byte2 & 0b11) << 8)
    palette_num = byte2 >> 4
    if palette_num > 13: # XXX
        palette_num = 0
    palette = GRAYSCALE or palettes[palette_num]
    img = imgs[palette_num]
    flips = (byte2 & 0xC) >> 2
    x = (tile_num % TILES_PER_LINE) * 8
    y = (tile_num // TILES_PER_LINE) * 8
    pos = (x, y, x+8, y+8)
    part_img = img.crop(pos)
    if flips & 1:
        part_img = part_img.transpose(Image.FLIP_LEFT_RIGHT)
    if flips & 2:
        part_img = part_img.transpose(Image.FLIP_TOP_BOTTOM)
    x, y = positions[part]
    pos = (x, y, x+8, y+8)
    t = palette[0]
    return part_img, t, pos

def build_block_imgs(blocks_mem, imgs, palettes):
    ''' Build images from the block information and tilesets.
     Every block is 16 bytes, and holds down and up parts for a tile,
     composed of 4 subtiles
     every subtile is 2 bytes
    
    [01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16]
       1     2     3     4     5     6     7     8

    Top layer Bottom layer
     1 | 2       5 | 6
     -----       -----
     3 | 4       7 | 8

     1st byte and 2nd byte's last (two?) bit(s) is the tile number
     2nd byte's first 4 bits is the color palette index
     2nd byte's final 4 bits is the flip information... and something else,
     I guess
         0b0100 = x flip
     '''
    # TODO: I think this might be a bit slow in old machines
    cdef list block_imgs
    cdef tuple pos, t
    cdef bytearray layer_mem
    cdef int byte1, byte2, block, layer, part
    block_imgs = []
    base_block_img = Image.new("RGB", (16, 16))
    mask = Image.new("L", (8, 8))
    for block in range(len(blocks_mem)//16):
        block_mem = blocks_mem[block*16:block*16+16]
        # Copying is faster than creating
        block_img = base_block_img.copy()
        # Up/down
        for layer in range(2):
            layer_mem = block_mem[layer*8:layer*8+8]
            for part in range(4):
                d = part*2
                byte1 = layer_mem[d]
                byte2 = layer_mem[d+1]
                part_img, t, pos = build_subtile(byte1, byte2, palettes, imgs, part)
                if layer:
                    img_data = tuple(part_img.getdata())
                    mask_data = [0 if i == t else 255 for i in img_data]
                    mask.putdata(mask_data)
                    block_img.paste(part_img, pos, mask)
                else:
                    block_img.paste(part_img, pos)

        block_imgs.append(block_img)
    return block_imgs

