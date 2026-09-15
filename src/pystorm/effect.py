from .common import JSONContributions
from .emitter import Emitter
from .particle import Particle
from .context import Event, Curve

from typing import Any

def makeParticleEffect(identifier: str, emitter: Emitter, particle: Particle, events: list[Event] = [], curves: list[Curve] = []):
    contrib = JSONContributions()
    contrib.contribute("particle_effect#description#identifier", identifier)
    contrib.contribute("format_version", "1.10.0")
    
    contrib.merge(emitter._contributeJson())
    contrib.merge(particle._contributeJson())
    
    for event in events:
        contrib.merge(event._contributeJson())
        
    for curve in curves:
        contrib.merge(curve._contributeJson())
    
    return contrib.asJson()
        
    