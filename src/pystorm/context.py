from pystorm.common import JSONContributions
from .molang_types import Molang, MolangValue, Number

from .common import JSONContributor
from abc import ABC, abstractmethod
from typing import Any, Literal
import random
import string
from dataclasses import dataclass

class EventTrigger(ABC):
    """Base class for event triggers. Use 
    :class:`EmitterCreationTrigger`,
    :class:`EmitterExpirationTrigger`,
    :class:`ParticleCreationTrigger`,
    :class:`ParticleExpirationTrigger`,
    :class:`EmitterTravelTrigger`,
    :class:`EmitterLoopingTravelTrigger`,
    :class:`EmitterTimelineTrigger`,
    :class:`ParticleTimelineTrigger`,
    or :class:`CollisionEventTrigger`
    instead."""
    @abstractmethod
    def _contributeJson(self, event: str) -> JSONContributions:
        pass
    
    @abstractmethod
    def target(self) -> str:
        pass


@dataclass
class BasicEventTrigger(EventTrigger, ABC):
    """Base class for simple event triggers. See :class:`EventTrigger` for options."""
    def _contributeJson(self, event: str) -> JSONContributions:
        contrib = JSONContributions()
        contrib.contribute_item(self.target(), event)
        return contrib

class EmitterCreationTrigger(BasicEventTrigger):
    """Runs on emitter creation."""
    def target(self) -> str:
        return "particle_effect#components#minecraft:emitter_lifetime_events#creation_event"

class EmitterExpirationTrigger(BasicEventTrigger):
    """Runs on emitter expiration."""
    def target(self) -> str:
        return "particle_effect#components#minecraft:emitter_lifetime_events#expiration_event"
    
class ParticleCreationTrigger(BasicEventTrigger):
    """Runs on particle creation."""
    def target(self) -> str:
        return "particle_effect#components#minecraft:particle_lifetime_events#creation_event"

class ParticleExpirationTrigger(BasicEventTrigger):
    """Runs on particle expiration."""
    def target(self) -> str:
        return "particle_effect#components#minecraft:particle_lifetime_events#expiration_event"


@dataclass
class TravelEventTrigger(EventTrigger):
    """Base class for travel distance event triggers. See :class:`EventTrigger` for options."""
    travelDistance: Number
    """Distance to trigger at (blocks)."""
        
    def _contributeJson(self, event: str) -> JSONContributions:
        contrib = JSONContributions()
        contrib.contribute_item(self.target() + "." + str(self.travelDistance), event)
        return contrib

class EmitterTravelTrigger(TravelEventTrigger):
    """Runs at `travelDistance` blocks of emitter travel."""
    def target(self) -> str:
        return "particle_effect#components#minecraft:emitter_lifetime_events#travel_distance_events"

class EmitterLoopingTravelTrigger(TravelEventTrigger):
    """Runs every `travelDistance` blocks of emitter travel."""
    # I have no clue why this has to be formated differently to the non-looping version
    # but it's a pain in my ass
    def _contributeJson(self, event: str) -> JSONContributions:
        contrib = JSONContributions()
        contrib.contribute_looping_item(self.target(), self.travelDistance, event)
        return contrib
    
    def target(self) -> str:
        return "particle_effect#components#minecraft:emitter_lifetime_events#looping_travel_distance_events"


@dataclass
class TimelineEventTrigger(EventTrigger):
    """Base class for timeline event triggers. See :class:`EventTrigger` for options."""
    timeStamp: Number
    """Time to run this event at."""
        
    def _contributeJson(self, event: str) -> JSONContributions:
        contrib = JSONContributions()
        contrib.contribute_item(self.target() + "." + str(self.timeStamp), event)
        return contrib
    
class EmitterTimelineTrigger(TimelineEventTrigger):
    """Runs at a specific emitter age."""
    def target(self) -> str:
        return "particle_effect#components#minecraft:emitter_lifetime_events#timeline"
    
class ParticleTimelineTrigger(TimelineEventTrigger):
    """Runs at a specific particle age."""
    def target(self) -> str:
        return "particle_effect#components#minecraft:particle_lifetime_events#timeline"
    

@dataclass
class CollisionEventTrigger(EventTrigger):
    """Runs on particle collision."""
    minSpeed: Number
        
    def _contributeJson(self, event: str) -> JSONContributions:
        contrib = JSONContributions()
        contrib.contribute_item(self.target(), { "event": event, "min_speed": self.minSpeed })
        return contrib
    
    def target(self) -> str:
        # ? means the contribution only occurs if that element already exists
        return "particle_effect#components#minecraft:particle_motion_collision?#events"
    
    
type EventParticleType = Literal["emitter", "emitter_bound", "particle", "particle_with_velocity"]

@dataclass
class EventParticle():
    """Event behavior which spawns a new particle emitter of any type at the current particle/emitter location."""
    effect: str
    """Effect identifier of effect to spawn. `namespace:name`."""
    expression: Molang | None = None
    """Molang to run on spawned emitter."""
    emissionType: EventParticleType = "emitter"
    """Emission type. Probably don't change this."""
        
    def _contributeJson(self, event: str) -> JSONContributions:
        contrib = JSONContributions(f"particle_effect#events#{event}#particle_effect")
        contrib.contribute("effect", self.effect)
        contrib.contribute("type", self.emissionType)
        contrib.contribute("pre_effect_expression", self.expression)
        return contrib
    

@dataclass
class Event(JSONContributor):
    """Event triggers and associated actions."""
    triggers: list[EventTrigger]
    """Trigers to fire this event on."""
    expression: Molang | None = None
    """Expression to run on this emitter / particle."""
    sound: str | None = None
    """Sound to play. An identifier from `sound_definitions.json`."""
    particleEffect: EventParticle | None = None
    """Particle to spawn."""
    
    __name = (''
        .join(random.choices(string.ascii_lowercase, k=1))
        .join(random.choices(string.ascii_lowercase + string.digits, k=7))
    )
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions(f"particle_effect#events#{self.__name}")
        contrib.contribute("sound_effect#event_name", self.sound)
        contrib.contribute("expression", self.expression)
        
        if self.particleEffect is not None:
            contrib.merge(self.particleEffect._contributeJson(self.__name))
            
        for trigger in self.triggers:
            contrib.merge(trigger._contributeJson(self.__name))
        
        return contrib
    


class Curve(JSONContributor, ABC):
    """Base class for curve interpolation types. Use :class:`LinearCurve`, :class:`BezierCurve`, :class:`CatmulRomCurve`, :class:`BezierChainCurve` instead."""
    pass

@dataclass
class LinearCurve(Curve):
    """Linearly interpolated value. Accessed in molang via it's assigned variable."""
    _curveType = "linear"
    
    inputExpression: MolangValue
    """Interpolant value from 0 to 1. `outputVariable = first keyframe` if `inputExpression = 0`. `outputVariable = last keyframe` if `inputExpression = 1`."""
    outputVariable: Molang
    """Variable to output to. `v.{name}`, `variable.{name}`, `t.{name}`, or `temp.{name}`"""
    controlPoints: list[MolangValue]
    """Evenly spaced (in input space) keyframes."""
        
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions(f"particle_effect#curves#{self.outputVariable}")
        contrib.contribute("type", self._curveType)
        contrib.contribute("input", self.inputExpression)
        contrib.contribute("nodes", self.controlPoints)
        return contrib

class BezierCurve(LinearCurve):
    """Bezier interpolated value. Accessed in molang via it's assigned variable."""
    _curveType = "bezier"
    
class CatmulRomCurve(LinearCurve):
    """Catmul-Rom interpolated value. Accessed in molang via it's assigned variable."""
    _curveType = "catmull_rom"

@dataclass
class BezierNode(JSONContributor):
    """A bezier chain node. See :class:`BezierChainCurve`"""
    timestamp: Number
    """Input value of this node."""
    value: Number
    """Output value of this node."""
    slope: Number | tuple[Number, Number]
    """Slope through this node or slope to either side of this node. Using a different left and right slope will create a cusp in the function."""
    
    def controls(self) -> dict:
        if isinstance(self.slope, tuple):  
            return {"value": self.value, "left_slope": self.slope[0], "right_slope": self.slope[1]}
        else:
            return {"value": self.value, "slope": self.slope}

@dataclass
class BezierChainCurve(Curve):
    """Bezier chain interpolated value. Accessed in molang via it's assigned variable."""
    inputExpression: MolangValue
    """Interpolant/\"time\" value."""
    outputVariable: Molang
    """Variable to output to. `v.{name}`, `variable.{name}`, `t.{name}`, or `temp.{name}`"""
    controlPoints: list[BezierNode]
    """Keyframes. `{time}: (value, slope)`. Note: additional options not implemented."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions(f"particle_effect#curves#{self.outputVariable}")
        contrib.contribute("type", "bezier_chain")
        contrib.contribute("input", self.inputExpression)
        contrib.contribute("nodes", {node.timestamp: node.controls() for node in self.controlPoints})
        return contrib