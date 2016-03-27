#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Blue Spider UI's code. In real need of refactoring, but seems to work. """

# If I keep trying, this code will end up looking as messy as elite map's!

import os
import sys
import time
import pkgutil

from PyQt5 import QtCore, QtGui, QtWidgets
try:
    import Image
    import ImageQt
except ImportError:
    from PIL import Image, ImageQt

from .window import Ui_MainWindow
from . import qmapview
from . import mapped
from . import structures
from . import structure_utils
from . import gui_connections
from . import map_printer
from . import game
from . import mapdata

import appdirs

debug_mode = False
def debug(*args):
    if debug_mode:
        print(*args)

sfn = "settings.txt"
path = appdirs.user_data_dir("bluespider", "cosarara97")
if not os.path.exists(path):
    os.makedirs(path)
settings_path = os.path.join(path, sfn)

class Window(QtWidgets.QMainWindow):
    """ This class is the mother of everything in the GUI """
    def __init__(self, parent=None, no_argv=False):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()

        self.ui.setupUi(self)
        # CX_Freeze
        if getattr(sys, 'frozen', False):
            iconpath = os.path.join(
                os.path.dirname(sys.executable),
                "bluespider", "data", "icon.svg")
            pixmap = QtGui.QPixmap(iconpath)
        else:
            icon = pkgutil.get_data('bluespider',
                                    os.path.join('data', 'icon.svg'))
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(icon)
        icon = QtGui.QIcon()
        icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        self.tree_model = QtGui.QStandardItemModel()
        self.ui.treeView.setModel(self.tree_model)

        self.ui.map_scene = QtWidgets.QGraphicsScene()
        self.ui.map.setScene(self.ui.map_scene)
        self.ui.mov_scene = QtWidgets.QGraphicsScene()
        self.ui.movPermissionsMap.setScene(self.ui.mov_scene)
        self.ui.event_scene = QtWidgets.QGraphicsScene()
        self.ui.eventMap.setScene(self.ui.event_scene)
        self.ui.palette_scene = QtWidgets.QGraphicsScene()
        self.ui.palette.setScene(self.ui.palette_scene)
        self.ui.perms_palette_scene = QtWidgets.QGraphicsScene()
        self.ui.MovPermissionsPalette.setScene(self.ui.perms_palette_scene)
        self.ui.sprite_scene = QtWidgets.QGraphicsScene()
        self.ui.sprite_scene.setSceneRect(QtCore.QRectF(0, 0, 16, 32))
        self.ui.spriteImg.setScene(self.ui.sprite_scene)

        self.game = game.Game()
        self.map_data = mapdata.MapData()

        #self.map_data.t1_header = None
        self.t1_imgs = None
        self.t1_img_qt = None
        #self.map_data.t2_header = None

        #self.map_data = None
        #self.map_data.events_header = None
        self.mapPixMap = None
        self.spritePixMap = None
        self.tilesetPixMap = None
        self.eventPixMap = None
        self.movPixMap = None
        self.permsPalPixMap = None
        self.map_img_qt = None
        self.mov_img_qt = None
        self.event_img_qt = None
        #self.map_data.tilemap_ptr = None
        #self.map_data.map_n = None
        self.map_img = None

        self.blocks_img_w = None
        self.blocks_imgs = None

        #self.game.sprites = []
        #self.map_data.events = [[], [], [], []]

        # needed lambda,
        # not directly load_rom because that would give Qt stuff as a parameter
        self.ui.actionLoad_ROM.triggered.connect(lambda: self.load_rom())
        self.ui.actionSave.triggered.connect(self.write_to_file)
        self.ui.actionSave_As.triggered.connect(self.save_as)
        self.ui.actionExport_Map.triggered.connect(self.export_map)
        self.ui.actionImport_Map.triggered.connect(self.import_map)
        self.ui.actionAdd_new_banks.triggered.connect(self.add_new_banks)
        self.ui.treeView.clicked.connect(self.load_map_qindex)
        self.ui.s_type.currentIndexChanged.connect(
            self.update_signpost_stacked)
        self.ui.p_edit_script.clicked.connect(self.launch_script_editor)
        self.ui.s_edit_script.clicked.connect(self.launch_script_editor)
        self.ui.t_edit_script.clicked.connect(self.launch_script_editor)

        self.ui.actionChoose_script_editor.triggered.connect(
            self.select_script_editor)

        self.ui.openInEmulatorButton.clicked.connect(self.open_warp_in_emulator)
        self.ui.warpGoToMapButton.clicked.connect(self.go_to_warp)

        self.ui.addLevelScriptButton.clicked.connect(self.add_level_script)

        self.selected_tile = 0
        self.hovered_tile = None
        self.selected_mov_tile = 0
        self.selected_event = None
        self.selected_event_type = None
        #self.game.rom_file_name = None
        # RS or FR
        #self.game = None
        #self.game.rom_code = None
        #self.game.rom_data = None
        base = ''
        usepackagedata = True
        if getattr(sys, 'frozen', False):
            base = os.path.join(os.path.dirname(sys.executable), "bluespider")
            usepackagedata = False
        self.mov_perms_imgs = mapped.get_imgs([base, "data", "mov_perms"],
                                              0x40, usepackagedata)


        self.loaded_map = False

        self.ui_event_connections = gui_connections.get_event_connections(
            self.ui)
        self.update_header, self.save_header = (gui_connections.
                                                make_header_connections(self))

        self.ui.addWarpButton.clicked.connect(self.add_warp)
        self.ui.remWarpButton.clicked.connect(self.rem_warp)
        self.ui.addPersonButton.clicked.connect(self.add_person)
        self.ui.remPersonButton.clicked.connect(self.rem_person)
        self.ui.addTriggerButton.clicked.connect(self.add_trigger)
        self.ui.remTriggerButton.clicked.connect(self.rem_trigger)
        self.ui.addSignpostButton.clicked.connect(self.add_signpost)
        self.ui.remSignpostButton.clicked.connect(self.rem_signpost)

        self.ui.rmEventButton.clicked.connect(self.rem_this_event)

        self.loading_started = None

        self.reload_lock = 0
        redrawing_items = (
            self.ui.w_x, self.ui.w_y,
            self.ui.p_x, self.ui.p_y,
            self.ui.t_x, self.ui.t_y,
            self.ui.s_x, self.ui.s_y)
        for item in redrawing_items:
            item.textChanged.connect(self.redraw_events)
        self.ui.sprite_num.valueChanged.connect(self.reload_person_img)
        self.ui.eventSpinBox.valueChanged.connect(self.event_spinbox_changed)
        self.ui.eventSelectorCombo.currentIndexChanged.connect(
            self.update_event_spinbox_max_value)

        self.current_index = None # Tree selector index
        #self.map_data.event_n = None

        self.script_editor_command = ''
        self.isxse = False
        self.load_settings()

        if len(sys.argv) >= 2 and not no_argv:
            self.load_rom(sys.argv[1])
        if len(sys.argv) >= 4 and not no_argv:
            self.load_map(int(sys.argv[2]), int(sys.argv[3]))

    def redraw_events(self):
        """ Called when some event's position is changed in the GUI """
        if self.reload_lock:
            return
        self.save_event_to_memory()
        self.load_map_qindex(self.current_index)
        index = ["person", "warp",
                 "trigger", "signpost"].index(self.selected_event_type)
        self.selected_event = self.map_data.events[index][self.map_data.event_n]

    def reload_person_img(self):
        """ Called when the sprite num. is changed in the GUI """
        if self.reload_lock:
            return
        self.save_event_to_memory()
        self.update_event_editor()


    def load_rom(self, fn=None):
        """ If no filename is given, it'll prompt the user with a nice dialog """
        if fn is None:
            fn, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open ROM file',
                                                          QtCore.QDir.homePath(),
                                                          "GBA ROM (*.gba);;"
                                                          "All files (*)")
        if not fn:
            return

        self.tree_model.clear()
        self.loaded_map = None
        self.game.load_rom(fn)
        self.load_banks()

    def write_rom(self):
        ''' The file might have changed while we were editing, so
        we reload it and apply the modifications to it. '''
        self.ui.statusbar.showMessage("Saving...")
        if not self.game.rom_file_name:
            QtWidgets.QMessageBox.critical(self, "ERROR!", "No ROM loaded!")
            return
        try:
            with open(self.game.rom_file_name, "rb") as rom_file:
                actual_rom_contents = bytearray(rom_file.read())
        except FileNotFoundError:
            with open(self.game.rom_file_name, "wb") as rom_file:
                rom_file.write(self.game.rom_contents)
            return

        self.ui.statusbar.showMessage("Saving... Diffing/Patching...")
        if self.game.rom_contents == self.game.original_rom_contents:
            self.ui.statusbar.showMessage("Nothing to save")
            return

        for i in range(len(self.game.rom_contents)):
            if self.game.rom_contents[i] != self.game.original_rom_contents[i]:
                actual_rom_contents[i] = self.game.rom_contents[i]

        self.ui.statusbar.showMessage("Saving... Writing...")
        with open(self.game.rom_file_name, "wb") as rom_file:
            rom_file.write(actual_rom_contents)
        self.ui.statusbar.showMessage("Saved {}".format(self.game.rom_file_name))

    def load_banks(self):
        self.tree_model.clear()
        self.game.banks = mapped.get_banks(self.game.rom_contents, self.game.rom_data)
        map_labels = mapped.get_map_labels(self.game.rom_contents,
                                           self.game.rom_data, self.game.name)
        for i, bank in enumerate(self.game.banks):
            self.tree_model.appendRow(
                QtGui.QStandardItem(hex(i) + " - " + hex(bank)))
            self.load_maps(i, map_labels)

    def load_maps(self, bank_num, map_labels):
        """ Loads the map list """
        map_header_ptrs = mapped.get_map_headers(self.game.rom_contents,
                                                 bank_num, self.game.banks)

        for i, ptr in enumerate(map_header_ptrs):
            map = mapped.parse_map_header(self.game.rom_contents, ptr)
            index = map['label_index']
            if self.game.name == 'FR':
                index -= 88 # Magic!
            if index >= len(map_labels):
                continue
            label = map_labels[index]
            self.tree_model.item(bank_num).appendRow(
                QtGui.QStandardItem("%s - %s" % (i, label)))

    def get_tilesets(self, t1_header, t2_header, t1_imgs=None,
                     previous_map_data=None):
        do_not_load_1 = False
        if previous_map_data and previous_map_data.t1_header == t1_header:
            if previous_map_data.t2_header == t2_header and t1_imgs:
                return t1_imgs

            num_of_blocks = 640
            if self.game.name == 'RS' or self.game.name == 'EM':
                num_of_blocks = 512
            self.blocks_imgs = self.blocks_imgs[:num_of_blocks]
            do_not_load_1 = True

        else:
            self.blocks_imgs = []
            t1_imgs = None

        pals1_ptr = mapped.get_rom_addr(t1_header["palettes_ptr"])
        pals2_ptr = mapped.get_rom_addr(t2_header["palettes_ptr"])
        pals = mapped.get_pals(self.game.rom_contents, self.game.name,
                               pals1_ptr, pals2_ptr)
        # Half of the time this function runs is spent here
        imgs = mapped.load_tilesets(self.game.rom_contents, self.game.name,
                                    t1_header, t2_header, pals)
        if do_not_load_1:
            to_load = (t2_header,)
        else:
            to_load = (t1_header, t2_header)
        for tileset_header in to_load:
            block_data_mem = mapped.get_block_data(self.game.rom_contents,
                                                   tileset_header, self.game.name)
            # Half of the time this function runs is spent here
            blocks_imgs = mapped.build_block_imgs(block_data_mem, imgs, pals)
            self.blocks_imgs += blocks_imgs

        return imgs


    def draw_palette(self):
        """ Draws the tile palette (not the colors but the selectable tiles) """
        blocks_imgs = self.blocks_imgs
        perms_imgs = self.mov_perms_imgs
        self.blocks_img_w = 16 * 8 # 8 tiles per row
        perms_img_w = self.blocks_img_w
        blocks_img_h = (len(blocks_imgs) * 16) // 8
        perms_img_h = (len(perms_imgs) * 16) // 8
        blocks_img = Image.new("RGB", (self.blocks_img_w, blocks_img_h))
        perms_img = Image.new("RGB", (perms_img_w, perms_img_h))
        i = 0
        for row in range(blocks_img_h // 16):
            for col in range(self.blocks_img_w // 16):
                x = col*16
                y = row*16
                x2 = x+16
                y2 = y+16
                pos = (x, y, x2, y2)
                blocks_img.paste(blocks_imgs[i], pos)
                i += 1

        i = 0
        for row in range(perms_img_h // 16):
            for col in range(perms_img_w // 16):
                x = col*16
                y = row*16
                x2 = x+16
                y2 = y+16
                pos = (x, y, x2, y2)
                perms_img.paste(perms_imgs[i], pos)
                i += 1

        self.t1_img_qt = ImageQt.ImageQt(blocks_img)
        self.perms_pal_img_qt = ImageQt.ImageQt(perms_img)

        # Palette is not draw yet at this point, draw palette has to be called too

    def print_palette(self, quick=False):
        if not quick:
            self.draw_palette()
        self.tilesetPixMap = QtGui.QPixmap.fromImage(self.t1_img_qt)
        self.permsPalPixMap = QtGui.QPixmap.fromImage(self.perms_pal_img_qt)

        self.ui.palette_scene.clear()
        self.ui.perms_palette_scene.clear()
        self.palette_pixmap_qobject = qmapview.QMapPixmap(self.tilesetPixMap)
        self.perms_palette_pixmap_qobject = qmapview.QMapPixmap(
            self.permsPalPixMap)
        self.ui.palette_scene.addItem(self.palette_pixmap_qobject)
        self.ui.perms_palette_scene.addItem(self.perms_palette_pixmap_qobject)
        self.ui.palette_scene.update()
        self.ui.perms_palette_scene.update()
        self.palette_pixmap_qobject.clicked.connect(self.palette_clicked)
        self.perms_palette_pixmap_qobject.clicked.connect(
            self.perms_palette_clicked)

        square_painter = QtGui.QPainter(self.tilesetPixMap)
        square_painter.setPen(QtCore.Qt.red)
        p = self.selected_tile
        w = self.blocks_img_w // 16
        x = (p%w)*16
        y = (p//w)*16
        square_painter.drawRect(x, y, 16, 16)
        square_painter.end()

    def draw_map(self, map):
        w = len(map[0])
        h = len(map)
        map_img = Image.new("RGB", (w*16, h*16))
        mov_img = Image.new("RGB", (w*16, h*16))
        for row in range(h):
            for tile in range(w):
                tile_num, behavior = map[row][tile]
                x = tile*16
                y = row*16
                x2 = x+16
                y2 = y+16
                pos = (x, y, x2, y2)
                if tile_num < len(self.blocks_imgs):
                    map_img.paste(self.blocks_imgs[tile_num], pos)
                    mov_img.paste(self.blocks_imgs[tile_num], pos)
                if behavior < len(self.mov_perms_imgs):
                    mov_img.paste(self.mov_perms_imgs[behavior], pos,
                                  self.mov_perms_imgs[behavior])

        self.map_img = map_img
        self.map_img_qt = ImageQt.ImageQt(map_img)
        self.mov_img_qt = ImageQt.ImageQt(mov_img)

    def print_map(self, map, quick=False):
        if not quick:
            self.draw_map(map)
        self.mapPixMap = QtGui.QPixmap.fromImage(self.map_img_qt)
        self.movPixMap = QtGui.QPixmap.fromImage(self.mov_img_qt)
        self.ui.map_scene.clear()
        self.ui.mov_scene.clear()
        self.map_pixmap_qobject = qmapview.QMapPixmap(self.mapPixMap)
        self.mov_pixmap_qobject = qmapview.QMapPixmap(self.movPixMap)
        self.ui.map_scene.addItem(self.map_pixmap_qobject)
        self.ui.mov_scene.addItem(self.mov_pixmap_qobject)
        self.ui.map_scene.update()
        self.ui.mov_scene.update()

        self.map_pixmap_qobject.clicked.connect(self.map_clicked)
        self.mov_pixmap_qobject.clicked.connect(self.mov_clicked)

        if self.hovered_tile is not None:
            square_painter = QtGui.QPainter(self.tilesetPixMap)
            square_painter.setPen(QtCore.Qt.red)
            p = self.selected_tile
            w = self.blocks_img_w // 16
            x = (p%w)*16
            y = (p//w)*16
            square_painter.drawRect(x, y, 16, 16)
            square_painter.end()

    def draw_events(self, events=None):
        if events is None:
            events = self.map_data.events
        event_img = self.map_img.copy()
        person_events, warp_events, trigger_events, signpost_events = events
        base = ''
        usepackagedata = True
        if getattr(sys, 'frozen', False):
            base = os.path.join(os.path.dirname(sys.executable), "bluespider")
            usepackagedata = False
        event_imgs = mapped.get_imgs([base, "data", "events"], 4,
                                     usepackagedata)
        person_img, warp_img, trigger_img, signpost_img = event_imgs
        event_types = (
            (person_events, person_img),
            (warp_events, warp_img),
            (trigger_events, trigger_img),
            (signpost_events, signpost_img))
        for event_type in event_types:
            data, img = event_type
            for event in data:
                if not event: # Some events aren't parsed yet
                    continue
                x = event['x']
                if x == 0xFFFF:
                    x = 0
                y = event['y']
                if y == 0xFFFF:
                    y = 0
                x = x*16
                y = y*16
                x2 = x+16
                y2 = y+16
                pos = (x, y, x2, y2)
                event_img.paste(img, pos, img)
        self.event_img_qt = ImageQt.ImageQt(event_img)
        self.eventPixMap = QtGui.QPixmap.fromImage(self.event_img_qt)
        self.ui.event_scene.clear()
        self.event_pixmap_qobject = qmapview.QMapPixmap(self.eventPixMap)
        self.ui.event_scene.addItem(self.event_pixmap_qobject)
        self.ui.event_scene.update()
        self.event_pixmap_qobject.clicked.connect(self.event_clicked)

    def load_events(self):
        events_header = self.map_data.events_header
        self.ui.num_of_warps.setText(str(events_header['n_of_warps']))
        self.ui.num_of_people.setText(str(events_header['n_of_people']))
        self.ui.num_of_triggers.setText(str(events_header['n_of_triggers']))
        self.ui.num_of_signposts.setText(str(events_header['n_of_signposts']))

    def load_map_qindex(self, qindex):
        self.current_index = qindex
        bank_n = qindex.parent().row()
        if bank_n == -1:
            return
        map_n = qindex.row()
        self.load_map(bank_n, map_n)

    def load_map(self, bank_n, map_n):
        """ Called when a map is selected, a warp is clicked or the map has
            to be reloaded. """
        self.loading_started = time.time()
        self.ui.statusbar.showMessage("Loading map...")
        if self.loaded_map:
            self.save_map()
            self.save_events()

        debug(bank_n, map_n)
        previous_map_data = self.map_data
        self.map_data = mapdata.MapData()
        self.map_data.load(self.game, bank_n, map_n)

        self.load_level_scripts()
        try:
            self.t1_imgs = self.get_tilesets(self.map_data.t1_header,
                                             self.map_data.t2_header,
                                             self.t1_imgs,
                                             previous_map_data)
        except:
            self.ui.statusbar.showMessage("Error loading tilesets")
            raise

        self.load_events()

        self.print_map(self.map_data.tilemap)
        self.print_palette()
        self.draw_events(self.map_data.events)
        self.event_spinbox_changed()
        self.loaded_map = True

        self.update_header()

        self.ui.statusbar.showMessage("Map loaded in {} seconds".format(
            time.time() - self.loading_started))


    def get_tile_num_from_mouseclick(self, event, pixmap):
        pos = event.pos()
        x = int(pos.x())
        y = int(pos.y())
        w = pixmap.width()
        #h = pixmap.height()
        tile_size = 16
        tiles_per_row = w // tile_size
        tile_x = x // tile_size
        tile_y = y // tile_size
        tile_num = tile_x + tile_y * tiles_per_row
        return tile_num, tile_x, tile_y

    def get_event_at_pos_from_list(self, pos, events):
        x, y = pos
        i = 0
        for event in events:
            if event['x'] == x and event['y'] == y:
                self.map_data.event_n = i
                return event
            i += 1
        return None

    def get_event_at_pos(self, pos):
        person_events, warp_events, trigger_events, signpost_events = self.map_data.events
        types = (
            ("person", person_events),
            ("warp", warp_events),
            ("trigger", trigger_events),
            ("signpost", signpost_events))
        for event_type, events in types:
            event = self.get_event_at_pos_from_list(pos, events)
            if event:
                return event_type, event
        x, y = pos
        debug(x, y)
        return None, None

    def get_event_from_mouseclick(self, event, pixmap):
        pos = event.pos()
        x = int(pos.x())
        y = int(pos.y())
        w = pixmap.width()
        #h = pixmap.height()
        tile_size = 16
        #tiles_per_row = w // tile_size
        tile_x = x // tile_size
        tile_y = y // tile_size
        event = self.get_event_at_pos((tile_x, tile_y))
        return event, tile_x, tile_y

    def update_event_editor(self, event=None, type=None):
        if type is None:
            type = self.selected_event_type
        if event is None:
            event = self.selected_event

        if event is None: # There is NO self.selected_event
            self.ui.eventsStackedWidget.setCurrentIndex(0)
            return

        if type == "person":
            self.ui.eventsStackedWidget.setCurrentIndex(2)
            sprite_num = event['sprite_num']
            if sprite_num < len(self.game.sprites):
                img = self.game.sprites[sprite_num]
                self.sprite_qimg = ImageQt.ImageQt(img)
                self.ui.sprite_scene.clear()
                self.spritePixMap = QtGui.QPixmap.fromImage(self.sprite_qimg)
                self.ui.sprite_scene.addPixmap(self.spritePixMap)
                self.ui.sprite_scene.update()
        elif type == "warp":
            self.ui.eventsStackedWidget.setCurrentIndex(1)
        elif type == "trigger":
            self.ui.eventsStackedWidget.setCurrentIndex(3)
        elif type == "signpost":
            self.ui.eventsStackedWidget.setCurrentIndex(4)

        for connection in self.ui_event_connections[type]:
            read_function, update_function, data_element = connection
            update_function(event[data_element])

    def save_event_to_memory(self):
        """ take event info from UI and save it in self.selected_event """
        type = self.selected_event_type
        if not type or not self.selected_event:
            return
        for connection in self.ui_event_connections[type]:
            read_function, update_function, data_element = connection
            num = read_function()
            if num is None:
                return
            structure = structure_utils.to_dict(structures.events[type])
            if data_element in structure:
                size = structure[data_element][0]
            else: # Bah, don't check it (it'll apply only to signposts)
                size = "u32"
            if not mapped.fits(num, size):
                raise Exception(data_element + " too big")
            if size == "ptr" and num < 0x8000000:
                num |= 0x8000000
            self.selected_event[data_element] = num

    def save_events(self, skip_ui=False):
        """ Save all events to rom_contents """
        if not skip_ui: # used when removing the selected event
            self.save_event_to_memory()
        mapped.write_events(self.game.rom_contents, self.map_data.events_header,
                            self.map_data.events)
        mapped.write_events_header(self.game.rom_contents, self.map_data.events_header)

    def map_clicked(self, event):
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(
            event, self.mapPixMap)
        debug("clicked tile:", hex(tile_num))
        self.map_data.tilemap[tile_y][tile_x][0] = self.selected_tile
        self.print_map(self.map_data.tilemap)
        self.draw_events(self.map_data.events)

    def mov_clicked(self, event):
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(
            event, self.movPixMap)
        debug("clicked tile:", hex(tile_num))
        self.map_data.tilemap[tile_y][tile_x][1] = self.selected_mov_tile
        self.print_map(self.map_data.tilemap)
        self.draw_events(self.map_data.events)

    def event_clicked(self, qtevent):
        self.reload_lock = True
        self.save_event_to_memory()
        event, event_x, event_y = self.get_event_from_mouseclick(
            qtevent, self.eventPixMap)
        if event == (None, None):
            return
        debug("clicked event tile:", event)
        type, event = event
        self.draw_events(self.map_data.events)
        self.selected_event = event
        self.selected_event_type = type

        self.update_event_editor(event, type)

        square_painter = QtGui.QPainter(self.eventPixMap)
        square_painter.setPen(QtCore.Qt.red)
        square_painter.drawRect(event_x*16, event_y*16, 16, 16)
        square_painter.end()

        event_type_i = ("person", "warp", "trigger", "signpost").index(type)
        self.ui.eventSelectorCombo.setCurrentIndex(event_type_i)
        self.ui.eventSpinBox.setValue(self.map_data.events[event_type_i].index(event))

        self.reload_lock = False

    def palette_clicked(self, event):
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(
            event, self.tilesetPixMap)
        debug("selected tile:", hex(tile_num))
        self.selected_tile = tile_num
        self.print_palette(quick=True)

    def perms_palette_clicked(self, event):
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(
            event, self.permsPalPixMap)
        debug("selected tile:", hex(tile_num))
        self.selected_mov_tile = tile_num

    def save_map(self):
        self.save_header()
        new_map_mem = mapped.map_to_mem(self.map_data.tilemap)
        pos = self.map_data.tilemap_ptr
        size = len(new_map_mem)
        self.game.rom_contents[pos:pos+size] = new_map_mem

    def export_map(self):
        if not self.game or not self.map_data:
            self.ui.statusbar.showMessage("Can't export without loaded map")
            return
        fn, ftype = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save map file', QtCore.QDir.homePath(),
            "Pokemon Map (*.pkmap);;"
            "Script (*.pks);;"
            "All files (*)")
        self.ui.statusbar.showMessage("Exporting...")
        if not fn:
            self.ui.statusbar.clearMessage()
            return

        extension = os.path.splitext(fn)[1]
        if "pkmap" in ftype or extension == "pkmap":
            mapmem = self.game.rom_contents[self.map_data.tilemap_ptr:]
            w, h = self.map_data.data_header["w"], self.map_data.data_header["h"]
            text_map = map_printer.map_to_text(mapmem, w, h)
            with open(fn, "wb") as file:
                file.write(text_map.encode("utf8"))
        elif "pks" in ftype or extension == "pks":
            with open(fn, "wb") as file:
                file.write(mapped.export_script(self.game, self.map_data))
        else:
            self.ui.statusbar.showMessage("Unkown file type {}, not saved".format(
                extension))
            return

        self.ui.statusbar.showMessage("Saved {}".format(fn))

    def import_map(self):
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Load map file',
                                                      QtCore.QDir.homePath(),
                                                      "Pokemon Map (*.pkmap);;"
                                                      "All files (*)")
        with open(fn, "r") as map_text_file:
            map_text = map_text_file.read()
        new_map = map_printer.text_to_mem(map_text)
        ptr = self.map_data.tilemap_ptr
        self.game.rom_contents[ptr:ptr+len(new_map)] = new_map
        self.loaded_map = False
        self.load_map(self.map_data.bank_n, self.map_data.map_n)
        self.ui.statusbar.showMessage("Loaded {}".format(fn))

    def write_to_file(self):
        if self.loaded_map:
            self.save_map()
            self.save_events()
        self.write_rom()

    def save_as(self):
        fn, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save ROM file',
                                                      QtCore.QDir.homePath(),
                                                      "GBA ROM (*.gba);;"
                                                      "All files (*)")

        if not fn:
            debug("Nothing selected")
            return
        debug(fn)
        import shutil
        shutil.copyfile(self.game.rom_file_name, fn)
        self.game.rom_file_name = fn
        self.write_to_file()

    def update_signpost_stacked(self):
        if self.ui.s_type.currentIndex() < 5:
            self.ui.signpost_stacked.setCurrentIndex(0)
        else:
            self.ui.signpost_stacked.setCurrentIndex(1)

    def add_event(self, type):
        self.save_events()
        mapped.add_event(self.game.rom_contents, self.map_data.events_header, type)
        mapped.write_events_header(self.game.rom_contents, self.map_data.events_header)
        self.load_events()
        self.draw_events(self.map_data.events)
        self.update_event_spinbox_max_value()

    def rem_event(self, type):
        self.save_events()
        mapped.rem_event(self.game.rom_contents, self.map_data.events_header, type)
        mapped.write_events_header(self.game.rom_contents, self.map_data.events_header)
        self.load_events()
        self.draw_events(self.map_data.events)
        if self.selected_event not in self.map_data.events:
            self.selected_event = None
            self.selected_event_type = None
            self.update_event_editor()
            self.update_event_spinbox_max_value()

    def rem_this_event(self):
        # We remove it from the runtime list, save to ROM and delete
        # the last (bad) event in the ROM
        this_event = self.selected_event
        type = self.selected_event_type

        self.selected_event = None
        self.selected_event_type = None

        for typed_events in self.map_data.events:
            try:
                typed_events.remove(this_event)
            except ValueError:
                pass
        self.save_events(skip_ui=True)
        mapped.rem_event(self.game.rom_contents, self.map_data.events_header, type)
        mapped.write_events_header(self.game.rom_contents, self.map_data.events_header)

        self.load_events()
        self.draw_events(self.map_data.events)
        self.update_event_editor()

    add_warp = lambda self: self.add_event("warp")
    rem_warp = lambda self: self.rem_event("warp")
    add_person = lambda self: self.add_event("person")
    rem_person = lambda self: self.rem_event("person")
    add_trigger = lambda self: self.add_event("trigger")
    rem_trigger = lambda self: self.rem_event("trigger")
    add_signpost = lambda self: self.add_event("signpost")
    rem_signpost = lambda self: self.rem_event("signpost")

    def event_spinbox_changed(self, dont_recurse_pls=False):
        if not dont_recurse_pls:
            self.update_event_spinbox_max_value()
        combo = self.ui.eventSelectorCombo
        spin = self.ui.eventSpinBox

        self.reload_lock = True
        self.save_event_to_memory()
        event_type_i = combo.currentIndex()
        if len(self.map_data.events[event_type_i]) == 0:
            self.ui.eventsStackedWidget.setCurrentIndex(0)
            return
        events = self.map_data.events[event_type_i]
        try:
            event = events[int(spin.value())]
        except IndexError:
            event = events[0]
        event_x, event_y = event["x"], event["y"]
        debug("selected event tile:", event)
        self.draw_events(self.map_data.events)
        self.selected_event = event
        type = ("person", "warp", "trigger", "signpost")[event_type_i]
        self.selected_event_type = type
        self.update_event_editor()

        square_painter = QtGui.QPainter(self.eventPixMap)
        square_painter.setPen(QtCore.Qt.red)
        square_painter.drawRect(event_x*16, event_y*16, 16, 16)
        square_painter.end()

        self.reload_lock = False

    def update_event_spinbox_max_value(self):
        combo = self.ui.eventSelectorCombo
        spin = self.ui.eventSpinBox
        type_i = combo.currentIndex()
        max_event = len(self.map_data.events[type_i])-1 # -1 cause index 0
        if max_event == -1:
            spin.setEnabled(False)
        else:
            spin.setEnabled(True)
            spin.setMaximum(max_event)
        self.event_spinbox_changed(True)

    def go_to_warp(self, _, bank=None, map=None):
        if bank is None:
            bank = self.selected_event["bank_num"]
        if map is None:
            map = self.selected_event["map_num"]
        debug(bank, map)
        self.load_map(bank, map)

    def launch_script_editor(self, offset=None, file_name=None, command=None,
                             xse=None):
        if xse is None:
            xse = self.isxse
        if not command:
            command = self.script_editor_command
        if not file_name:
            file_name = self.game.rom_file_name
        if not offset:
            self.save_event_to_memory()
            offset = self.selected_event['script_ptr']
        debug(hex(offset))
        debug(xse)
        if sys.platform == "win32":
            file_name = file_name.replace("/", "\\")
        if not xse:
            args = [command, file_name, hex(offset)]
        else:
            args = [command, file_name+":"+hex(mapped.get_rom_addr(offset))[2:]]
        import subprocess
        subprocess.Popen(args)

    def select_script_editor(self):
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                      'Choose script editor executable',
                                                      QtCore.QDir.homePath(),
                                                      "All files (*)")
        q = "Is it XSE?"
        isxse = QtWidgets.QMessageBox.question(self, q, q,
                                               QtWidgets.QMessageBox.Yes,
                                               QtWidgets.QMessageBox.No)
        if isxse == QtWidgets.QMessageBox.Yes:
            self.isxse = True
        else:
            self.isxse = False

        self.script_editor_command = fn
        self.save_settings()

    def open_warp_in_emulator(self):
        """ Never got it working outside linux """
        warp_num = self.map_data.event_n
        bank_num = self.map_data.bank_n
        map_num = self.map_data.map_n
        if self.game.name == "EM":
            codebin_fn = "warpem.gba"
        elif self.game.name == "FR":
            codebin_fn = "warpfr.gba"
        elif self.game.name == "RS":
            codebin_fn = "warprs.gba"
        with open(codebin_fn, "rb") as codebin:
            code = codebin.read()
        script = "load 1\n"
        script += "er 15 0x02f10000\n"
        script += ''.join(
            ['eb ' + hex(0x02f10000+i) + " " +
             hex(byte)[2:] + "\n"
             for i, byte in enumerate(code)])
        script += ("eb 0x02f30000 39" +
                   "eb 0x02f30001 %s\n" % hex(bank_num)[2:] +
                   "eb 0x02f30002 %s\n" % hex(map_num)[2:] +
                   "eb 0x02f30003 %s\n" % hex(warp_num)[2:] +
                   "eb 0x02f30004 02\n")
        debug(script)
        with open("script.txt", "w") as file:
            file.write(script)
        file_name = self.game.rom_file_name
        if os.name == 'posix': # Dunno 'bout Macs and BSDs, but Linux is posix
            command = './vbam'
        else:
            command = './vbam.exe'
        import subprocess
        debug(command, "-c", "cfg", "-r", file_name)
        #subprocess.Popen([command, "-c", "cfg", "--debug", "-r", file_name])
        subprocess.Popen([command, "-c", "cfg", "-r", file_name])

    def load_settings(self):
        try:
            with open(settings_path) as settings_file:
                settings_text = settings_file.read()
        except FileNotFoundError:
            return
        import ast
        settings = ast.literal_eval(settings_text)
        if "script_editor" in settings:
            self.script_editor_command = settings["script_editor"]
        else:
            self.script_editor_command = None
        if "script_editor_is_xse" in settings:
            self.isxse = settings["script_editor_is_xse"]
        if "nocolor" in settings:
            if settings["nocolor"] is True:
                mapped.GRAYSCALE = mapped.grayscale_pal
            else:
                mapped.GRAYSCALE = settings["nocolor"]

    def save_settings(self):
        settings = {"script_editor": self.script_editor_command,
                    "nocolor": mapped.GRAYSCALE,
                    "script_editor_is_xse": self.isxse}
        with open(settings_path, "w") as settings_file:
            settings_file.write(str(settings))

    def add_new_banks(self):
        num, ok = QtWidgets.QInputDialog.getInt(self, 'How many?', # Title
                                                "How many?", # Label
                                                1, 1, 255) # Default, min, max
        if not ok:
            return
        oldnum = len(self.game.banks)
        ptr = mapped.add_banks(self.game.rom_contents, self.game.rom_data["MapHeaders"],
                               oldnum, oldnum+num)
        mapped.write_rom_ptr_at(self.game.rom_contents,
                                self.game.rom_data["MapHeaders"], ptr)
        self.load_banks()

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

    def load_level_scripts(self):
        """ I don't even... me from the past, did something good happen that day? """
        struct = structures.lscript_entry
        struct2 = structures.lscript_type_2
        r = lambda p: mapped.parse_data_structure(self.game.rom_contents, struct, p)
        r2 = lambda p: mapped.parse_data_structure(self.game.rom_contents, struct2, p)
        p = self.map_data.header['level_script_ptr']
        e = r(p)
        layout = self.ui.lscriptsLayout
        # Clear
        for i in reversed(range(layout.count())):
            li = layout.itemAt(i)
            for j in reversed(range(li.count())):
                li.itemAt(j).widget().setParent(None)
            layout.removeItem(li)

        while e['type'] != 0:
            layout = QtWidgets.QHBoxLayout()
            typeLabel = QtWidgets.QLabel("Type:")
            ptrLabel = QtWidgets.QLabel("Pointer:")
            ptr2Label = QtWidgets.QLabel("Pointer 2:")
            flagLabel = QtWidgets.QLabel("Flag:")
            valueLabel = QtWidgets.QLabel("Value:")
            typeLineEdit = QtWidgets.QLineEdit()
            ptrLineEdit = QtWidgets.QLineEdit()
            ptr2LineEdit = QtWidgets.QLineEdit()
            flagLineEdit = QtWidgets.QLineEdit()
            valueLineEdit = QtWidgets.QLineEdit()
            layout.addWidget(typeLabel)
            layout.addWidget(typeLineEdit)
            layout.addWidget(ptrLabel)
            layout.addWidget(ptrLineEdit)
            layout.addWidget(ptr2Label)
            layout.addWidget(ptr2LineEdit)
            layout.addWidget(flagLabel)
            layout.addWidget(flagLineEdit)
            layout.addWidget(valueLabel)
            layout.addWidget(valueLineEdit)
            self.ui.lscriptsLayout.addLayout(layout)
            typeLineEdit.setText(str(e["type"]))
            ptrLineEdit.setText(hex(e["script_header_ptr"]))
            if e["type"] in (2, 4):
                e2 = r2(e["script_header_ptr"])
                ptr2LineEdit.setText(hex(e2["script_body_ptr"]))
                flagLineEdit.setText(hex(e2["flag"]))
                valueLineEdit.setText(hex(e2["value"]))
                b = QtWidgets.QPushButton()
                b.setText("Edit Script")
                launchscripteditor = (
                    lambda: self.launch_script_editor(offset=int(ptr2LineEdit.text(), 16))
                )
                b.clicked.connect(launchscripteditor)
                layout.addWidget(b)
            else:
                ptr2LineEdit.hide()
                flagLineEdit.hide()
                valueLineEdit.hide()
                ptr2Label.hide()
                flagLabel.hide()
                valueLabel.hide()
            p += structure_utils.size_of(struct)
            e = r(p)

    def add_level_script(self):
        """ TODO """
        print("+")

def main():
    # FIXME: We sometimes get segfaults on exit
    app = QtWidgets.QApplication(sys.argv)
    try:
        win = Window()
    except:
        app.deleteLater()
        raise
    if len(sys.argv) >= 5: # Running as a test
        app.deleteLater()
        sys.exit(0)
    win.show()
    r = app.exec_()
    win.close()
    app.deleteLater()
    sys.exit(r)

if __name__ == "__main__":
    main()

