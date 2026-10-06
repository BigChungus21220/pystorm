import re
from compact_json import Formatter

# this function was (mostly) written by Gemini
def processMolang(expression: str):
    """Processes strings with all your favorite molang decorations to valid molang / json. (newlines, comments, whitespace shrinking, double quotes)"""
    # 1. Remove C-style single-line (//) and multi-line (/* */) comments.
    # We use a regex that matches strings first (to avoid removing comment characters inside strings)
    # Group 1: Strings | Group 2: Comments
    def remove_comments(match):
        if match.group(1): 
            return match.group(1) # Keep string as is
        return ""                 # Remove comment

    # remove comments only if there are multiple lines (in case this string isn't molang)
    if "\n" in expression or "\r" in expression:
        # Matches "...", '...', /*...*/, and //...
        pattern = r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')|(/\*.*?\*/|//[^\r\n]*)'
        expression = re.sub(pattern, remove_comments, expression, flags=re.DOTALL)

        # 2. Remove all newlines and carriage returns
        expression = expression.replace('\n', '').replace('\r', '')

    # 3. Replace double quotes with single quotes, and tabs with spaces
    expression = expression.replace('"', "'").replace('\t', ' ')

    # 4. Remove double spaces not contained in quotes
    parts = re.split(r"('[^'\\]*(?:\\.[^'\\]*)*')", expression)
    
    for i in range(len(parts)):
        if i % 2 == 0:  # Even index = outside of quotes
            while '  ' in parts[i]:
                parts[i] = parts[i].replace('  ', ' ')
                
    return "".join(parts).strip()


element_precedence = [
    "format_version",
    "particle_effect",
    "description",
    "curves",
    "events",
    "components",
    "minecraft:emitter_lifetime_events",
    "minecraft:emitter_lifetime_expression",
    "minecraft:emitter_lifetime_looping",
    "minecraft:emitter_lifetime_once",
    "minecraft:emitter_rate_instant",
    "minecraft:emitter_rate_manual",
    "minecraft:emitter_rate_steady",
    "minecraft:emitter_shape_disc",
    "minecraft:emitter_shape_box",
    "minecraft:emitter_shape_custom",
    "minecraft:emitter_shape_entity_aabb",
    "minecraft:emitter_shape_point",
    "minecraft:emitter_shape_sphere",
    "minecraft:emitter_initialization",
    "minecraft:emitter_local_space",
    "minecraft:particle_appearance_billboard",
    "minecraft:particle_appearance_lighting",
    "minecraft:particle_appearance_tinting",
    "minecraft:particle_initial_speed",
    "minecraft:particle_initial_spin",
    "minecraft:particle_expire_if_in_blocks",
    "minecraft:particle_expire_if_not_in_blocks",
    "minecraft:particle_lifetime_events",
    "minecraft:particle_lifetime_expression",
    "minecraft:particle_kill_plane",
    "minecraft:particle_motion_collision",
    "minecraft:particle_motion_dynamic",
    "minecraft:particle_motion_parametric",
    "identifier",
    "basic_render_parameters",
    "material",
    "texture"
]

def custom_sort_dict_R(obj, order_list):
    if isinstance(obj, dict):
        sorted_items = sorted(
            obj.items(),
            key=lambda item: (
                order_list.index(item[0]) if item[0] in order_list else len(order_list),
                item[0]
            )
        )
        return {k: custom_sort_dict_R(v, order_list) for k, v in sorted_items}
    
    elif isinstance(obj, list):
        return [custom_sort_dict_R(item, order_list) for item in obj]
    
    return obj

def sort_effect(obj) -> dict:
    """Sorts particle json according to standard organization"""
    return custom_sort_dict_R(obj, element_precedence) # type: ignore

def serializePretty(json: dict) -> str:
    """Pretty prints and sorts the json according to particle file convention"""
    sort = sort_effect(json)
    
    formatter = Formatter()
    formatter.indent_spaces = 4
    formatter.max_inline_complexity = 0
    
    # someone mistyped their function lol
    return formatter.serialize(sort) # type: ignore