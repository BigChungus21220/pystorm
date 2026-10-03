from .common import JSONContributions
from .emitter import Emitter
from .particle import Particle
from .context import Event, Curve
from .utils import serializePretty
from pathlib import Path
        
class ParticleEffect:
    def __init__(self, identifier: str, emitter: Emitter, particle: Particle, events: list[Event] = [], curves: list[Curve] = []):
        self.identifier = identifier
        self.emitter = emitter
        self.particle = particle
        self.events = events
        self.curves = curves
        
    def asJSON(self) -> dict:
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
        json = self.asJSON()
        return serializePretty(json)
    
    def saveAs(self, particle_path: Path):
        with open(particle_path, "w") as file:
            file.write(self.asStr())