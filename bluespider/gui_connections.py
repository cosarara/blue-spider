# -*- coding: utf-8 -*-
import ast

from . import structures
from . import structure_utils
from . import mapped

num_read = lambda x: (lambda: ast.literal_eval(x()) if x() else None)

hex_update = lambda x: (lambda n: x(hex(n)))
hex_read = lambda x: (lambda: int(x(), 16))
bool_update = lambda x: (lambda n: x(bool(n)))
bool_read = lambda x: (lambda: int(x()))
combo_update = lambda x: (lambda n: x(int(n)))
combo_read = lambda x: (lambda: int(x()))

text_element = lambda name, obj: (
    (
        #hex_read(obj.text),
        num_read(obj.text),
        hex_update(obj.setText),
        name
    )
)

def make_header_connections(self):
    ui = self.ui
    conns = {
        structures.map_header: (
            text_element("map_data_ptr", ui.m_data_ptr),
            text_element("event_data_ptr", ui.e_data_ptr),
            text_element("level_script_ptr", ui.ls_ptr),
            text_element("connections_ptr", ui.con_data_ptr),
            text_element("song_index", ui.song_index),
            text_element("map_ptr_index", ui.m_ptr_index),
            text_element("label_index", ui.label_index),
            (
                bool_read(ui.is_cave.isChecked),
                bool_update(ui.is_cave.setChecked),
                "is_a_cave"
            ),
            text_element("weather", ui.weather_type),
            text_element("map_type", ui.map_type),
            (
                bool_read(ui.show_label.isChecked),
                bool_update(ui.show_label.setChecked),
                "show_label"
            ),
            text_element("battle_type", ui.battle_type),
            ),
        structures.map_data: (
            text_element("h", ui.map_h),
            text_element("w", ui.map_w),
            text_element("border_ptr", ui.border_info_ptr),
            text_element("tilemap_ptr", ui.tilemap_ptr),
            text_element("global_tileset_ptr", ui.t1_ptr),
            text_element("local_tileset_ptr", ui.t2_ptr),
            )
        }
    def update():
        for t, d in ((structures.map_header, self.map_data.header),
                     (structures.map_data, self.map_data.data_header)):
            for connection in conns[t]:
                read_function, update_function, data_element = connection
                update_function(d[data_element])

    def save_to_mem():
        for t, d in ((structures.map_header, self.map_data.header),
                     (structures.map_data, self.map_data.data_header)):
            for connection in conns[t]:
                read_function, update_function, data_element = connection
                num = read_function()
                structure = structure_utils.to_dict(t)
                if data_element in structure:
                    size = structure[data_element][0]
                else: # Bah, don't check it (it'll apply only to signposts)
                    size = "u32"
                if not mapped.fits(num, size):
                    raise Exception(data_element + " too big")
                if size == "ptr" and num < 0x8000000 and num != 0:
                    num |= 0x8000000
                d[data_element] = num

        mapped.write_map_header(self.game.rom_contents, self.map_data.header)
        mapped.write_map_data_header(self.game.rom_contents, self.map_data.data_header)
    return update, save_to_mem


def get_event_connections(ui):
    return {
        'person': (
            text_element("script_ptr", ui.p_script_offset),
            text_element("person_num", ui.person_num),
            (
                ui.sprite_num.value,
                ui.sprite_num.setValue,
                "sprite_num"
            ),
            #text_element("sprite_num", ui.sprite_num),
            text_element("x", ui.p_x),
            text_element("y", ui.p_y),
            text_element("flag", ui.p_flag),
            text_element("radius", ui.p_view_radius),
            text_element("mov", ui.p_mov),
            text_element("unknown1", ui.p_unknown1),
            text_element("unknown2", ui.p_unknown2),
            text_element("unknown3", ui.p_unknown3),
            text_element("unknown4", ui.p_unknown4),
            text_element("unknown5", ui.p_unknown5),
            text_element("unknown6", ui.p_unknown6),
            text_element("unknown7", ui.p_unknown7),
            (
                combo_read(ui.p_mov_type.currentIndex),
                combo_update(ui.p_mov_type.setCurrentIndex),
                "mov_type"
            ),
            text_element("is_a_trainer", ui.is_a_trainer),
        ),
        'warp': (
            text_element("x", ui.w_x),
            text_element("y", ui.w_y),
            text_element("unknown", ui.w_unknown1),
            text_element("warp_num", ui.w_warp_n),
            text_element("bank_num", ui.w_bank_n),
            text_element("map_num", ui.w_map_n),
        ),
        "trigger": (
            text_element("x", ui.t_x),
            text_element("y", ui.t_y),
            text_element("unknown1", ui.t_unknown1),
            text_element("unknown2", ui.t_unknown2),
            text_element("unknown3", ui.t_unknown3),
            text_element("var_num", ui.t_var_num),
            text_element("var_value", ui.t_var_val),
            text_element("script_ptr", ui.t_script_offset),
        ),
        "signpost": (
            text_element("x", ui.s_x),
            text_element("y", ui.s_y),
            (
                combo_read(ui.s_talking_level.currentIndex),
                combo_update(ui.s_talking_level.setCurrentIndex),
                "talking_level"
            ),
            (
                combo_read(ui.s_type.currentIndex),
                combo_update(ui.s_type.setCurrentIndex),
                "type"
            ),
            text_element("unknown1", ui.s_unknown1),
            text_element("unknown2", ui.s_unknown2),
            text_element("script_ptr", ui.s_script_offset),
            text_element("item_number", ui.s_item_id),
            text_element("hidden_item_id", ui.s_hidden_id),
            text_element("amount", ui.s_amount),
        )
    }
