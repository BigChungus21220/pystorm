from abc import ABC, abstractmethod
from typing import Self, Never, Any
from .utils import processMolang, sort_effect
from collections import defaultdict, deque
from .molang_types import Number

class JSONContributions:
    def __init__(self, root: str | None = None) -> None:
        """JSON contributions starting from `root`. Eg: `contributeJson("name", ...)` with `root = 'path'` contributes `path#name`

        Args:
            root: Root json path. Defaults to None.
        """
        self.root = root
        self.contributions: dict[str, Any] = {}
    
    def contribute(self, path: str, value: Any | None):
        """Contributes a value if it is not `None`
        
        Args:
            path: Where to put value. Formatted as `key1#key2?#key3`, where ? means the value is only contributed if `key1#key2` has another contribution under it.
            value: value to contribute at `path`
        """
        if value is not None:
            if isinstance(value, str):
                value = processMolang(value)
                
            if self.root is not None:
                path = self.root + "#" + path
            
            self.contributions[path] = value
    
    def contribute_or_default(self, path: str, value: Any, defaultValue: Any):
        """Contributes a value only if it is not the default value and it isn't `None`
        
        Args:
            path: Where to put value. Formatted as `key1#key2?#key3`, where ? means the value is only contributed if `key1#key2` has another contribution under it.
            value: value to contribute at `path`
            defaultValue: value to compare against to check if contribution needs to be made
        """
        if value != defaultValue:
            if isinstance(value, str):
                value = processMolang(value)
                
            if self.root is not None:
                path = self.root + "#" + path
                
            self.contributions[path] = value
            
    def contribute_item(self, path: str, value: Any | None):
        """Specialized contribution for list items"""
        if value is not None:
            if isinstance(value, str):
                value = processMolang(value)
                
            if self.root is not None:
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
        """Specialized contribution for looping events"""
        if value is not None:
            if isinstance(value, str):
                value = processMolang(value)
                
            if self.root is not None:
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
                    if idx is None:
                        contrib.append({
                            "distance": id,
                            "effects": [value]
                        })
                    else:
                        contrib[idx]["events"].append(value)
                else:
                    raise TypeError(f"{path} is not a list")
    
    def merge(self, other: Self):
        """Joins two contribution lists. Paths of joined contributions are not updated, but any new contributions will still use the root as the path base."""
        self.contributions.update(other.contributions)
        
    def asJson(self) -> dict:
        """Resolves contributions into a json document"""
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
        
        sort = sort_effect(json_obj)
        
        return sort
        
    # helper method written by Gemini
    @staticmethod
    def _resolve_conditional_keys(contributions: dict[str, Any]) -> list[tuple[str, Any]]:
        """resolves conditional keys (keys containing ? only contribute if another key appends up to ?)"""
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
    