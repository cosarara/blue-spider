# -*- coding: utf-8 -*-

from .structure_utils import u8, u16, u32, s32, ptr
from .structure_utils import calculate_offsets as c

map_header = c(
    ("map_data_ptr", ptr),
    ("event_data_ptr", ptr),
    ("level_script_ptr", ptr),
    ("connections_ptr", ptr),
    ("song_index", u16),
    ("map_ptr_index", u16),
    ("label_index", u8),
    ("is_a_cave", u8),
    ("weather", u8),
    ("map_type", u8),
    ("null", u16), # Unknown at 24-25
    ("show_label", u8),
    ("battle_type", u8),
)

map_data = c(
    ("w", u32),
    ("h", u32),
    ("border_ptr", ptr),
    ("tilemap_ptr", ptr),
    ("global_tileset_ptr", ptr),
    ("local_tileset_ptr", ptr),
    # FR only
    ("border_w", u8),
    ("border_h", u8)
)

connections_header = c(
    ("n_of_connections", u32),
    ("connection_data_ptr", ptr)
)

connection_data = c(
    ("direction", u32),
    ("offset", s32),
    ("bank_num", u8),
    ("map_num", u8),
    ("null", u16)
)

tileset_header_base = (
    ("is_compressed", u8),
    ("tileset_type", u8),
    ("null", u16), # 0000
    ("tileset_image_ptr", ptr),
    ("palettes_ptr", ptr),
    ("block_data_ptr", ptr),
)

tileset_header_rs = c(*(tileset_header_base + (
    ("behavior_data_ptr", ptr),
    ("animation_data_ptr", ptr),
)))

tileset_header_fr = c(*(tileset_header_base + (
    ("animation_data_ptr", ptr),
    ("behavior_data_ptr", ptr),
)))

events_header = c(
    ("n_of_people", u8),
    ("n_of_warps", u8),
    ("n_of_triggers", u8),
    ("n_of_signposts", u8),
    ("person_events_ptr", ptr),
    ("warp_events_ptr", ptr),
    ("trigger_events_ptr", ptr),
    ("signpost_events_ptr", ptr)
)

person_event = c(
    ("person_num", u8),
    ("sprite_num", u8),
    ("unknown1", u8),
    ("unknown2", u8),
    ("x", u16),
    ("y", u16),
    ("unknown3", u8),
    ("mov_type", u8),
    ("mov", u8),
    ("unknown4", u8),
    ("is_a_trainer", u8),
    ("unknown5", u8),
    ("radius", u16),
    ("script_ptr", ptr),
    ("flag", u16),
    ("unknown6", u8),
    ("unknown7", u8),
)

warp_event = c(
    ("x", u16),
    ("y", u16),
    ("unknown", u8),
    ("warp_num", u8),
    ("map_num", u8),
    ("bank_num", u8),
)

trigger_event = c(
    ("x", u16),
    ("y", u16),
    ("unknown1", u16),
    ("var_num", u16),
    ("var_value", u16),
    ("unknown2", u8),
    ("unknown3", u8),
    ("script_ptr", ptr),
)

signpost_event = c(
    ("x", u16),
    ("y", u16),
    ("talking_level", u8),
    ("type", u8),
    ("unknown1", u8),
    ("unknown2", u8),
)

events = {
    "person": person_event,
    "trigger": trigger_event,
    "warp": warp_event,
    "signpost": signpost_event
}

sprite = (
    ("clear", "u16", 0), # FFFF
    ("palette_num", "u8", 2),
    ("width", "u16", 8),
    ("heigth", "u16", 10),
    ("header2_ptr", "ptr", 28),
)

sprite2 = c(
    ("img_ptr", ptr), # Yes it makes no sense
)

lscript_entry = c(
    ("type", u8),
    ("script_header_ptr", ptr),
)
# List of entries ends in 0x00

# type 2 or 4, doesn't matter
lscript_type_2 = c(
    ("flag", u16),
    ("value", u16),
    ("script_body_ptr", ptr),
    ("null", u16), # 0000
)

