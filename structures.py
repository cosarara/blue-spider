
map_header = (
        ("map_data_ptr", "ptr", 0),
        ("event_data_ptr", "ptr", 4),
        ("level_script_ptr", "ptr", 8),
        ("connections_ptr", "ptr", 12),
        ("song_index", "short", 16),
        ("map_ptr_index", "short", 18),
        ("label_index", "byte", 20),
        ("is_a_cave", "byte", 21),
        ("weather", "byte", 22),
        ("map_type", "byte", 23),
        # Unknown at 24-25
        ("show_label", "byte", 26),
        ("battle_type", "byte", 27),
        )

map_data = (
        ("h", "long", 0),
        ("w", "long", 4),
        ("border_ptr", "ptr", 8),
        ("tilemap_ptr", "ptr", 12),
        ("global_tileset_ptr", "ptr", 16),
        ("local_tileset_ptr", "ptr", 20),
        # FR only
        ("border_w", "byte", 24),
        ("border_h", "byte", 25)
        )

tileset_header_base = (
        ("is_compressed", "byte", 0),
        ("tileset_type", "byte", 1),
        # 0000
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
        ("n_of_people", "byte", 0),
        ("n_of_warps", "byte", 1),
        ("n_of_triggers", "byte", 2),
        ("n_of_signposts", "byte", 3),
        ("people_events_ptr", "ptr", 4),
        ("warp_events_ptr", "ptr", 8),
        ("trigger_events_ptr", "ptr", 12),
        ("singpost_events_ptr", "ptr", 16)
        )

person_event = (
        ("person_num", "byte", 0),
        ("sprite_num", "byte", 1),
        ("unknown1", "byte", 2),
        ("unknown2", "byte", 3),
        ("x", "short", 4),
        ("y", "short", 6),
        ("unknown3", "byte", 8),
        ("mov_type", "byte", 9),
        ("mov", "byte", 10),
        ("unknown4", "byte", 11),
        ("is_a_trainer", "byte", 12),
        ("unknown5", "byte", 13),
        ("radius", "short", 14),
        ("script_ptr", "ptr", 16),
        ("flag", "short", 20),
        ("unknown6", "byte", 22),
        ("unknown7", "byte", 23),
        )

warp_event = (
        ("x", "short", 0),
        ("y", "short", 2),
        ("unknown", "byte", 4),
        ("warp_num", "byte", 5),
        ("map_num", "byte", 6),
        ("bank_num", "byte", 7),
        )

trigger_event = (
        ("x", "short", 0),
        ("y", "short", 2),
        ("unknown", "short", 4),
        ("var_num", "short", 6),
        ("var_value", "short", 8),
        ("unknown2", "byte", 10),
        ("unknown3", "byte", 11),
        ("script_offset", "ptr", 12),
        )

signpost_event = (
        ("x", "short", 0),
        ("y", "short", 2),
        ("talking_level", "byte", 4),
        ("type", "byte", 5),
        ("unknown", "byte", 6),
        ("unknown", "byte", 7),
        )

events = {
    "person": person_event,
    "trigger": trigger_event,
    "warp": warp_event,
    "signpost": signpost_event
    }

def to_dict(structure):
    d = {}
    for element in structure:
        key, size, pos = element
        d[key] = (size, pos)
    return d


