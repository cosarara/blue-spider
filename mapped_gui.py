#!/usr/bin/env python3

import sys
from PyQt4 import Qt, QtCore, QtGui
from window import Ui_MainWindow
import qmapview

import mapped

#MapHeaders      = 0x53324
#Maps            = 0x5326C
#MapLabels       = 0xFBFE0

#get_addr = lambda x : int.from_bytes(x, "little")
#
#def get_rom_addr(x): # Safer and more useful version
#    a = int.from_bytes(x, "little")
#    if a & 0x8000000 == 0x8000000:
#        return a & 0xFFFFFF
#    else:
#        return -1

from PIL import Image, ImageQt


class Window(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.treemodel = QtGui.QStandardItemModel()
        self.ui.treeView.setModel(self.treemodel)

        self.map_scene = QtGui.QGraphicsScene()
        self.ui.map.setScene(self.map_scene)
        #self.map_pixmap = QtGui.QPixmap()
        #self.
        self.palette_scene = QtGui.QGraphicsScene()
        self.ui.palette.setScene(self.palette_scene)
        self.map_scene = QtGui.QGraphicsScene()
        self.ui.map.setScene(self.map_scene)

        #self.treemodel.setItem(0, QtGui.QStandardItem("first"))
        #self.treemodel.setItem(1, QtGui.QStandardItem("seccond"))
        #self.treemodel.item(1).appendRow(QtGui.QStandardItem("seccond child"))

        #QtCore.QObject.connect(self.ui.actionLoad_ROM,
        #                       QtCore.SIGNAL("triggered()"),
        #                       self.load_rom)
        self.ui.actionLoad_ROM.triggered.connect(self.load_rom)
        self.ui.actionSave.triggered.connect(self.save_map)
        self.ui.treeView.clicked.connect(self.load_map)

        self.selected_tile = 0
        self.rom_file_name = None
        # RS or FR
        self.game = None
        self.rom_code = None
        self.rom_data = None


    def load_rom(self):
        self.treemodel.clear()
        self.banks = []
        fn = QtGui.QFileDialog.getOpenFileName(self, 'Open ROM file', 
                                               QtCore.QDir.homePath(),
                                               "GBA ROM (*.gba);;"
                                               "All files (*)")

        if not fn:
            return
        with open(fn, "rb") as rom_file:
            self.rom_contents = rom_file.read()

        self.rom_file_name = fn
        self.rom_code = self.rom_contents[0xAC:0xAC+4]
        if self.rom_code == b'AXVE':
            self.rom_data = mapped.axve
            self.game = 'RS'
        elif self.rom_code == b'BPRE':
            self.rom_data = mapped.bpre
            self.game = 'FR'
        else:
            raise Exception("ROM code not found")

        self.load_banks()

    def write_rom(self):
        if not self.rom_file_name:
            # TODO: ERROR, no ROM selected
            return
        with open(self.rom_file_name, "wb") as rom_file:
            rom_file.write(self.rom_contents)

    def load_banks(self):
        self.banks = mapped.get_banks(self.rom_contents, self.rom_data)
        for i, bank in enumerate(self.banks):
            self.treemodel.appendRow(QtGui.QStandardItem(hex(i) + " - " + hex(bank)))
            self.load_maps(i)
            #self.treemodel.setItem(1, QtGui.QStandardItem("seccond"))
            #self.treemodel.item(1).appendRow(QtGui.QStandardItem("seccond child"))

    def load_maps(self, bank_num):
        maps = mapped.get_map_headers(self.rom_contents, bank_num, self.banks)

        for i, map, in enumerate(maps):
            self.treemodel.item(bank_num).appendRow(
                    QtGui.QStandardItem(hex(i) + " - " + hex(map))
                    )
        #print(self.treemodel.item(0).child(9).text())

    def load_tileset(self, tileset_header, previous_img=None):
        #print(tileset_header)
        tileset_img = mapped.get_tileset_img(self.rom_contents, tileset_header)
        if previous_img:
            w = previous_img.size[0]
            h = previous_img.size[1] + tileset_img.size[1]
            #print("big_img_size", w, h)
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
        block_data_mem = mapped.parse_block_data(self.rom_contents, tileset_header, self.game)
        blocks_imgs = mapped.build_block_imgs(block_data_mem, tileset_img)
        #dummy_img = Image.new("RGB", (16, 16))
        #blocks_imgs += [dummy_img] * 512
        self.blocks_imgs += blocks_imgs
        return tileset_img

    def draw_palette(self):
        # The tile palette, not the color one
        blocks_imgs = self.blocks_imgs
        #print("len", len(blocks_imgs))
        #blocks_img_w = (len(blocks_imgs) // 8) * 16
        blocks_img_w = 16 * 8 # 8 tiles per row
        #print("w", blocks_img_w)
        blocks_img_h = (len(blocks_imgs) * 16) // 8
        #print("h", blocks_img_h)
        blocks_img = Image.new("RGB", (blocks_img_w, blocks_img_h))
        i = 0
        for row in range(blocks_img_h // 16):
            for col in range(blocks_img_w // 16):
                x = col*16
                y = row*16
                x2 = x+16
                y2 = y+16
                pos = (x, y, x2, y2)
                block_img = blocks_imgs[i]
                blocks_img.paste(block_img, pos)
                i += 1

        #self.t1_img_qt = ImageQt.ImageQt(tileset1_img)
        #self.t1_img_qt = ImageQt.ImageQt(blocks_imgs[map_n])
        blocks_img.save("tpalette.png", "PNG")
        self.t1_img_qt = ImageQt.ImageQt(blocks_img)

        self.tilesetPixMap = QtGui.QPixmap.fromImage(self.t1_img_qt)
        self.palette_scene.clear()
        self.palette_pixmap_qobject = qmapview.QMapPixmap(self.tilesetPixMap)
        self.palette_scene.addItem(self.palette_pixmap_qobject)
        #self.palette_scene.addPixmap(self.tilesetPixMap)
        self.palette_scene.update()
        self.palette_pixmap_qobject.clicked.connect(self.palette_clicked)
        #self.ui.palette.fitInView(self.palette_scene.sceneRect(), mode=QtCore.Qt.KeepAspectRatio)

    def draw_map(self, map):
        #print(map)
        w = len(map[0])
        h = len(map)
        map_img = Image.new("RGB", (w*16, h*16))
        for row in range(h):
            for tile in range(w):
                tile_num, behavior = map[row][tile]
                #print("a", tile_num, behavior)

                x = tile*16
                y = row*16
                x2 = x+16
                y2 = y+16
                pos = (x, y, x2, y2)

                #print(tile_num, len(self.blocks_imgs))
                map_img.paste(self.blocks_imgs[tile_num], pos)

        self.map_img_qt = ImageQt.ImageQt(map_img)
        self.mapPixMap = QtGui.QPixmap.fromImage(self.map_img_qt)
        self.map_scene.clear()
        self.map_pixmap_qobject = qmapview.QMapPixmap(self.mapPixMap)
        self.map_scene.addItem(self.map_pixmap_qobject)
        #self.mapPixMapItem = self.map_scene.addPixmap(self.mapPixMap)
        #self.mapPixMapItem.mousePressEvent = lambda event : print("asdf!", event.x(), event.y())
        self.map_scene.update()

        self.map_pixmap_qobject.clicked.connect(self.map_clicked)


    def load_map(self, qindex):
        bank_n = qindex.parent().row()
        self.bank_n = bank_n
        if bank_n == -1:
            return
        map_n = qindex.row()
        self.map_n = map_n
        print(bank_n, map_n)
        maps = mapped.get_map_headers(self.rom_contents, bank_n, self.banks)
        map_h_ptr = maps[map_n]
        map_header = mapped.parse_map_header(self.rom_contents, map_h_ptr)
        map_data_header = mapped.parse_map_data(
                self.rom_contents, map_header['map_data_ptr'],
                self.game
                )

        self.blocks_imgs = []

        tileset_header = mapped.parse_tileset_header(
                self.rom_contents,
                map_data_header['global_tileset_ptr'],
                self.game
                )
        tileset2_header = mapped.parse_tileset_header(
                self.rom_contents,
                map_data_header['local_tileset_ptr'],
                self.game
                )
        t1_img = self.load_tileset(tileset_header)
        self.load_tileset(tileset2_header, t1_img)

        map_size = map_data_header['w'] * map_data_header['h'] * 2 # Every tile is 2 bytes
        tilemap_ptr = map_data_header['tilemap_ptr']
        self.tilemap_ptr = tilemap_ptr
        map_mem = self.rom_contents[tilemap_ptr:tilemap_ptr+map_size]
        self.map = mapped.parse_map_mem(map_mem, map_data_header['w'], map_data_header['h'])

        self.draw_map(self.map)
        self.draw_palette()

    def get_tile_num_from_mouseclick(self, event, pixmap):
        pos = event.pos()
        x = int(pos.x())
        y = int(pos.y())
        w = pixmap.width()
        h = pixmap.height()
        tile_size = 16
        tiles_per_row = w // tile_size
        tile_x = x // tile_size
        tile_y = y // tile_size
        tile_num = tile_x + tile_y * tiles_per_row
        return tile_num, tile_x, tile_y

    def map_clicked(self, event):
        #print(event)
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(event, self.mapPixMap)
        print("clicked tile:", hex(tile_num))
        self.map[tile_y][tile_x][0] = self.selected_tile
        self.draw_map(self.map)

    def palette_clicked(self, event):
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(event, self.tilesetPixMap)
        print("selected tile:", hex(tile_num))
        self.selected_tile = tile_num

    def save_map(self):
        new_map_mem = mapped.map_to_mem(self.map)
        print(self.map)
        pos = self.tilemap_ptr
        size = len(new_map_mem)
        self.rom_contents = bytearray(self.rom_contents)
        self.rom_contents[pos:pos+size] = new_map_mem
        self.write_rom()




if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = Window()
    win.show()
    r = app.exec_()
    app.deleteLater() # Avoid errors on exit
    sys.exit(r)
    #sys.exit(app.exec_())


