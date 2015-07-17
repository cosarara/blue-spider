# -*- coding: utf8 -*-

map_header = (
    ("map_data_ptr", "ptr", 0),
    ("event_data_ptr", "ptr", 4),
    ("level_script_ptr", "ptr", 8),
    ("connections_ptr", "ptr", 12),
    ("song_index", "u16", 16),
    ("map_ptr_index", "u16", 18),
    ("label_index", "u8", 20),
    ("is_a_cave", "u8", 21),
    ("weather", "u8", 22),
    ("map_type", "u8", 23),
    ("null", "u16", 24), # Unknown at 24-25
    ("show_label", "u8", 26),
    ("battle_type", "u8", 27),
)

map_data = (
    ("w", "u32", 0),
    ("h", "u32", 4),
    ("border_ptr", "ptr", 8),
    ("tilemap_ptr", "ptr", 12),
    ("global_tileset_ptr", "ptr", 16),
    ("local_tileset_ptr", "ptr", 20),
    # FR only
    ("border_w", "u8", 24),
    ("border_h", "u8", 25)
)

connections_header = (
        ("n_of_connections", "u32", 0),
        ("connection_data_ptr", "ptr", 4)
        )

connection_data = (
        ("direction", "u32", 0),
        ("offset", "s32", 4),
        ("bank_num", "u8", 8),
        ("map_num", "u8", 9),
        ("null", "u16", 10)
        )

tileset_header_base = (
    ("is_compressed", "u8", 0),
    ("tileset_type", "u8", 1),
    ("null", "u16", 2), # 0000
    ("tileset_image_ptr", "ptr", 4),
    ("palettes_ptr", "ptr", 8),
    ("block_data_ptr", "ptr", 12),
)

tileset_header_rs = tileset_header_base + (
    ("behavior_data_ptr", "ptr", 16),
    ("animation_data_ptr", "ptr", 20),
)

tileset_header_fr = tileset_header_base + (
    ("animation_data_ptr", "ptr", 16),
    ("behavior_data_ptr", "ptr", 20),
)

events_header = (
    ("n_of_people", "u8", 0),
    ("n_of_warps", "u8", 1),
    ("n_of_triggers", "u8", 2),
    ("n_of_signposts", "u8", 3),
    ("person_events_ptr", "ptr", 4),
    ("warp_events_ptr", "ptr", 8),
    ("trigger_events_ptr", "ptr", 12),
    ("signpost_events_ptr", "ptr", 16)
)

person_event = (
    ("person_num", "u8", 0),
    ("sprite_num", "u8", 1),
    ("unknown1", "u8", 2),
    ("unknown2", "u8", 3),
    ("x", "u16", 4),
    ("y", "u16", 6),
    ("unknown3", "u8", 8),
    ("mov_type", "u8", 9),
    ("mov", "u8", 10),
    ("unknown4", "u8", 11),
    ("is_a_trainer", "u8", 12),
    ("unknown5", "u8", 13),
    ("radius", "u16", 14),
    ("script_ptr", "ptr", 16),
    ("flag", "u16", 20),
    ("unknown6", "u8", 22),
    ("unknown7", "u8", 23),
)

warp_event = (
    ("x", "u16", 0),
    ("y", "u16", 2),
    ("unknown", "u8", 4),
    ("warp_num", "u8", 5),
    ("map_num", "u8", 6),
    ("bank_num", "u8", 7),
)

trigger_event = (
    ("x", "u16", 0),
    ("y", "u16", 2),
    ("unknown1", "u16", 4),
    ("var_num", "u16", 6),
    ("var_value", "u16", 8),
    ("unknown2", "u8", 10),
    ("unknown3", "u8", 11),
    ("script_ptr", "ptr", 12),
)

signpost_event = (
    ("x", "u16", 0),
    ("y", "u16", 2),
    ("talking_level", "u8", 4),
    ("type", "u8", 5),
    ("unknown1", "u8", 6),
    ("unknown2", "u8", 7),
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

sprite2 = (
    ("img_ptr", "ptr", 0), # Yes it makes no sense
)

lscript_entry = (
    ("type", "u8", 0),
    ("script_header_ptr", "ptr", 1),
)
# List of entries ends in 0x00

# type 2 or 4, doesn't matter
lscript_type_2 = (
    ("flag", "u16", 0),
    ("value", "u16", 2),
    ("script_body_ptr", "ptr", 4),
    ("null", "u16", 2), # 0000
)

def to_dict(structure):
    d = {}
    for element in structure:
        key, size, pos = element
        d[key] = (size, pos)
    return d

bytes_in_size = {
    "u8": 1,
    "u16": 2,
    "ptr": 4,
    "u32": 4,
    "s32": 4
}

def size_of(structure):
    total = 0
    for _, size, _ in structure:
        total += bytes_in_size[size]
    return total

