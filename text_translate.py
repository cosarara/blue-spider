#!/usr/bin/env python
# -*- coding: utf-8 -*-

#This file is part of ASC.

#    ASC is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    ASC is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with ASC.  If not, see <http://www.gnu.org/licenses/>.


# Compat. with python 3.2
from __future__ import unicode_literals

import string

with open("pktext.tbl", "r") as table_file:
    table_str = table_file.read().rstrip("\n")
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
    #for i in range(len(string)):
        character = astring[i]
        if character == "\\" and astring[i + 1] == "h":
            #print "case1"
            if (astring[i + 2] in string.hexdigits and
                astring[i + 3] in string.hexdigits):
                trans_string += bytes((int(astring[i+2:i+4], 16),))
                i += 3
        elif character in dictionary:
            #print "case normal"
            trans_string += bytes((dictionary[character],))
        elif astring[i:i + 2] in dictionary:
            #print "case3"
            trans_string += bytes((dictionary[astring[i:i + 2]],))
            i += 1
        else:  # (not tested)
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


#print type(read_table_decode(table)['1B'])
#print ascii_to_hex(u"abcde ", read_table_encode(table))
#print hex_to_ascii("E0D5E0D5E0D5E0D5E0D5E0D5", read_table_decode(table))
