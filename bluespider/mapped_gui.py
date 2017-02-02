#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Blue Spider UI's code. In real need of refactoring, but seems to work. """

# If I keep trying, this code will end up looking as messy as elite map's!

import os
import sys
import time
import pkgutil
import threading

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
        self.ui.edPalette.setScene(self.ui.palette_scene)
        self.ui.tileset_scene = QtWidgets.QGraphicsScene()
        self.ui.tileset.setScene(self.ui.tileset_scene)
        self.ui.tile_preview_scene = QtWidgets.QGraphicsScene()
        self.ui.tilePreview.setScene(self.ui.tile_preview_scene)
        self.ui.layer1_scene = QtWidgets.QGraphicsScene()
        self.ui.layer1.setScene(self.ui.layer1_scene)
        self.ui.layer2_scene = QtWidgets.QGraphicsScene()
        self.ui.layer2.setScene(self.ui.layer2_scene)

        self.game = game.Game()
        self.map_data = mapdata.MapData()

        self.blocks_img_qt = None

        #self.map_data.events_header = None
        self.mapPixMap = None
        self.spritePixMap = None
        self.tilesetPixMap = None
        self.eventPixMap = None
        self.movPixMap = None
        self.tileset_editorPixMap = None
        self.tpreviewPixMap = None
        self.layer1PixMap = None
        self.layer2PixMap = None
        self.permsPalPixMap = None
        self.map_img_qt = None
        self.mov_img_qt = None
        self.tileset_ed_img_qt = None
        self.tpreview_img_qt = None
        self.layer1_img_qt = None
        self.layer2_img_qt = None
        self.event_img_qt = None
        #self.map_data.tilemap_ptr = None
        #self.map_data.map_n = None
        self.map_img = None

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

        self.ui.m_data_ptr.textChanged.connect(self.map_was_modified)
        self.ui.m_ptr_index.textChanged.connect(self.map_was_modified)
        self.ui.ls_ptr.textChanged.connect(self.map_was_modified)
        self.ui.con_data_ptr.textChanged.connect(self.map_was_modified)
        self.ui.song_index.textChanged.connect(self.map_was_modified)
        self.ui.label_index.textChanged.connect(self.map_was_modified)
        self.ui.map_type.textChanged.connect(self.map_was_modified)
        self.ui.weather_type.textChanged.connect(self.map_was_modified)
        self.ui.battle_type.textChanged.connect(self.map_was_modified)
        self.ui.map_w.textChanged.connect(self.map_was_modified)
        self.ui.map_h.textChanged.connect(self.map_was_modified)
        self.ui.tilemap_ptr.textChanged.connect(self.map_was_modified)
        self.ui.t1_ptr.textChanged.connect(self.map_was_modified)
        self.ui.t2_ptr.textChanged.connect(self.map_was_modified)
        self.ui.border_info_ptr.textChanged.connect(self.map_was_modified)
        self.ui.show_label_byte.textChanged.connect(self.map_was_modified)
        self.ui.is_cave_byte.textChanged.connect(self.map_was_modified)


        self.ui.addLevelScriptButton.clicked.connect(self.add_level_script)

        self.ui.behaviour1.textChanged.connect(self.blocks_were_modified)
        self.ui.behaviour2.textChanged.connect(self.blocks_were_modified)
        self.ui.background1.textChanged.connect(self.blocks_were_modified)
        self.ui.background2.textChanged.connect(self.blocks_were_modified)
        self.ui.xFlipBox.clicked.connect(self.print_preview_tile)
        self.ui.yFlipBox.clicked.connect(self.print_preview_tile)
        self.ui.saveBlocksButton.clicked.connect(self.save_blocks)
        self.ui.paletteSelectorCombo.currentIndexChanged.connect(
            self.selected_palette_changed
        )

        self.ui.PalTab.setEnabled(False)

        self.selected_tile = 0
        self.selected_small_tile = 0
        self.hovered_tile = None
        self.selected_mov_tile = 0
        self.selected_event = None
        self.selected_event_type = None
        self.selected_pal = 0
        self.map_modified = None
        self.blocks_modified = None
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
        self.current_map_n = None
        self.current_bank_n = None
        self.event_n = None

        self.script_editor_command = ''
        self.isxse = False
        self.load_settings()

        if len(sys.argv) >= 2 and not no_argv:
            self.load_rom(sys.argv[1])
        if len(sys.argv) >= 4 and not no_argv:
            self.load_map(int(sys.argv[2]), int(sys.argv[3]))

    def confirm_saving_dialog(self, title, question='Would you like to save the changes?', detailed=True):
        self.ui.centralwidget.setEnabled(False)
        self.ui.menubar.setEnabled(False)
        msgbox = QtWidgets.QMessageBox()
        msgbox.setWindowTitle(title)
        msgbox.setText(question)
        if detailed:
            msgbox.setInformativeText('  (Changes will be saved to a buffer, click show details to see more)')
            msgbox.setDetailedText('None of the changes you have done will be actually written to your rom, '
                                   'they will be saved in a buffer. To actually save the changes use the '
                                   '"Save" option in the "File" menu.')
        msgbox.setIcon(QtWidgets.QMessageBox.Question)
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | \
                                  QtWidgets.QMessageBox.Cancel)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.Save)
        result = msgbox.exec()
        self.ui.centralwidget.setEnabled(True)
        self.ui.menubar.setEnabled(True)
        return result

    def redraw_events(self):
        """ Called when some event's position is changed in the GUI """
        if self.reload_lock:
            return
        self.save_event_to_memory()
        self.load_map(self.current_bank_n, self.current_map_n)
        index = ["person", "warp",
                 "trigger", "signpost"].index(self.selected_event_type)
        self.selected_event = self.map_data.events[index][self.event_n]

    def reload_person_img(self):
        """ Called when the sprite num. is changed in the GUI """
        if self.reload_lock:
            return
        self.save_event_to_memory()
        self.update_event_editor()

    def load_rom(self, fn=None):
        """ If no filename is given, it'll prompt the user with a nice dialog """

        if self.game.name and self.close_rom_confirm():
            return

        if fn is None:
            fn, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open ROM file',
                                                          QtCore.QDir.homePath(),
                                                          "GBA ROM (*.gba);;"
                                                          "All files (*)")
        if not fn:
            return

        self.loaded_map = None
        self.map_modified = None
        self.blocks_modified = None
        self.ui.centralwidget.setEnabled(False)
        self.ui.menubar.setEnabled(False)
        if self.game.name:
            self.tree_model.clear()
            self.disable_behback_signals(True)
            self.ui.behaviour1.setText('')
            self.ui.background1.setText('')
            self.ui.behaviour2.setText('')
            self.ui.background2.setText('')
            self.disable_behback_signals(False)
            self.ui.map_scene.clear()
            self.ui.mov_scene.clear()
            self.ui.palette_scene.clear()
            self.ui.perms_palette_scene.clear()
            self.ui.event_scene.clear()
            self.ui.tileset_scene.clear()
            self.ui.tile_preview_scene.clear()
            self.ui.layer1_scene.clear()
            self.ui.layer2_scene.clear()

            self.ui.t1_img_ptr.setText('')
            self.ui.t2_img_ptr.setText('')

            self.ui.PalTab.setEnabled(False)
            self.ui.eventsTab.setEnabled(False)
            self.ui.HeaderTab.setEnabled(False)
            self.map_data = mapdata.MapData()
        self.game.load_rom(fn)

        self.load_banks()
        self.ui.centralwidget.setEnabled(True)
        self.ui.menubar.setEnabled(True)

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

        self.game.rom_contents = actual_rom_contents
        self.game.original_rom_contents = bytes(actual_rom_contents)

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
            map = mapped.parse_map_header(self.game, ptr)
            index = map['label_index']
            if self.game.name == 'FR':
                index -= 88 # Magic!
            if index >= len(map_labels):
                continue
            label = map_labels[index]
            self.tree_model.item(bank_num).appendRow(
                QtGui.QStandardItem("%s - %s" % (i, label)))

    def paint_square(self, pixmap, x, y, h, w, color=QtCore.Qt.red):
        square_painter = QtGui.QPainter(pixmap)
        square_painter.setPen(color)
        square_painter.drawRect(x, y, h, w)
        square_painter.end()

    def draw_palette(self):
        """ Draws the tile palette (not the colors but the selectable tiles) """
        blocks_imgs = self.map_data.blocks.images
        perms_imgs = self.mov_perms_imgs
        perms_img_w = self.map_data.blocks.images_wide
        blocks_img_h = (len(blocks_imgs) * 16) // 8
        perms_img_h = (len(perms_imgs) * 16) // 8
        blocks_img = Image.new("RGB", (self.map_data.blocks.images_wide, blocks_img_h))
        perms_img = Image.new("RGB", (perms_img_w, perms_img_h))
        i = 0
        for row in range(blocks_img_h // 16):
            for col in range(self.map_data.blocks.images_wide // 16):
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

        self.blocks_img_qt = ImageQt.ImageQt(blocks_img)
        self.perms_pal_img_qt = ImageQt.ImageQt(perms_img)

        # Palette is not draw yet at this point, draw palette has to be called too

    def print_palette(self, quick=False):
        if not quick:
            self.draw_palette()
        self.tilesetPixMap = QtGui.QPixmap.fromImage(self.blocks_img_qt)
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

        p = self.selected_tile
        w = self.map_data.blocks.images_wide // 16
        x = (p%w)*16
        y = (p//w)*16
        self.paint_square(self.tilesetPixMap, x, y, 16, 16)
        p = self.selected_mov_tile
        x = (p % 8) * 16
        y = (p // 8) * 16
        self.paint_square(self.permsPalPixMap, x, y, 16, 16)

    def draw_map(self, map):
        w = len(map[0])
        h = len(map)
        map_img = Image.new("RGB", (w*16, h*16))
        mov_img = Image.new("RGB", (w*16, h*16))
        for row in range(h):
            for tile in range(w):
                tile_num, behaviour = map[row][tile]
                x = tile*16
                y = row*16
                x2 = x+16
                y2 = y+16
                pos = (x, y, x2, y2)
                if tile_num < len(self.map_data.blocks.images):
                    map_img.paste(self.map_data.blocks.images[tile_num], pos)
                    mov_img.paste(self.map_data.blocks.images[tile_num], pos)
                if behaviour < len(self.mov_perms_imgs):
                    mov_img.paste(self.mov_perms_imgs[behaviour], pos,
                                  self.mov_perms_imgs[behaviour])

        self.map_img = map_img
        self.map_img_qt = ImageQt.ImageQt(map_img)
        self.mov_img_qt = ImageQt.ImageQt(mov_img)

    def print_map(self, map, quick=False, delete_old=True):
        if not quick:
            self.draw_map(map)
        self.mapPixMap = QtGui.QPixmap.fromImage(self.map_img_qt)
        self.movPixMap = QtGui.QPixmap.fromImage(self.mov_img_qt)
        if delete_old:
            self.ui.map_scene.clear()
            self.ui.mov_scene.clear()
            self.map_pixmap_qobject = qmapview.QMapPixmap(self.mapPixMap)
            self.mov_pixmap_qobject = qmapview.QMapPixmap(self.movPixMap)
            self.ui.map_scene.addItem(self.map_pixmap_qobject)
            self.ui.mov_scene.addItem(self.mov_pixmap_qobject)
            self.map_pixmap_qobject.clicked.connect(
                lambda event: self.base_map_clicked(event, self.selected_tile, self.mapPixMap, 0)
            )
            self.map_pixmap_qobject.click_dragged.connect(
                lambda event: self.base_map_clicked(event, self.selected_tile, self.mapPixMap, 0)
            )
            self.mov_pixmap_qobject.clicked.connect(
                lambda event: self.base_map_clicked(event, self.selected_mov_tile, self.movPixMap, 1)
            )
            self.mov_pixmap_qobject.click_dragged.connect(
                lambda event: self.base_map_clicked(event, self.selected_mov_tile, self.movPixMap, 1)
            )
        else:
            self.map_pixmap_qobject.set_pixmap(self.mapPixMap)
            self.mov_pixmap_qobject.set_pixmap(self.movPixMap)
        self.ui.map_scene.update()
        self.ui.mov_scene.update()

        if self.hovered_tile is not None:
            p = self.selected_tile
            w = self.map_data.blocks.images_wide // 16
            x = (p%w)*16
            y = (p//w)*16
            self.paint_square(self.mapPixMap, x, y, 16, 16, QtCore.Qt.white)

    def print_tileset(self, delete_old=True):
        img = self.map_data.complete_tilesets[self.selected_pal]
        img_w, img_h = img.size
        self.tileset_ed_img_qt = ImageQt.ImageQt(img.resize((img_w * 2, img_h * 2)))
        self.tileset_editorPixMap = QtGui.QPixmap.fromImage(self.tileset_ed_img_qt)

        if delete_old:
            self.ui.tileset_scene.clear()
            self.tileset_pixmap_qobject = qmapview.QMapPixmap(self.tileset_editorPixMap)
            self.ui.tileset_scene.addItem(self.tileset_pixmap_qobject)
            self.tileset_pixmap_qobject.clicked.connect(self.tileset_clicked)
        else:
            self.tileset_pixmap_qobject.set_pixmap(self.tileset_editorPixMap)
        self.ui.tileset_scene.update()

        p = self.selected_small_tile
        w = 16
        x = (p % w) * 16
        y = (p // w) * 16
        self.paint_square(self.tileset_editorPixMap, x, y, 16, 16)

    def print_preview_tile(self, delete_old=True):
        img = self.map_data.cropped_tileset[self.selected_pal][self.selected_small_tile]
        if self.ui.xFlipBox.isChecked():
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if self.ui.yFlipBox.isChecked():
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        w, h = img.size
        img = img.resize((w * 2, h * 2))
        self.tpreview_img_qt = ImageQt.ImageQt(img)
        self.tpreviewPixMap = QtGui.QPixmap.fromImage(self.tpreview_img_qt)
        if delete_old:
            self.ui.tile_preview_scene.clear()
            self.tpreview_pixmap_qobject = qmapview.QMapPixmap(self.tpreviewPixMap)
            self.ui.tile_preview_scene.addItem(self.tpreview_pixmap_qobject)
        else:
            self.tpreview_pixmap_qobject.set_pixmap(self.tpreviewPixMap)
        self.ui.tile_preview_scene.update()

    def print_block_layers(self, layer=-1, delete_old=True):
        layer_imgs = self.map_data.get_block_layers(self.selected_tile)
        if layer in (0, -1):
            self.layer1_img_qt = ImageQt.ImageQt(layer_imgs[0].resize((32, 32)))
            self.layer1PixMap = QtGui.QPixmap.fromImage(self.layer1_img_qt)
            if delete_old:
                self.ui.layer1_scene.clear()
                self.layer1_pixmap_qobject = qmapview.QMapPixmap(self.layer1PixMap)
                self.ui.layer1_scene.addItem(self.layer1_pixmap_qobject)

                self.layer1_pixmap_qobject.clicked.connect(
                    lambda event: self.base_layer_clicked(event, 0)
                )
            else:
                self.layer1_pixmap_qobject.set_pixmap(self.layer1PixMap)
            self.ui.layer1_scene.update()

        if layer in (1, -1):
            self.layer2_img_qt = ImageQt.ImageQt(layer_imgs[1].resize((32, 32)))
            self.layer2PixMap = QtGui.QPixmap.fromImage(self.layer2_img_qt)
            if delete_old:
                self.ui.layer2_scene.clear()
                self.layer2_pixmap_qobject = qmapview.QMapPixmap(self.layer2PixMap)
                self.ui.layer2_scene.addItem(self.layer2_pixmap_qobject)

                self.layer2_pixmap_qobject.clicked.connect(
                    lambda event: self.base_layer_clicked(event, 1)
                )
            else:
                self.layer2_pixmap_qobject.set_pixmap(self.layer2PixMap)
            self.ui.layer2_scene.update()

    def disable_behback_signals(self, bool):
        self.ui.behaviour1.blockSignals(bool)
        self.ui.behaviour2.blockSignals(bool)
        self.ui.background1.blockSignals(bool)
        self.ui.background2.blockSignals(bool)

    def show_block_behbacks(self):
        block = self.map_data.blocks.blocks[self.selected_tile]
        self.disable_behback_signals(True)
        self.ui.behaviour1.setText(hex(block.behaviour1))
        self.ui.background1.setText(hex(block.background1))
        if block.behaviour2 is not None:
            self.ui.behaviour2.setText(hex(block.behaviour2))
            self.ui.background2.setText(hex(block.background2))
        self.disable_behback_signals(False)

    def update_block_behbacks(self):
        try:
            beh1 = self.ui.behaviour1.text()
            back1 = self.ui.background1.text()
            if self.ui.behaviour2.isEnabled():
                beh2 = self.ui.behaviour2.text()
                back2 = self.ui.background2.text()
                self.map_data.update_block_behback(self.selected_tile, beh1, back1, beh2, back2)
            else:
                self.map_data.update_block_behback(self.selected_tile, beh1, back1)
        except Exception as e:
            raise e
            QtWidgets.QMessageBox.critical(self, 'ERROR:', str(e))

            result = QtWidgets.QMessageBox.question(self, 'Discard?',
                                                    'Would you like to discard behaviour and background bytes?',
                                                    QtWidgets.QMessageBox.Yes,
                                                    QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.No:
                return 1
        return 0

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
        for addr in (events_header[n] for n in ('person_events_ptr',
                                                'signpost_events_ptr',
                                                'trigger_events_ptr',
                                                'warp_events_ptr')):
            if not mapped.is_word_aligned(addr):
                QtWidgets.QMessageBox.critical(self, "bad header",
                                               str("unaligned event header"))
        self.ui.num_of_warps.setText(str(events_header['n_of_warps']))
        self.ui.num_of_people.setText(str(events_header['n_of_people']))
        self.ui.num_of_triggers.setText(str(events_header['n_of_triggers']))
        self.ui.num_of_signposts.setText(str(events_header['n_of_signposts']))

    def load_map_qindex(self, qindex):
        bank_n = qindex.parent().row()
        if bank_n == -1:
            return
        map_n = qindex.row()
        self.current_bank_n = bank_n
        self.current_map_n = map_n
        self.load_map(bank_n, map_n)

    def load_map(self, bank_n, map_n):
        """ Called when a map is selected, a warp is clicked or the map has
            to be reloaded. """
        if bank_n >= len(self.game.banks):
            return
        self.loading_started = time.time()

        self.ui.statusbar.showMessage("Loading map...")
        if self.loaded_map:
            if (self.map_modified and self.save_map(confirm=True)) or \
                    (self.blocks_modified and self.save_blocks(confirm=True)):
                # If abort, abort...
                return
            self.save_events()

        self.ui.treeView.expand(self.tree_model.index(bank_n, 0))
        self.ui.treeView.setCurrentIndex(
            self.tree_model.index(map_n, 0, self.tree_model.index(bank_n, 0)))

        debug(bank_n, map_n)
        previous_map_data = self.map_data
        self.map_data = mapdata.MapData()
        try:
            self.map_data.load(self.game, bank_n, map_n)
        except Exception as e: # TODO: type of exception
            QtWidgets.QMessageBox.critical(self, "ERROR loading map!", str(e))
            self.map_data = previous_map_data
            return

        self.load_level_scripts()
        try:
            self.map_data.load_tilesets(self.game, previous_map_data)
            self.print_tileset()
            if self.selected_small_tile >= len(self.map_data.cropped_tileset[0]):
                self.selected_small_tile = 0
            self.print_preview_tile()
            if self.selected_tile >= len(self.map_data.blocks.blocks):
                self.selected_tile = 0
            self.print_block_layers()
            self.show_block_behbacks()
            self.ui.t1_img_ptr.setText(
                hex(self.map_data.tileset1.header['tileset_image_ptr']))
            self.ui.t2_img_ptr.setText(
                hex(self.map_data.tileset2.header['tileset_image_ptr']))
        except Exception:
            QtWidgets.QMessageBox.critical(self, "Error loading tilesets", str(e))
            self.ui.statusbar.showMessage("Error loading tilesets")
            #raise
            return

        self.load_events()

        self.print_map(self.map_data.tilemap)
        self.print_palette()
        self.draw_events(self.map_data.events)
        self.event_spinbox_changed()
        if not self.loaded_map:
            self.ui.PalTab.setEnabled(True)
            if self.game.name in ('EM', 'RS'):
                self.ui.behaviour2.setEnabled(False)
                self.ui.background2.setEnabled(False)
            self.ui.eventsTab.setEnabled(True)
            self.ui.HeaderTab.setEnabled(True)
            self.loaded_map = True

        self.update_header()

        self.map_modified = False
        self.blocks_modified = False
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

    def select_tile(self, tile_num, map_type):
        if map_type == 0:
            if self.update_block_behbacks():
                return
            self.selected_tile = tile_num
            self.print_block_layers()
            self.show_block_behbacks()
        elif map_type == 1:
            self.selected_mov_tile = tile_num

        self.print_palette(quick=True)

    def base_map_clicked(self, event, selected_tile, pixmap, map_type):
        # map_type:
        #   0   Regular map
        #   1   Movemente permission map
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(
            event, pixmap)
        debug("clicked tile:", hex(tile_num))

        button = event.button()
        if button == QtCore.Qt.NoButton and hasattr(event, 'origin_button'):
            button = event.origin_button
        original_tile = self.map_data.tilemap[tile_y][tile_x][map_type]
        # Left click
        if button == QtCore.Qt.LeftButton and original_tile != selected_tile:
            self.map_data.tilemap[tile_y][tile_x][map_type] = selected_tile
            self.print_map(self.map_data.tilemap, delete_old=False)
            self.draw_events(self.map_data.events)
            self.map_was_modified()
        # Right click
        elif button == QtCore.Qt.RightButton:
            self.select_tile(self.map_data.tilemap[tile_y][tile_x][map_type], map_type)
        # Mouse wheel click
        elif button == QtCore.Qt.MiddleButton and original_tile != selected_tile:
            to_paint_tiles = [(tile_y, tile_x)]
            testing = []
            tiles_width = len(self.map_data.tilemap)
            tiles_heigth = len(self.map_data.tilemap[0])
            while len(to_paint_tiles):
                current_tile_y, current_tile_x = to_paint_tiles[0]
                del to_paint_tiles[0]
                self.map_data.tilemap[current_tile_y][current_tile_x][map_type] = selected_tile
                for next_to_tile_y in (current_tile_y - 1, current_tile_y + 1):
                    if 0 <= next_to_tile_y < tiles_width and \
                                    self.map_data.tilemap[next_to_tile_y][current_tile_x][map_type] \
                                    == original_tile and (next_to_tile_y, current_tile_x) not in to_paint_tiles:
                        to_paint_tiles.append((next_to_tile_y, current_tile_x))
                for next_to_tile_x in (current_tile_x - 1, current_tile_x + 1):
                    if 0 <= next_to_tile_x < tiles_heigth and \
                                    self.map_data.tilemap[current_tile_y][next_to_tile_x][map_type] \
                                    == original_tile and (current_tile_y, next_to_tile_x) not in to_paint_tiles:
                        to_paint_tiles.append((current_tile_y, next_to_tile_x))
            self.print_map(self.map_data.tilemap, delete_old=False)
            self.draw_events(self.map_data.events)
            self.map_was_modified()

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
        self.select_tile(tile_num, 0)

    def tileset_clicked(self, event):
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(
            event, self.tileset_editorPixMap)
        self.selected_small_tile = tile_num
        self.print_tileset(delete_old=False)
        self.print_preview_tile(delete_old=False)

    def base_layer_clicked(self, event, layer):
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(
            event, self.layer1PixMap)

        button = event.button()
        if button == QtCore.Qt.LeftButton:
            self.map_data.update_block_img(self.selected_tile, layer, tile_num, self.selected_small_tile,
                                           self.selected_pal, self.ui.xFlipBox.isChecked(),
                                           self.ui.yFlipBox.isChecked())
            self.print_block_layers(delete_old=False)
            self.print_palette()
            self.print_map(self.map_data.tilemap)
            self.blocks_were_modified()
        elif button == QtCore.Qt.RightButton:
            new_tile_num, new_pal, x_flip, y_flip = self.map_data.blocks.blocks[self.selected_tile][layer][tile_num]
            self.selected_small_tile = new_tile_num

            self.ui.xFlipBox.setChecked(x_flip)
            self.ui.yFlipBox.setChecked(y_flip)

            if self.selected_pal != new_pal:
                self.selected_pal = new_pal
                self.ui.paletteSelectorCombo.setCurrentIndex(new_pal)
            else:
                self.print_tileset()
                self.print_preview_tile()

    def perms_palette_clicked(self, event):
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(
            event, self.permsPalPixMap)
        debug("selected tile:", hex(tile_num))
        self.select_tile(tile_num, 1)

    def blocks_were_modified(self):
        if not self.blocks_modified:
            self.ui.saveBlocksButton.setEnabled(True)
            self.blocks_modified = True

    def save_blocks(self, confirm=False):
        if self.ui.saveBlocksButton.isEnabled():
            self.ui.saveBlocksButton.setEnabled(False)
        if confirm:
            result = self.confirm_saving_dialog('Blocks have been modified')
            if result == QtWidgets.QMessageBox.Cancel:
                # Abort
                return 1
            elif result == QtWidgets.QMessageBox.Discard:
                # Continue without saving
                return 0

        # Save blocks
        if self.update_block_behbacks():
            return 1
        self.map_data.save_blocks(self.game.rom_contents)
        self.blocks_modified = False
        self.ui.statusbar.showMessage('Blocks saved')
        return 0

    def map_was_modified(self):
        if not self.map_modified:
            self.map_modified = True

    def save_map(self, confirm=False):
        if self.blocks_modified and self.save_blocks(confirm):
            #If abort, abort...
            return 1

        if confirm:
            result = self.confirm_saving_dialog('Current map has been modified')
            if result == QtWidgets.QMessageBox.Cancel:
                # Abort
                return 1
            elif result == QtWidgets.QMessageBox.Discard:
                # Continue without saving
                return 0

        # Save the map
        self.save_header()
        new_map_mem = mapped.map_to_mem(self.map_data.tilemap)
        pos = self.map_data.tilemap_ptr
        size = len(new_map_mem)
        self.game.rom_contents[pos:pos+size] = new_map_mem
        self.map_modified = False
        return 0

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
        self.ui.PalTab.setEnabled(False)
        self.ui.eventsTab.setEnabled(False)
        self.ui.HeaderTab.setEnabled(False)
        self.loaded_map = False
        self.load_map(self.map_data.bank_n, self.map_data.map_n)
        self.ui.statusbar.showMessage("Loaded {}".format(fn))

    def write_to_file(self):
        if self.loaded_map:
            if self.map_modified:
                self.save_map(confirm=False)
            elif self.blocks_modified:
                self.save_blocks(confirm=False)
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
        if self.map_data.events_header['self'] == 0:
            addr = mapped.create_event_header(self.game.rom_contents)
            self.map_data.events_header['self'] = addr
            self.map_data.header['event_data_ptr'] = addr
            self.update_header()
            self.save_header()

        self.save_events()
        mapped.add_event(self.game.rom_contents, self.map_data.events_header, type)
        mapped.write_events_header(self.game.rom_contents,
                                   self.map_data.events_header)
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
        if this_event is None or type is None:
            print("FIXME: deleting event with no event selected")
            return

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
            self.event_n = int(spin.value())
        except IndexError:
            event = events[0]
            self.event_n = 0
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

    def selected_palette_changed(self):
        self.selected_pal = self.ui.paletteSelectorCombo.currentIndex()
        self.print_tileset()
        self.print_preview_tile()

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
        print(args)
        import subprocess
        subprocess.Popen(args)

    def select_script_editor(self):
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                      'Choose script editor executable',
                                                      QtCore.QDir.homePath(),
                                                      "All files (*)")
        if not fn:
            return
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
        oldnum = len(self.game.banks)
        num, ok = QtWidgets.QInputDialog.getInt(self, 'How many?', # Title
                                                "How many?", # Label
                                                1, 1, (256 - oldnum)) # Default, min, max
        if not ok:
            return
        ptr = mapped.add_banks(self.game.rom_contents, self.game.rom_data["MapHeaders"],
                               oldnum, oldnum+num)
        mapped.write_rom_ptr_at(self.game.rom_contents,
                                self.game.rom_data["MapHeaders"], ptr)
        self.load_banks()

    def close_rom_confirm(self):
        if self.map_modified or self.blocks_modified or \
                self.game.rom_contents != self.game.original_rom_contents:
            result = self.confirm_saving_dialog('Changes not saved',
                                                'The buffer contains unsaved data.\n'
                                                'Would you like to write the changes to your rom?',
                                                detailed=False)
            if result == QtWidgets.QMessageBox.Save:
                self.ui.menubar.setEnabled(False)
                self.ui.centralwidget.setEnabled(False)
                self.write_to_file()
            elif result == QtWidgets.QMessageBox.Cancel:
                return 1
        return 0

    def closeEvent(self, event):
        if self.close_rom_confirm():
            event.ignore()
            return
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
    #win.close()
    app.deleteLater()
    sys.exit(r)

if __name__ == "__main__":
    main()

