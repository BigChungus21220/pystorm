from .common import JSONContributor, JSONContributions
from .common_types import MolangValue, MolangInt, MolangNumber, MolangVector3, Molang
from abc import ABC
from typing import Literal
from dataclasses import dataclass


class EmitterLifetime(JSONContributor, ABC):
    """Base class for emitter lifetimes. Use :class:`EmitterLifetimeOnce`, :class:`EmitterLifetimeExpression`, or :class:`EmitterLifetimeLooping` instead"""
    pass

@dataclass
class EmitterLifetimeExpression(EmitterLifetime):
    """Expression driven lifetime. Emits based on molang per frame."""
    activate: MolangValue = 1
    """A particle is emitted each frame this expression is true. Eval every frame."""
    expire: MolangValue = 0
    """Emitter expires when this expression is false. Eval every frame."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_lifetime_expression")
        contrib.contribute_or_default("activation_expression", self.activate, 1)
        contrib.contribute_or_default("expiration_expression", self.expire, 0)
        return contrib

@dataclass
class EmitterLifetimeLooping(EmitterLifetime):
    """Looping lifetime. Cycles between on and off at molang defined intervals."""
    activeTime: MolangValue = 10
    """Emitter on time (seconds). Eval once per loop."""
    sleepTime: MolangValue = 0
    """Emitter off time (seconds). Eval once per loop."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_lifetime_looping")
        contrib.contribute("active_time", self.activeTime)
        contrib.contribute("sleep_time", self.sleepTime)
        return contrib

@dataclass
class EmitterLifetimeOnce(EmitterLifetime):
    """Standard fixed lifetime emitter."""
    activeTime: MolangValue = 10
    """Emitter lifetime (seconds). Eval at init."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_lifetime_once")
        contrib.contribute("active_time", self.activeTime)
        return contrib



class EmitterRate(JSONContributor, ABC):
    """Base class for emitter rates. Use :class:`EmitterRateInstant`, :class:`EmitterRateSteady`, or :class:`EmitterRateManual` instead"""
    pass

@dataclass
class EmitterRateInstant(EmitterRate):
    """Emits all particles in a short burst"""
    particles: int | Molang = 1
    """Particles to emit. Eval once per loop."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_rate_instant")
        contrib.contribute("num_particles", self.particles)
        return contrib

@dataclass
class EmitterRateManual(EmitterRate):
    """Legacy emission mode for some vanilla particles"""
    maxParticles: MolangInt = 50
    """Max number of particles of this type which can exist in the world. Eval once per particle."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_rate_manual")
        contrib.contribute("max_particles", self.maxParticles)
        return contrib

@dataclass
class EmitterRateSteady(EmitterRate):
    """Emits particles at a constant rate"""
    spawnRate: MolangNumber = 1
    """Spawn rate (particles/sec). Eval once per particle."""
    maxParticles: MolangInt = 50
    """Max particles this emitter can have at once. Eval once per emitter loop."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_rate_steady")
        contrib.contribute("spawn_rate", self.spawnRate)
        contrib.contribute("max_particles", self.maxParticles)
        return contrib



class EmitterShape(JSONContributor, ABC):
    """Base class for emitter shapes. Use :class:`EmitterShapePoint`, :class:`EmitterShapeDisc`, :class:`EmitterShapeSphere`, :class:`EmitterShapeBox`, or :class:`EmitterShapeEntityAABB` instead"""
    pass

@dataclass
class EmitterShapeDisc(EmitterShape):
    """Emits from a disk with an expression defined normal."""
    planeNormal: MolangVector3 = (0, 1, 0)
    """Disk normal (the direction perpendicular / orthogonal to the surface). Eval not documented."""
    offset: MolangVector3 = (0, 0, 0)
    """Offset of disk center. Eval once per particle. X and Y values are negated when attached to a locator."""
    radius: MolangNumber = 1
    """Radius of the disk. Eval once per particle."""
    surfaceOnly: bool = False
    """Whether to emit only from the circle around the disk."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_shape_disk")
        contrib.contribute_or_default("plane_normal", self.planeNormal, (0, 1, 0))
        contrib.contribute_or_default("offset", self.offset, (0, 0, 0))
        contrib.contribute_or_default("radius", self.radius, 1)
        contrib.contribute_or_default("surface_only", self.surfaceOnly, False)
        return contrib

@dataclass
class EmitterShapeBox(EmitterShape):
    """Emits from an axis aligned box."""
    halfDimensions: MolangVector3
    """Half dimensions of the box, centered on the emitter origin. Eval not documented."""
    offset: MolangVector3 = (0, 0, 0)
    """Offset of box center. Eval once per particle. X and Y values are negated when attached to a locator."""
    surfaceOnly: bool = False
    """Whether to emit only from the surface of the box."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_shape_box")
        contrib.contribute("half_dimensions", self.halfDimensions)
        contrib.contribute_or_default("offset", self.offset, (0, 0, 0))
        contrib.contribute_or_default("surface_only", self.surfaceOnly, False)
        return contrib

@dataclass
class EmitterShapeEntityAABB(EmitterShape):
    """Emits from the entity bounding box."""
    surfaceOnly: bool = False
    """Whether to emit only from the surface of the bounding box."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_shape_entity_aabb")
        contrib.contribute_or_default("surface_only", self.surfaceOnly, False)
        return contrib

@dataclass
class EmitterShapePoint(EmitterShape):
    """Emits from a point."""
    offset: MolangVector3 = (0, 0, 0)
    """Offset of particle. Eval once per particle. X and Y values are negated when attached to a locator."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_shape_point")
        contrib.contribute_or_default("offset", self.offset, (0, 0, 0))
        return contrib

@dataclass
class EmitterShapeSphere(EmitterShape):
    """Emits from a sphere."""
    offset: MolangVector3 = (0, 0, 0)
    """Offset of sphere. Eval once per particle. X and Y values are negated when attached to a locator."""
    radius: MolangNumber = 1
    """Sphere radius. Eval once per particle."""
    surfaceOnly: bool = False
    """Whether to emit only from the surface of the sphere."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:emitter_shape_sphere")
        contrib.contribute_or_default("offset", self.offset, (0, 0, 0))
        contrib.contribute_or_default("radius", self.radius, 1)
        contrib.contribute_or_default("surface_only", self.surfaceOnly, False)
        return contrib
    
    
    

@dataclass
class Emitter(JSONContributor):
    """Defines how particles are emitted."""
    lifetime: EmitterLifetime
    """Emitter lifetime. One of :class:`EmitterLifetimeOnce`, :class:`EmitterLifetimeExpression`, :class:`EmitterLifetimeLooping`"""
    rate: EmitterRate
    """Emission rate. One of :class:`EmitterRateInstant`, :class:`EmitterRateSteady`, :class:`EmitterRateManual`"""
    shape: EmitterShape
    """Emitter shape. One of :class:`EmitterShapePoint`, :class:`EmitterShapeDisc`, :class:`EmitterShapeSphere`, :class:`EmitterShapeBox`, :class:`EmitterShapeEntityAABB`"""
    localPosition: bool = False
    """Whether the particles inherit the local position space of their parent entity / locator. Only works on entity-attached particles."""
    localRotation: bool = False
    """Whether the particles inherit the local rotation space of their parent entity / locator. Only works when `localPosition` is true on entity-attached particles."""
    localVelocity: bool = False
    """Whether the particles inherit their initial velocity from their parent entity / locator. Only works on entity-attached particles."""
    emitterCreation: Molang | None = None
    """An expression that runs on emitter creation. Best place to put variable initialization for emitter variables."""
    emitterUpdate: Molang | None = None
    """An expression that runs \"once per emitter update\". Whatever that means."""
    
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