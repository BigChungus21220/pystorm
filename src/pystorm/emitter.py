from .common import JSONContributor, MolangValue, MolangInt, MolangNumber, MolangVector3, Molang, JSONContributions
from abc import ABC
from typing import Literal


class EmitterLifetime(JSONContributor, ABC):
    pass

class EmitterLifetimeExpression(EmitterLifetime):
    def __init__(self, activate: MolangValue = 1, expire: MolangValue = 0 ) -> None:
        super().__init__()
        self.activate = activate
        self.expire = expire
        
    def contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect.minecraft:emitter_lifetime_expression")
        contrib.contribute_or_default("activation_expression", self.activate, 1)
        contrib.contribute_or_default("expiration_expression", self.expire, 0)
        return contrib
    
class EmitterLifetimeLooping(EmitterLifetime):
    def __init__(self, activeTime: MolangValue = 10, sleepTime: MolangValue = 0 ) -> None:
        super().__init__()
        self.activeTime = activeTime
        self.sleepTime = sleepTime
        
    def contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect.minecraft:emitter_lifetime_looping")
        contrib.contribute("active_time", self.activeTime)
        contrib.contribute("sleep_time", self.sleepTime)
        return contrib
    
class EmitterLifetimeOnce(EmitterLifetime):
    def __init__(self, activeTime: MolangValue = 10 ) -> None:
        super().__init__()
        self.activeTime = activeTime
        
    def contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect.minecraft:emitter_lifetime_once")
        contrib.contribute("active_time", self.activeTime)
        return contrib



class EmitterRate(JSONContributor, ABC):
    pass

class EmitterRateInstant(EmitterRate):
    def __init__(self, particles: int | Molang = 1) -> None:
        super().__init__()
        self.particles = particles
        
    def contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect.minecraft:emitter_rate_instant")
        contrib.contribute("num_particles", self.particles)
        return contrib
    
class EmitterRateManual(EmitterRate):
    def __init__(self, maxParticles: MolangInt = 50) -> None:
        super().__init__()
        self.maxParticles = maxParticles
        
    def contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect.minecraft:emitter_rate_manual")
        contrib.contribute("max_particles", self.maxParticles)
        return contrib
    
class EmitterRateSteady(EmitterRate):
    def __init__(self, spawnRate: MolangNumber = 1, maxParticles: MolangInt = 50) -> None:
        super().__init__()
        self.maxParticles = maxParticles
        self.spawnRate = spawnRate
        
    def contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect.minecraft:emitter_rate_steady")
        contrib.contribute("spawn_rate", self.spawnRate)
        contrib.contribute("max_particles", self.maxParticles)
        return contrib



type EmitterShapeDirection = Literal["inwards", "outwards"] | MolangVector3

class EmitterShape(JSONContributor, ABC):
    pass

class EmitterShapeDisc(EmitterShape):
    def __init__(self, planeNormal: MolangVector3 = (0, 1, 0), offset: MolangVector3 = (0, 0, 0), radius: MolangNumber = 1, surfaceOnly: bool = False, direction: EmitterShapeDirection = "outwards") -> None:
        super().__init__()
        self.planeNormal = planeNormal
        self.offset = offset
        self.radius = radius
        self.surfaceOnly = surfaceOnly
        self.direction = direction
        
    def contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect.minecraft:emitter_shape_disk")
        contrib.contribute_or_default("plane_normal", self.planeNormal, (0, 1, 0))
        contrib.contribute_or_default("offset", self.offset, (0, 0, 0))
        contrib.contribute_or_default("radius", self.radius, 1)
        contrib.contribute_or_default("surface_only", self.surfaceOnly, False)
        contrib.contribute_or_default("direction", self.direction, "outwards")
        return contrib

class EmitterShapeBox(EmitterShape):
    def __init__(self, halfDimensions: MolangVector3, offset: MolangVector3 = (0, 0, 0), surfaceOnly: bool = False, direction: EmitterShapeDirection = "outwards") -> None:
        super().__init__()
        self.halfDimensions = halfDimensions
        self.offset = offset
        self.surfaceOnly = surfaceOnly
        self.direction = direction
        
    def contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect.minecraft:emitter_shape_box")
        contrib.contribute("half_dimensions", self.halfDimensions)
        contrib.contribute_or_default("offset", self.offset, (0, 0, 0))
        contrib.contribute_or_default("surface_only", self.surfaceOnly, False)
        contrib.contribute_or_default("direction", self.direction, "outwards")
        return contrib
    
class EmitterShapeEntityAABB(EmitterShape):
    def __init__(self, surfaceOnly: bool = False, direction: EmitterShapeDirection = "outwards") -> None:
        super().__init__()
        self.surfaceOnly = surfaceOnly
        self.direction = direction
        
    def contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect.minecraft:emitter_shape_entity_aabb")
        contrib.contribute_or_default("surface_only", self.surfaceOnly, False)
        contrib.contribute_or_default("direction", self.direction, "outwards")
        return contrib
    
class EmitterShapePoint(EmitterShape):
    def __init__(self, offset: MolangVector3 = (0, 0, 0), direction: MolangVector3 = (0, 0, 0)) -> None:
        super().__init__()
        self.offset = offset
        self.direction = direction
        
    def contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect.minecraft:emitter_shape_point")
        contrib.contribute_or_default("offset", self.offset, (0, 0, 0))
        contrib.contribute("direction", self.direction)
        return contrib

class EmitterShapeSphere(EmitterShape):
    def __init__(self, offset: MolangVector3 = (0, 0, 0), radius: MolangNumber = 1, surfaceOnly: bool = False, direction: EmitterShapeDirection = "outwards") -> None:
        super().__init__()
        self.offset = offset
        self.radius = radius
        self.surfaceOnly = surfaceOnly
        self.direction = direction
        
    def contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect.minecraft:emitter_shape_sphere")
        contrib.contribute_or_default("offset", self.offset, (0, 0, 0))
        contrib.contribute_or_default("radius", self.radius, 1)
        contrib.contribute_or_default("surface_only", self.surfaceOnly, False)
        contrib.contribute_or_default("direction", self.direction, "outwards")
        return contrib
    
    
    

class Emitter(JSONContributor):
    def __init__(self, lifetime: EmitterLifetime, rate: EmitterRate, shape: EmitterShape, localPosition: bool = False, localRotation: bool = False, localVelocity: bool = False):
        self.lifetime = lifetime
        self.rate = rate
        self.shape = shape
        self.localPosition = localPosition
        self.localRotation = localRotation
        self.localVelocity = localVelocity
    
    def contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect.minecraft:emitter_local_space")
        contrib.contribute_or_default("position", self.localPosition, False)
        contrib.contribute_or_default("rotation", self.localRotation, False)
        contrib.contribute_or_default("velocity", self.localVelocity, False)
        
        contrib.merge(self.lifetime.contributeJson())
        contrib.merge(self.rate.contributeJson())
        contrib.merge(self.shape.contributeJson())
        
        return contrib