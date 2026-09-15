from pystorm.common import JSONContributions, Number, Molang, MolangValue

from .common import JSONContributor
from abc import ABC, abstractmethod
from typing import Any, Literal
import random
import string

class EventTrigger(ABC):
    @abstractmethod
    def _contributeJson(self, event: str) -> JSONContributions:
        pass
    
    @abstractmethod
    def target(self) -> str:
        pass



class BasicEventTrigger(EventTrigger, ABC):
    def __init__(self) -> None:
        super().__init__()
        
    def _contributeJson(self, event: str) -> JSONContributions:
        contrib = JSONContributions()
        contrib.contribute_item(self.target(), event)
        return contrib
    
class EmitterCreationTrigger(BasicEventTrigger):
    def target(self) -> str:
        return "particle_effect#components#minecraft:emitter_lifetime_events#creation_event"

class EmitterExpirationTrigger(BasicEventTrigger):
    def target(self) -> str:
        return "particle_effect#components#minecraft:emitter_lifetime_events#expiration_event"
    
class ParticleCreationTrigger(BasicEventTrigger):
    def target(self) -> str:
        return "particle_effect#components#minecraft:particle_lifetime_events#creation_event"

class ParticleExpirationTrigger(BasicEventTrigger):
    def target(self) -> str:
        return "particle_effect#components#minecraft:particle_lifetime_events#expiration_event"


class TravelEventTrigger(EventTrigger):
    def __init__(self, travelDistance: Number) -> None:
        super().__init__()
        self.travelDistance = travelDistance
        
    def _contributeJson(self, event: str) -> JSONContributions:
        contrib = JSONContributions()
        contrib.contribute_item(self.target() + "." + str(self.travelDistance), event)
        return contrib

class EmitterTravelTrigger(TravelEventTrigger):
    def target(self) -> str:
        return "particle_effect#components#minecraft:emitter_lifetime_events#travel_distance_events"

class EmitterLoopingTravelTrigger(TravelEventTrigger):
    # I have no clue why this has to be formated differently to the non-looping version
    # but it's a pain in my ass
    def _contributeJson(self, event: str) -> JSONContributions:
        contrib = JSONContributions()
        contrib.contribute_looping_item(self.target(), self.travelDistance, event)
        return contrib
    
    def target(self) -> str:
        return "particle_effect#components#minecraft:emitter_lifetime_events#looping_travel_distance_events"


class TimelineEventTrigger(EventTrigger):
    def __init__(self, timeStamp: Number) -> None:
        super().__init__()
        self.timeStamp = timeStamp
        
    def _contributeJson(self, event: str) -> JSONContributions:
        contrib = JSONContributions()
        contrib.contribute_item(self.target() + "." + str(self.timeStamp), event)
        return contrib
    
class EmitterTimelineTrigger(TimelineEventTrigger):
    def target(self) -> str:
        return "particle_effect#components#minecraft:emitter_lifetime_events#timeline"
    
class ParticleTimelineTrigger(TimelineEventTrigger):
    def target(self) -> str:
        return "particle_effect#components#minecraft:particle_lifetime_events#timeline"
    

class CollisionEventTrigger(EventTrigger):
    def __init__(self, minSpeed: Number) -> None:
        super().__init__()
        self.minSpeed = minSpeed
        
    def _contributeJson(self, event: str) -> JSONContributions:
        contrib = JSONContributions()
        contrib.contribute_item(self.target(), { "event": event, "min_speed": self.minSpeed })
        return contrib
    
    def target(self) -> str:
        # ? means the contribution only occurs if that element already exists
        return "particle_effect#components#minecraft:particle_motion_collision?#events"
    
    
type EventParticleType = Literal["emitter", "emitter_bound", "particle", "particle_with_velocity"]
    
class EventParticle():
    def __init__(self, effect: str, expression: Molang | None = None, emissionType: EventParticleType = "emitter") -> None:
        super().__init__()
        self.effect = effect
        self.expression = expression
        self.emissionType = emissionType
        
    def _contributeJson(self, event: str) -> JSONContributions:
        contrib = JSONContributions(f"particle_effect#events#{event}#particle_effect")
        contrib.contribute("effect", self.effect)
        contrib.contribute("type", self.emissionType)
        contrib.contribute("pre_effect_expression", self.expression)
        return contrib
    

class Event(JSONContributor):
    def __init__(self, triggers: list[EventTrigger], expression: Molang | None = None, sound: str | None = None, particleEffect: EventParticle | None = None) -> None:
        super().__init__()
        self.name = (''
            .join(random.choices(string.ascii_lowercase, k=1))
            .join(random.choices(string.ascii_lowercase + string.digits, k=7))
        )
        self.triggers = triggers
        self.expression = expression
        self.sound = sound
        self.effect = particleEffect
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions(f"particle_effect#events#{self.name}")
        contrib.contribute("sound_effect#event_name", self.sound)
        contrib.contribute("expression", self.expression)
        
        if self.effect != None:
            contrib.merge(self.effect._contributeJson(self.name))
            
        for trigger in self.triggers:
            contrib.merge(trigger._contributeJson(self.name))
        
        return contrib
    


class Curve(JSONContributor, ABC):
    pass

class LinearCurve(Curve):
    curveType = "linear"
    
    def __init__(self, inputExpression: MolangValue, outputVariable: Molang, controlPoints: list[MolangValue]) -> None:
        super().__init__()
        self.inputExpression = inputExpression
        self.outputVariable = outputVariable
        self.controlPoints = controlPoints
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions(f"particle_effect#curves#{self.outputVariable}")
        contrib.contribute("type", self.curveType)
        contrib.contribute("input", self.inputExpression)
        contrib.contribute("nodes", self.controlPoints)
        return contrib

class BezierCurve(LinearCurve):
    curveType = "bezier"
    
class CatmulRomCurve(LinearCurve):
    curveType = "catmull_rom"
    
class BezierChainCurve(Curve):
    def __init__(self, inputExpression: MolangValue, outputVariable: Molang, controlPoints: dict[Number, tuple[Number, Number]]) -> None:
        super().__init__()
        self.inputExpression = inputExpression
        self.outputVariable = outputVariable
        self.controlPoints = controlPoints
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions(f"particle_effect#curves#{self.outputVariable}")
        contrib.contribute("type", "bezier_chain")
        contrib.contribute("input", self.inputExpression)
        contrib.contribute("nodes", {key: {"value": value[0], "slope": value[1]} for key, value in self.controlPoints.items()})
        return contrib