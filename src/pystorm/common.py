from abc import ABC, abstractmethod
from typing import Self, Never, Any
from .utils import processMolang
from collections import defaultdict, deque
from compact_json import Formatter

# this is braindead fr
type Molang = str
type MolangValue = Molang | int | float | bool
type MolangNumber = Molang | int | float
type Number = float | int
type MolangInt = Molang | int
type MolangVector2 = tuple[MolangNumber, MolangNumber]
type MolangVector3 = tuple[MolangNumber, MolangNumber, MolangNumber]
type MolangVector4 = tuple[MolangNumber, MolangNumber, MolangNumber, MolangNumber]
type Color = str | MolangVector3 | MolangVector4
type EmptyObject = dict[Never, Never]
type JSONValue = str | int | float | bool | list[JSONValue] | list[str] | tuple[JSONValue, ...] | tuple[Number, ...] | dict[Number, Color] | EmptyObject

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

def custom_sort_dict(obj, order_list):
    if isinstance(obj, dict):
        sorted_items = sorted(
            obj.items(),
            key=lambda item: (
                order_list.index(item[0]) if item[0] in order_list else len(order_list),
                item[0]
            )
        )
        return {k: custom_sort_dict(v, order_list) for k, v in sorted_items}
    
    elif isinstance(obj, list):
        return [custom_sort_dict(item, order_list) for item in obj]
    
    return obj

class JSONContributions:
    def __init__(self, root: str | None = None) -> None:
        self.root = root
        self.contributions: dict[str, Any] = {}
    
    def contribute(self, path: str, value: Any | None):
        if value != None:
            if isinstance(value, str):
                value = processMolang(value)
                
            if self.root != None:
                path = self.root + "#" + path
            
            self.contributions[path] = value
                
    def contribute_item(self, path: str, value: Any | None):
        if value != None:
            if isinstance(value, str):
                value = processMolang(value)
                
            if self.root != None:
                path = self.root + "#" + path
            
            if path not in self.contributions:
                self.contributions[path] = [value]
            else:
                contrib = self.contributions[path]
                if isinstance(contrib, list):
                    contrib.append(value)
                else:
                    raise TypeError(f"{path} is not a list")
                
    def contribute_looping_item(self, path: str, id: Number, value: str | None):
        if value != None:
            if isinstance(value, str):
                value = processMolang(value)
                
            if self.root != None:
                path = self.root + "#" + path
            
            if path not in self.contributions:
                self.contributions[path] = [{
                    "distance": id,
                    "effects": [value]
                }]
            else:
                contrib = self.contributions[path]
                if isinstance(contrib, list):
                    idx = next((i for i, c in enumerate(contrib) if c["distance"] == id), None)
                    if idx == None:
                        contrib.append({
                            "distance": id,
                            "effects": [value]
                        })
                    else:
                        contrib[idx]["events"].append(value)
                else:
                    raise TypeError(f"{path} is not a list")
    
    def contribute_or_default(self, path: str, value: Any, defaultValue: JSONValue):
        if value != defaultValue:
            if isinstance(value, str):
                value = processMolang(value)
                
            if self.root != None:
                path = self.root + "#" + path
                
            self.contributions[path] = value
    
    def merge(self, other: Self):
        self.contributions.update(other.contributions)
        
    def asJson(self):
        contributions = JSONContributions._resolve_conditional_keys(self.contributions)
        
        json_obj = {}
        for key, value in contributions:
            path = key.split("#")
            pos = json_obj
            for i, name in enumerate(path):
                if i == len(path)-1:
                    pos[name] = value
                else:
                    if name in pos:
                        pos = pos[name]
                    else:
                        pos[name] = {}
                        pos = pos[name]
               
        sort = custom_sort_dict(json_obj, element_precedence)
                 
        formatter = Formatter()
        formatter.indent_spaces = 4
        formatter.max_inline_complexity = 0
        
        return formatter.serialize(sort) # type: ignore
        
    # helper method written by Gemini
    @staticmethod
    def _resolve_conditional_keys(contributions: dict[str, Any]):
        rules = []
        parsed_keys = {}
        
        # Step 1: Parse all keys and build dependency rules
        for key in contributions:
            segments = key.split('#')
            parsed = []
            for seg in segments:
                if seg.endswith('?'):
                    parsed.append((seg[:-1], True))
                else:
                    parsed.append((seg, False))
            
            parsed_keys[key] = parsed
            
            req = None
            current_path_list = []
            
            # Traverse the segments to generate rules
            for name, is_cond in parsed:
                current_path_list.append(name)
                current_path = "#".join(current_path_list)
                
                if is_cond:
                    # Update requirement for any following unconditional segments
                    req = current_path
                else:
                    # An unconditional segment provides a path, assuming `req` is met
                    rules.append((req, current_path))
                    
        # Step 2: Establish the unconditionally provided paths
        established = set()
        adj = defaultdict(list)
        
        for req, prov in rules:
            if req is None:
                established.add(prov)
            else:
                adj[req].append(prov)
                
        # Step 3: Cascade to find all conditionally established paths (BFS)
        queue = deque(established)
        
        while queue:
            curr = queue.popleft()
            for nxt in adj[curr]:
                if nxt not in established:
                    established.add(nxt)
                    queue.append(nxt)
                    
        # Step 4: Resolve keys and filter based on what was fully established
        result = []
        for key, value in contributions.items():
            parsed = parsed_keys[key]
            resolved_key = "#".join(name for name, _ in parsed)
            
            # A key is completely valid if its FULL resolved path is in the established set
            if resolved_key in established:
                result.append((resolved_key, value))
                
        return result

class JSONContributor(ABC):
    @abstractmethod
    def _contributeJson(self) -> JSONContributions:
        pass
    