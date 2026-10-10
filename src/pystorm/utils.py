import re
from compact_json import Formatter
from pathlib import Path
import json
from dataclasses import dataclass
import os

@dataclass
class _IndexedParticle:
    path: Path
    identifier: str
    texture_str: str | None
    texture_path: Path | None
    texture_dist: float = 999.0
    
from pathlib import Path

def tree_distance(path1: str | Path, path2: str | Path) -> int:
    # .resolve() ensures paths are absolute and resolves any symlinks or ".."
    p1_parts = Path(path1).resolve().parts
    p2_parts = Path(path2).resolve().parts
    
    # Find how many path parts they share from the root
    common_len = 0
    for part1, part2 in zip(p1_parts, p2_parts):
        if part1 == part2:
            common_len += 1
        else:
            break
            
    # Distance = (steps from path1 up to common parent) + (steps from parent down to path2)
    return (len(p1_parts) - common_len) + (len(p2_parts) - common_len)
    

def indexFolder(folder: Path | str, max_distance: int | None = None, search_referenced: bool = True) -> list[tuple[Path, Path | None]]:
    """Finds particle effects in a folder and matches them to textures.\n
    Only searches for `.json` and `.png`. `O(nm)`, where `n` is number of valid particle files, and `m` is number of png files.

    Args:
        folder (Path | str): Folder path to search
        
    Returns:
        (list[tuple[Path, Path]]): Particle path, texture path pairs
    """
    
    if isinstance(folder, str):
        folder = Path(folder) 
    
    particles: list[_IndexedParticle] = []
    
    # register all particles in the folder
    for file in folder.rglob("*.json", case_sensitive=False):
        if not file.is_file():
            continue
        
        try:
            with open(file, 'r', encoding='utf-8') as f:
                particle_json: dict = json.load(f)
            
            # check that it is probably a valid particle
            if particle_json.get("format_version") == "1.10.0":
                description: dict = particle_json.get("particle_effect", {}).get("description", {})
                identifier = description.get("identifier")
                if not isinstance(identifier, str):
                    continue
                texture = description.get("basic_render_parameters", {}).get("texture")
                if not isinstance(texture, str):
                    texture = None
                particles.append(_IndexedParticle(file, identifier, texture, None))
                
        except Exception:
            pass
            
    # Find the closest texture for each particle
    for file in folder.rglob("*.png", case_sensitive=False):
        if not file.is_file():
            continue
        
        name = file.stem
        for particle in particles:
            dist = 999
            # regular name matching
            if particle.path.stem == name:
                dist = tree_distance(file, particle.path)
            
            # referenced name matching
            # snap path to referenced node
            if search_referenced and particle.texture_str is not None:
                full_path = file.resolve().with_suffix("")
                
                partial_parts = Path(particle.texture_str).parts
                full_parts = full_path.parts
                
                if partial_parts and len(partial_parts) <= len(full_parts):
                    if full_parts[-len(partial_parts):] == partial_parts:
                        snap_path = Path(*full_path.parts[:-len(partial_parts)])
                        
                        dist = min(dist, tree_distance(snap_path, particle.path))
                
            # update distance
            if (max_distance is None or dist <= max_distance) and dist < particle.texture_dist:
                particle.texture_path = file
                particle.texture_dist = dist
    
    return [(particle.path, particle.texture_path) for particle in particles]            


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