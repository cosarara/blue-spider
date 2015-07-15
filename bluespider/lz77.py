# -*- coding: utf8 -*-

to_int = lambda x: int.from_bytes(x, "little")
block_size = 8

def decompress(compressed_data):
    '''Decompresses lz77-compressed images in GBA ROMs.
       Algorithm originally ported from NLZ-Advance code
       (which has copyright by Nintenlord)
       compressed data must be either a bytes() or a bytearray()'''
    size = to_int(compressed_data[1:4])
    decompressed_data = bytearray(size)
    if compressed_data[0] != 0x10:
        raise Exception('Not valid lz77 data')
    decomp_pos = 0
    comp_pos = 4
    while decomp_pos < size:
        # Every bit of this byte maps to one of the eight following blocks
        # if the bit is 1, that block is compressed
        byte = compressed_data[comp_pos]
        are_compressed = [(byte >> 7-i) & 1 for i in range(8)]
        comp_pos += 1
        for block_i, is_compressed in enumerate(are_compressed):
            if is_compressed:
                amount_to_copy = 3 + (compressed_data[comp_pos]>>4)
                to_copy_from = (1 +
                                ((compressed_data[comp_pos] & 0xF) << 8) +
                                compressed_data[comp_pos + 1])
                if to_copy_from > size:
                    raise Exception('Not valid lz77 data')
                tmp_start = decomp_pos
                for i in range(amount_to_copy):
                    if decomp_pos >= size:
                        break
                    decompressed_data[decomp_pos] = decompressed_data[
                        tmp_start - to_copy_from + i
                    ]
                    decomp_pos += 1
                comp_pos += 2

            else:
                if decomp_pos >= size:
                    break
                decompressed_data[decomp_pos] = compressed_data[comp_pos]
                decomp_pos += 1
                comp_pos += 1
            if decomp_pos > size:
                break
    return decompressed_data


if __name__ == "__main__":
    with open("axve.gba", "rb") as file:
        rom = file.read()
    comp_tileset = rom[0xe92118:]
    comp_tileset = rom[0x218684:]
    a = decompress(comp_tileset)
    with open("out.gba", "wb") as file:
        file.write(a)

    #cols = 8*16//2
    #rows = 8*32
    from PIL import Image
    im = Image.new("RGB", (16*8, 400))
    print(len(a))
    tiles_per_line = 16
    for pos in range(len(a)):
        tile = pos // (8*4)
        x = ((pos-(tile*8*4))%4)*2+((tile % tiles_per_line)*8)
        y = (pos-(tile*8*4))//4 + (tile//tiles_per_line*8)

        if pos < len(a):
            color2 = ((a[pos] >> 4) & 0xF)
            color1 = a[pos] & 0xF
        else:
            color1 = 0
            color2 = 0
        #print('-')
        #print("pos", pos)
        #print("x, y", x, y)
        #print("color", color1, color2)
        color1 *= 255//16
        color2 *= 255//16
        color1 = (color1, color1, color1)
        color2 = (color2, color2, color2)
        im.putpixel((x, y), color1)
        im.putpixel((x+1, y), color2)
    im.save("out.png", "PNG")
