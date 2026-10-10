from .common import JSONContributions
from .emitter import Emitter
from .particle import Particle
from .context import Event, Curve
from .utils import serializePretty
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class ParticleEffect:
    """A Minecraft particle effect"""
    identifier: str
    """Particle identifier. `namespace:name`"""
    emitter: Emitter
    """Rules for particle spawning."""
    particle: Particle
    """Particle behavior and appearance."""
    events: list[Event] = field(default_factory=list)
    """Events and event triggers"""
    curves: list[Curve] = field(default_factory=list)
    """Variable curves"""
        
    def asJSON(self) -> dict:
        """Returns the json dict for this particle."""
        contrib = JSONContributions()
        contrib.contribute("particle_effect#description#identifier", self.identifier)
        contrib.contribute("format_version", "1.10.0")
        
        contrib.merge(self.emitter._contributeJson())
        contrib.merge(self.particle._contributeJson())
        
        for event in self.events:
            contrib.merge(event._contributeJson())
            
        for curve in self.curves:
            contrib.merge(curve._contributeJson())
        
        return contrib.asJson()
    
    def asStr(self) -> str:
        """Returns the json string for this particle."""
        json = self.asJSON()
        return serializePretty(json)
    
    def saveAs(self, particle_path: Path):
        """Saves this particle's json to a file."""
        with open(particle_path, "w") as file:
            file.write(self.asStr())