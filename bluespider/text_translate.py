#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#This file is part of Blue Spider

#    Blue Spider is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    Blue Spider is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with Blue Spider.  If not, see <http://www.gnu.org/licenses/>.

import string
import pkgutil
import os
import sys

try:
    if getattr(sys, 'frozen', False):
        datadir = os.path.dirname(sys.executable)
        path = os.path.join(datadir, 'bluespider', 'data', 'pktext.tbl')
        with open(path, "r", encoding="utf8") as file:
            table_str = file.read().rstrip("\n")
    else:
        data = pkgutil.get_data('bluespider', os.path.join('data', 'pktext.tbl'))
        table_str = data.decode("utf8").rstrip("\n")
except Exception as e:
    print(e)
    table_str='FF=$$'
table = table_str

def read_table_encode(table_string=table_str):
    table = table_string.split("\n")
    dictionary = {}
    for line in table:
        line_table = line.split("=")
        dictionary[line_table[1]] = int(line_table[0], 16)
    return dictionary


def read_table_decode(table_string=table_str):
    table = table_string.split("\n")
    dictionary = {}
    for line in table:
        line_table = line.split("=")
        dictionary[int(line_table[0], 16)] = line_table[1]
    return dictionary


def ascii_to_hex(astring, dictionary=read_table_encode(table_str)):
    trans_string = b''
    i = 0
    while i < len(astring):
        character = astring[i]
        if character == "\\" and astring[i + 1] == "h":
            if (astring[i + 2] in string.hexdigits and
                astring[i + 3] in string.hexdigits):
                trans_string += bytes((int(astring[i+2:i+4], 16),))
                i += 3
        elif character in dictionary:
            trans_string += bytes((dictionary[character],))
        elif astring[i:i + 2] in dictionary:
            trans_string += bytes((dictionary[astring[i:i + 2]],))
            i += 1
        else:
            length = 2
            while length < 10:
                if astring[i:i + length] in dictionary:
                    trans_string += bytes((dictionary[astring[i:i + length]],))
                    i += length - 1
                    break
                else:
                    length += 1
        i += 1
    return trans_string


def hex_to_ascii(string, dictionary=read_table_decode(table_str)):
    trans_string = ''
    for i in range(len(string)):
        pos = i
        byte = string[pos]
        if byte in dictionary:
            trans_string += dictionary[byte]
        else:
            trans_string += "\\h" + hex(byte)[2:]
    return trans_string
