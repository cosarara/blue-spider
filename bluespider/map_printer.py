# -*- coding: utf8 -*-

''' Importing and exporting maps to utf8 '''

chars = ('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOP'
         'QRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
         'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòó'
         'ôõö÷øùúûüýþÿĀāĂăĄąĆćĈĉĊċČčĎďĐđĒēĔĕĖėĘęĚěĜĝĞğĠġĢģĤĥĦħ'
         'ĨĩĪīĬĭĮįİıĲĳĴĵĶķĸĹĺĻļĽľĿŀŁłŃńŅņŇňŉŊŋŌōŎŏŐőŒœŔŕŖŗŘřŚś'
         'ŜŝŞşŠšŢţŤťŦŧŨũŪūŬŭŮůŰűŲųŴŵŶŷŸŹźŻżŽž')
for n in range(700):
    chars += chr(n+300)

def text_to_mem(text):
    text = text.replace(" ", "")
    text_parts = text.split('---')
    text = text_parts[0]
    text2 = text_parts[1]
    lines = text.split('\n')[:-1]
    lines2 = text2.split('\n')[1:-2]
    h = len(lines)
    w = len(lines[0])//2
    print(h, w)
    mem = bytearray(h*w*2)
    i = 0
    for line, line2 in zip(lines, lines2):
        for char, char2 in zip(line, line2):
            num = chars.find(char)
            num2 = chars.find(char2)

            byte1 = (num & 0xFF)
            byte2 = ((num & 0b1100000000) >> 8) | (num2 << 2)
            #print(bin(byte2))
            tile_bytes = bytes((byte1, byte2))
            mem[i:i+2] = tile_bytes
            i += 2
    return mem

def map_to_text(mem, w, h):
    text = ''
    text2 = ''
    i = 0
    for row in range(h):
        line = ''
        line2 = ''
        for tile in range(w):
            # Each tile is 16 bit, 9 bits for tile num. and 7 for attributes
            tbytes = bytearray(mem[i*2:i*2+2])
            char = tbytes[0] | (tbytes[1] & 0b11) << 8
            char2 = (tbytes[1] & 0b11111100) >> 2
            line += chars[char] + ' '
            line2 += chars[char2] + ' '
            i += 1
        text += line + '\n'
        text2 += line2 + '\n'
    text = text + '---\n' + text2
    return text

def print_dict_hex(d):
    for key in sorted(d):
        print("%s: %s" % (key, hex(d[key])))

