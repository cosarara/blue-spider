#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
To store the variables regarding the current loaded map
"""

class MapData:
    def __init__(self):
        # TODO extract header
        self.header = None
        self.data_header = None

        self.events_header = None
        self.tilemap_ptr = None

        self.bank_n = None

        self.map_n = None

        self.event_n = None

        #self.events = [[], [], [], []]
        self.events = None

        self.t1_header = None
        self.t2_header = None

