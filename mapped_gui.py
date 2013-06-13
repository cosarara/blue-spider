#!/usr/bin/env python3

import sys
from PyQt4 import Qt, QtCore, QtGui
from window import Ui_MainWindow
import qmapview

import mapped
import structures


try:
    from PIL import Image, ImageQt
except:
    import Image
    import ImageQt


class Window(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.treemodel = QtGui.QStandardItemModel()
        self.ui.treeView.setModel(self.treemodel)

        self.map_scene = QtGui.QGraphicsScene()
        self.ui.map.setScene(self.map_scene)
        self.mov_scene = QtGui.QGraphicsScene()
        self.ui.movPermissionsMap.setScene(self.mov_scene)
        self.event_scene = QtGui.QGraphicsScene()
        self.ui.eventMap.setScene(self.event_scene)
        self.palette_scene = QtGui.QGraphicsScene()
        self.ui.palette.setScene(self.palette_scene)
        self.perms_palette_scene = QtGui.QGraphicsScene()
        self.ui.MovPermissionsPalette.setScene(self.perms_palette_scene)
        
        self.t1_header = None
        self.t1_img = None
        self.t2_header = None

        self.ui.actionLoad_ROM.triggered.connect(self.load_rom)
        self.ui.actionSave.triggered.connect(self.save_map)
        self.ui.treeView.clicked.connect(self.load_map)
        self.ui.s_type.currentIndexChanged.connect(
                self.update_signpost_stacked)
        self.ui.p_edit_script.clicked.connect(self.launch_script_editor)
        self.ui.s_edit_script.clicked.connect(self.launch_script_editor)
        self.ui.t_edit_script.clicked.connect(self.launch_script_editor)

        self.selected_tile = 0
        self.selected_mov_tile = 0
        self.selected_event = None
        self.selected_event_type = None
        self.rom_file_name = None
        # RS or FR
        self.game = None
        self.rom_code = None
        self.rom_data = None
        self.mov_perms_imgs = None

        hex_update = lambda x : (lambda n : x(hex(n)[2:]))
        hex_read = lambda x : (lambda : int(x(), 16))
        bool_update = lambda x : (lambda n : x(bool(n)))
        bool_read = lambda x : (lambda : int(x()))
        combo_update = lambda x : (lambda n : print(n)or x(int(n)))
        combo_read = lambda x : (lambda : print(x()) or int(x()))

        text_element = lambda name, obj : (
                        (
                            hex_read(obj.text),
                            hex_update(obj.setText),
                            name 
                        )
                      )

        self.ui_event_connections = {
                'person': (
                        text_element("script_ptr", self.ui.p_script_offset),
                        text_element("person_num", self.ui.person_num),
                        text_element("sprite_num", self.ui.sprite_num),
                        text_element("x", self.ui.p_x),
                        text_element("y", self.ui.p_y),
                        text_element("flag", self.ui.p_flag),
                        text_element("radius", self.ui.p_view_radius),
                        text_element("mov", self.ui.p_mov),
                        text_element("unknown1", self.ui.p_unknown1),
                        text_element("unknown2", self.ui.p_unknown2),
                        text_element("unknown3", self.ui.p_unknown3),
                        text_element("unknown4", self.ui.p_unknown4),
                        text_element("unknown5", self.ui.p_unknown5),
                        text_element("unknown6", self.ui.p_unknown6),
                        text_element("unknown7", self.ui.p_unknown7),
                        (
                            combo_read(self.ui.p_mov_type.currentIndex),
                            combo_update(self.ui.p_mov_type.setCurrentIndex),
                            "mov_type"
                        ),
                        (
                            bool_read(self.ui.is_a_trainer.isChecked),
                            bool_update(self.ui.is_a_trainer.setChecked),
                            "is_a_trainer"
                        ),
                    ),
                'warp': (
                        text_element("x", self.ui.w_x),
                        text_element("y", self.ui.w_y),
                        text_element("unknown", self.ui.w_unknown1),
                        text_element("warp_num", self.ui.w_warp_n),
                        text_element("bank_num", self.ui.w_bank_n),
                        text_element("map_num", self.ui.w_map_n),
                    ),
                "trigger": (
                        text_element("x", self.ui.t_x),
                        text_element("y", self.ui.t_y),
                        text_element("unknown1", self.ui.t_unknown1),
                        text_element("unknown2", self.ui.t_unknown2),
                        text_element("unknown3", self.ui.t_unknown3),
                        text_element("var_num", self.ui.t_var_num),
                        text_element("var_value", self.ui.t_var_val),
                        text_element("script_ptr", self.ui.t_script_offset),
                    ),
                "signpost": (
                        text_element("x", self.ui.s_x),
                        text_element("y", self.ui.s_y),
                        (
                            combo_read(self.ui.s_talking_level.currentIndex),
                            combo_update(self.ui.s_talking_level.setCurrentIndex),
                            "talking_level"
                        ),
                        (
                            combo_read(self.ui.s_type.currentIndex),
                            combo_update(self.ui.s_type.setCurrentIndex),
                            "type"
                        ),
                        text_element("unknown1", self.ui.s_unknown1),
                        text_element("unknown2", self.ui.s_unknown2),
                        text_element("script_ptr", self.ui.s_script_offset),
                        text_element("item_number", self.ui.s_item_id),
                        text_element("hidden_item_id", self.ui.s_hidden_id),
                        text_element("ammount", self.ui.s_ammount),
                    )
            }
            
        self.script_editor_command = '../asc/git/asc_gui_qt.py'




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

    def load_maps(self, bank_num):
        maps = mapped.get_map_headers(self.rom_contents, bank_num, self.banks)

        for i, map, in enumerate(maps):
            self.treemodel.item(bank_num).appendRow(
                    QtGui.QStandardItem(hex(i) + " - " + hex(map))
                    )

    def load_tileset(self, tileset_header, previous_img=None):
        tileset_img = mapped.get_tileset_img(self.rom_contents, tileset_header)
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
        block_data_mem = mapped.get_block_data(self.rom_contents,
                                               tileset_header, self.game)
        blocks_imgs = mapped.build_block_imgs(block_data_mem, tileset_img)
        self.blocks_imgs += blocks_imgs
        return tileset_img

    def draw_palette(self):
        # The tile palette, not the color one
        blocks_imgs = self.blocks_imgs
        perms_imgs = self.mov_perms_imgs
        blocks_img_w = 16 * 8 # 8 tiles per row
        perms_img_w = blocks_img_w
        blocks_img_h = (len(blocks_imgs) * 16) // 8
        perms_img_h = (len(perms_imgs) * 16) // 8
        blocks_img = Image.new("RGB", (blocks_img_w, blocks_img_h))
        perms_img = Image.new("RGB", (perms_img_w, perms_img_h))
        i = 0
        for row in range(blocks_img_h // 16):
            for col in range(blocks_img_w // 16):
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

        self.tilesetPixMap = QtGui.QPixmap.fromImage(self.t1_img_qt)
        self.permsPalPixMap = QtGui.QPixmap.fromImage(self.perms_pal_img_qt)
        self.palette_scene.clear()
        self.perms_palette_scene.clear()
        self.palette_pixmap_qobject = qmapview.QMapPixmap(self.tilesetPixMap)
        self.perms_palette_pixmap_qobject = qmapview.QMapPixmap(self.permsPalPixMap)
        self.palette_scene.addItem(self.palette_pixmap_qobject)
        self.perms_palette_scene.addItem(self.perms_palette_pixmap_qobject)
        self.palette_scene.update()
        self.perms_palette_scene.update()
        self.palette_pixmap_qobject.clicked.connect(self.palette_clicked)
        self.perms_palette_pixmap_qobject.clicked.connect(self.perms_palette_clicked)
        #self.ui.palette.fitInView(self.palette_scene.sceneRect(), mode=QtCore.Qt.KeepAspectRatio)

    def draw_map(self, map):
        #print(map)
        w = len(map[0])
        h = len(map)
        map_img = Image.new("RGB", (w*16, h*16))
        mov_img = Image.new("RGB", (w*16, h*16))
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
                mov_img.paste(self.blocks_imgs[tile_num], pos)
                mov_img.paste(self.mov_perms_imgs[behavior], pos, self.mov_perms_imgs[behavior])

        self.map_img = map_img
        self.map_img_qt = ImageQt.ImageQt(map_img)
        self.mov_img_qt = ImageQt.ImageQt(mov_img)
        self.mapPixMap = QtGui.QPixmap.fromImage(self.map_img_qt)
        self.movPixMap = QtGui.QPixmap.fromImage(self.mov_img_qt)
        self.map_scene.clear()
        self.mov_scene.clear()
        self.map_pixmap_qobject = qmapview.QMapPixmap(self.mapPixMap)
        self.mov_pixmap_qobject = qmapview.QMapPixmap(self.movPixMap)
        self.map_scene.addItem(self.map_pixmap_qobject)
        self.mov_scene.addItem(self.mov_pixmap_qobject)
        self.map_scene.update()
        self.mov_scene.update()

        self.map_pixmap_qobject.clicked.connect(self.map_clicked)
        self.mov_pixmap_qobject.clicked.connect(self.mov_clicked)

    def draw_events(self, events):
        event_img = self.map_img.copy()
        person_events, warp_events, trigger_events, signpost_events = events
        event_imgs = mapped.get_imgs(["data", "events"], 4)
        person_img, warp_img, trigger_img, signpost_img = event_imgs
        event_types = (
                (person_events, person_img),
                (warp_events, warp_img),
                (trigger_events, trigger_img),
                (signpost_events, signpost_img)
            )
        for event_type in event_types:
            data, img = event_type
            for event in data:
                if not event: # Some events aren't parsed yet
                    continue
                x = event['x']
                y = event['y']
                x = x*16
                y = y*16
                x2 = x+16
                y2 = y+16
                pos = (x, y, x2, y2)
                event_img.paste(img, pos, img)
        self.event_img_qt = ImageQt.ImageQt(event_img)
        self.eventPixMap = QtGui.QPixmap.fromImage(self.event_img_qt)
        self.event_scene.clear()
        self.event_pixmap_qobject = qmapview.QMapPixmap(self.eventPixMap)
        self.event_scene.addItem(self.event_pixmap_qobject)
        self.event_scene.update()
        self.event_pixmap_qobject.clicked.connect(self.event_clicked)

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
        if tileset_header != self.t1_header:
            self.blocks_imgs = []
            t1_img = self.load_tileset(tileset_header)
            self.load_tileset(tileset2_header, t1_img)
        else:
            t1_img = self.t1_img
            if tileset2_header != self.t2_header:
                if self.game == 'RS':
                    num_of_blocks = 512
                else:
                    num_of_blocks = 640
                self.blocks_imgs = self.blocks_imgs[:num_of_blocks]
                self.load_tileset(tileset2_header, t1_img)
        self.t1_img = t1_img
        self.t1_header = tileset_header
        self.t2_header = tileset2_header

        self.mov_perms_imgs = mapped.get_imgs()
        events_header = mapped.parse_events_header(self.rom_contents,
                map_header['event_data_ptr'])
        self.ui.num_of_warps.setText(str(events_header['n_of_warps']))
        self.ui.num_of_people.setText(str(events_header['n_of_people']))
        self.ui.num_of_triggers.setText(str(events_header['n_of_triggers']))
        self.ui.num_of_signposts.setText(str(events_header['n_of_signposts']))
        self.events = mapped.parse_events(self.rom_contents, events_header)

        map_size = map_data_header['w'] * map_data_header['h'] * 2 # Every tile is 2 bytes
        tilemap_ptr = map_data_header['tilemap_ptr']
        self.tilemap_ptr = tilemap_ptr
        map_mem = self.rom_contents[tilemap_ptr:tilemap_ptr+map_size]
        self.map = mapped.parse_map_mem(map_mem, map_data_header['w'], map_data_header['h'])

        self.draw_map(self.map)
        self.draw_palette()
        self.draw_events(self.events)

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

    def get_event_at_pos_from_list(self, pos, events):
        x, y = pos
        for event in events:
            if event['x'] == x and event['y'] == y:
                return event
        return None

    def get_event_at_pos(self, pos):
        person_events, warp_events, trigger_events, signpost_events = self.events
        #events = person_events + warp_events + trigger_events + signpost_events
        types = (
                ("person", person_events),
                ("warp", warp_events),
                ("trigger", trigger_events),
                ("signpost", signpost_events)
            )
        # haha, reserved names
        for type, list in types:
            event = self.get_event_at_pos_from_list(pos, list)
            if event:
                return type, event
        x, y = pos
        print(x, y)
        return None, None

    def get_event_from_mouseclick(self, event, pixmap):
        pos = event.pos()
        x = int(pos.x())
        y = int(pos.y())
        w = pixmap.width()
        h = pixmap.height()
        tile_size = 16
        tiles_per_row = w // tile_size
        tile_x = x // tile_size
        tile_y = y // tile_size
        event = self.get_event_at_pos((tile_x, tile_y))
        return event, tile_x, tile_y

    def update_event_editor(self, event, type):
        if not type or not event:
            return
        if type == "person":
            self.ui.eventsStackedWidget.setCurrentIndex(2)
        elif type == "warp":
            self.ui.eventsStackedWidget.setCurrentIndex(1)
        elif type == "trigger":
            self.ui.eventsStackedWidget.setCurrentIndex(3)
        elif type == "signpost":
            self.ui.eventsStackedWidget.setCurrentIndex(4)

        for connection in self.ui_event_connections[type]:
            read_function, update_function, data_element = connection
            update_function(event[data_element])
            #print(update_function, event[data_element], data_element)
            #self.ui.p_script_offset.setText(hex(event["script_ptr"])[2:])
        self.selected_event = event
        self.selected_event_type = type
        #print(dir(self.ui.eventsStackedWidget))


    def save_event_to_memory(self):
        '''take event info from UI and save it in the events object'''
        #self.selected_event[''] = None
        type = self.selected_event_type
        if not type or not self.selected_event:
            return
        for connection in self.ui_event_connections[type]:
            read_function, update_function, data_element = connection
            num = read_function()
            structure = structures.to_dict(structures.events[type])
            if data_element in structure:
                size = structure[data_element][0]
            else: # Bah, don't check it (it'll apply only to signposts)
                size = "long"
            if not mapped.fits(num, size):
                raise Exception(data_element + " too big")
            self.selected_event[data_element] = num

    def map_clicked(self, event):
        #print(event)
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(event, self.mapPixMap)
        print("clicked tile:", hex(tile_num))
        self.map[tile_y][tile_x][0] = self.selected_tile
        self.draw_map(self.map)

    def mov_clicked(self, event):
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(event, self.movPixMap)
        print("clicked tile:", hex(tile_num))
        self.map[tile_y][tile_x][1] = self.selected_mov_tile
        self.draw_map(self.map)

    def event_clicked(self, event):
        #print(event)
        self.save_event_to_memory()
        event, event_x, event_y = self.get_event_from_mouseclick(event, self.eventPixMap)
        print("clicked event tile:", event)
        type, event = event
        #self.map[tile_y][tile_x][0] = self.selected_tile
        self.draw_events(self.events)
        self.update_event_editor(event, type)

    def palette_clicked(self, event):
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(event, self.tilesetPixMap)
        print("selected tile:", hex(tile_num))
        self.selected_tile = tile_num

    def perms_palette_clicked(self, event):
        tile_num, tile_x, tile_y = self.get_tile_num_from_mouseclick(event, self.permsPalPixMap)
        print("selected tile:", hex(tile_num))
        self.selected_mov_tile = tile_num

    def save_events(self):
        person_events, warp_events, trigger_events, signpost_events = self.events
        types = (
                ("person", person_events),
                ("warp", warp_events),
                ("trigger", trigger_events),
                ("signpost", signpost_events)
            )
        for type, list in types:
            for event in list:
                mapped.write_event(self.rom_contents, event, type)

    def save_map(self):
        new_map_mem = mapped.map_to_mem(self.map)
        #print(self.map)
        pos = self.tilemap_ptr
        size = len(new_map_mem)
        self.rom_contents = bytearray(self.rom_contents)
        self.rom_contents[pos:pos+size] = new_map_mem
        self.save_events()
        self.write_rom()

    def update_signpost_stacked(self):
        if self.ui.s_type.currentIndex() < 5:
            self.ui.signpost_stacked.setCurrentIndex(0)
        else:
            self.ui.signpost_stacked.setCurrentIndex(1)

    def launch_script_editor(self, offset=None, file_name=None, command=None):
        if not command:
            command = self.script_editor_command
        if not file_name:
            file_name = self.rom_file_name
        if not offset:
            offset = self.selected_event['script_ptr']
        import subprocess
        subprocess.Popen([command, file_name, hex(offset)])


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = Window()
    win.show()
    r = app.exec_() # So yeah, I'm trying to make it not crash on exit
    win.close()
    app.deleteLater()
    sys.exit(r)
    #sys.exit(app.exec_())


