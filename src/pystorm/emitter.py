from .common import JSONContributor, JSONContributions
from .molang_types import MolangValue, MolangInt, MolangNumber, MolangVector3, Molang
from abc import ABC
from typing import Literal
from dataclasses import dataclass


class EmitterLifetime(JSONContributor, ABC):
    pass

@dataclass
class EmitterLifetimeExpression(EmitterLifetime):
    activate: MolangValue = 1
    expire: MolangValue = 0
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_lifetime_expression")
        contrib.contribute_or_default("activation_expression", self.activate, 1)
        contrib.contribute_or_default("expiration_expression", self.expire, 0)
        return contrib

@dataclass
class EmitterLifetimeLooping(EmitterLifetime):
    activeTime: MolangValue = 10
    sleepTime: MolangValue = 0
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_lifetime_looping")
        contrib.contribute("active_time", self.activeTime)
        contrib.contribute("sleep_time", self.sleepTime)
        return contrib

@dataclass
class EmitterLifetimeOnce(EmitterLifetime):
    activeTime: MolangValue = 10
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_lifetime_once")
        contrib.contribute("active_time", self.activeTime)
        return contrib



class EmitterRate(JSONContributor, ABC):
    pass

@dataclass
class EmitterRateInstant(EmitterRate):
    particles: int | Molang = 1
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_rate_instant")
        contrib.contribute("num_particles", self.particles)
        return contrib

@dataclass
class EmitterRateManual(EmitterRate):
    maxParticles: MolangInt = 50
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_rate_manual")
        contrib.contribute("max_particles", self.maxParticles)
        return contrib

@dataclass
class EmitterRateSteady(EmitterRate):
    spawnRate: MolangNumber = 1
    maxParticles: MolangInt = 50
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_rate_steady")
        contrib.contribute("spawn_rate", self.spawnRate)
        contrib.contribute("max_particles", self.maxParticles)
        return contrib



type EmitterShapeDirection = Literal["inwards", "outwards"] | MolangVector3

class EmitterShape(JSONContributor, ABC):
    pass

@dataclass
class EmitterShapeDisc(EmitterShape):
    planeNormal: MolangVector3 = (0, 1, 0)
    offset: MolangVector3 = (0, 0, 0)
    radius: MolangNumber = 1
    surfaceOnly: bool = False
    direction: EmitterShapeDirection = "outwards"
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_shape_disk")
        contrib.contribute_or_default("plane_normal", self.planeNormal, (0, 1, 0))
        contrib.contribute_or_default("offset", self.offset, (0, 0, 0))
        contrib.contribute_or_default("radius", self.radius, 1)
        contrib.contribute_or_default("surface_only", self.surfaceOnly, False)
        contrib.contribute_or_default("direction", self.direction, "outwards")
        return contrib

@dataclass
class EmitterShapeBox(EmitterShape):
    halfDimensions: MolangVector3
    offset: MolangVector3 = (0, 0, 0)
    surfaceOnly: bool = False
    direction: EmitterShapeDirection = "outwards"
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_shape_box")
        contrib.contribute("half_dimensions", self.halfDimensions)
        contrib.contribute_or_default("offset", self.offset, (0, 0, 0))
        contrib.contribute_or_default("surface_only", self.surfaceOnly, False)
        contrib.contribute_or_default("direction", self.direction, "outwards")
        return contrib

@dataclass
class EmitterShapeEntityAABB(EmitterShape):
    surfaceOnly: bool = False
    direction: EmitterShapeDirection = "outwards"
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_shape_entity_aabb")
        contrib.contribute_or_default("surface_only", self.surfaceOnly, False)
        contrib.contribute_or_default("direction", self.direction, "outwards")
        return contrib

@dataclass
class EmitterShapePoint(EmitterShape):
    offset: MolangVector3 = (0, 0, 0)
    direction: MolangVector3 = (0, 0, 0)
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_shape_point")
        contrib.contribute_or_default("offset", self.offset, (0, 0, 0))
        contrib.contribute_or_default("direction", self.direction, (0, 0, 0))
        return contrib

@dataclass
class EmitterShapeSphere(EmitterShape):
    offset: MolangVector3 = (0, 0, 0)
    radius: MolangNumber = 1
    surfaceOnly: bool = False
    direction: EmitterShapeDirection = "outwards"
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_shape_sphere")
        contrib.contribute_or_default("offset", self.offset, (0, 0, 0))
        contrib.contribute_or_default("radius", self.radius, 1)
        contrib.contribute_or_default("surface_only", self.surfaceOnly, False)
        contrib.contribute_or_default("direction", self.direction, "outwards")
        return contrib
    
    
    

@dataclass
class Emitter(JSONContributor):
    lifetime: EmitterLifetime
    rate: EmitterRate
    shape: EmitterShape
    localPosition: bool = False
    localRotation: bool = False
    localVelocity: bool = False
    emitterCreation: Molang | None = None
    emitterUpdate: Molang | None = None
    
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_local_space")
        contrib.contribute_or_default("position", self.localPosition, False)
        contrib.contribute_or_default("rotation", self.localRotation, False)
        contrib.contribute_or_default("velocity", self.localVelocity, False)
        
        emitter_contrib = JSONContributions("particle_effect#components#minecraft:emitter_initialization")
        emitter_contrib.contribute("creation_expression", self.emitterCreation)
        emitter_contrib.contribute("per_update_expression", self.emitterUpdate)
        contrib.merge(emitter_contrib)
        
        contrib.merge(self.lifetime._contributeJson())
        contrib.merge(self.rate._contributeJson())
        contrib.merge(self.shape._contributeJson())
        
        return contrib