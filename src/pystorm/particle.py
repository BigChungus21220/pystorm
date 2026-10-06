from .common import JSONContributor, JSONContributions
from .molang_types import MolangValue, MolangNumber, MolangVector3, Number, MolangVector2, Color
from abc import ABC
from typing import Literal
from dataclasses import dataclass, field

@dataclass
class ParticleLifetime(JSONContributor):
    maxLifetime: MolangValue
    expire: MolangValue = 0
    expireIn: list[str] = field(default_factory=list)
    surviveIn: list[str] = field(default_factory=list)
    killPlane: tuple[Number, Number, Number, Number] | None = None
        
    def _contributeJson(self) -> JSONContributions:
        contribExpireIn = JSONContributions()
        contribExpireIn.contribute_or_default("particle_effect#components#minecraft:particle_expire_if_in_blocks", self.expireIn, [])
        
        contribSurviveIn = JSONContributions()
        contribSurviveIn.contribute_or_default("particle_effect#components#minecraft:particle_expire_if_not_in_blocks", self.surviveIn, [])
        
        contribKillPlane = JSONContributions()
        contribKillPlane.contribute("particle_effect#components#minecraft:particle_kill_plane", self.killPlane)
        
        contribLifetime = JSONContributions("particle_effect#components#minecraft:particle_lifetime_expression")
        contribLifetime.contribute("max_lifetime", self.maxLifetime)
        contribLifetime.contribute_or_default("expiration_expression", self.expire, 0)
        
        contribLifetime.merge(contribExpireIn)
        contribLifetime.merge(contribSurviveIn)
        contribLifetime.merge(contribKillPlane)
        
        return contribLifetime



class ParticleRotation(JSONContributor, ABC):
    pass

@dataclass
class ParticleRotationDynamic(ParticleRotation):
    initialRotation: MolangNumber = 0
    initialVelocity: MolangNumber = 0
    acceleration: MolangNumber = 0
    drag: MolangNumber = 0
    
    def _contributeJson(self) -> JSONContributions:
        contrib_initial = JSONContributions("particle_effect#components#minecraft:particle_initial_spin")
        contrib_initial.contribute_or_default("rotation", self.initialRotation, 0)
        contrib_initial.contribute_or_default("rotation_rate", self.initialVelocity, 0)
        
        contrib = JSONContributions("particle_effect#components#minecraft:particle_motion_dynamic")
        contrib.contribute_or_default("rotation_acceleration", self.acceleration, 0)
        contrib.contribute_or_default("rotation_drag_coefficient", self.drag, 0)
        
        contrib.merge(contrib_initial)
        
        return contrib

@dataclass
class ParticleRotationParametric(ParticleRotation):
    rotation: MolangNumber = 0
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_motion_parametric")
        contrib.contribute_or_default("rotation", self.rotation, 0)
        return contrib



class ParticleTranslation(JSONContributor, ABC):
    pass

@dataclass
class ParticleTranslationDynamic(ParticleTranslation):
    initialSpeed: MolangNumber = 0
    acceleration: MolangVector3 = (0, 0, 0)
    drag: MolangNumber = 0
        
    def _contributeJson(self) -> JSONContributions:
        contrib_initial = JSONContributions()
        contrib_initial.contribute_or_default("particle_effect#components#minecraft:particle_initial_speed", self.initialSpeed, 0)
        
        contrib = JSONContributions("particle_effect#components#minecraft:particle_motion_dynamic")
        contrib.contribute_or_default("linear_acceleration", self.acceleration, (0, 0, 0))
        contrib.contribute_or_default("linear_drag_coefficent", self.drag, 0)
        
        contrib.merge(contrib_initial)
        
        return contrib

@dataclass
class ParticleTranslationParametric(ParticleTranslation):
    position: MolangVector3 = (0, 0, 0)
    direction: MolangVector3 | None = None
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_motion_parametric")
        contrib.contribute_or_default("relative_position", self.position, (0, 0, 0))
        contrib.contribute("direction", self.direction)
        
        return contrib



@dataclass
class ParticleCollision(JSONContributor):
    enabled: MolangValue = True
    drag: Number = 0
    restitution: Number = 0
    radius: Number = 0
    expireOnContact: bool = False
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_motion_collision")
        contrib.contribute_or_default("enabled", self.enabled, True)
        contrib.contribute("collision_drag", self.drag)
        contrib.contribute("coefficient_of_restitution", self.restitution)
        contrib.contribute("collision_radius", self.radius)
        contrib.contribute("expire_on_contact", self.expireOnContact)
        
        return contrib



class UVAnimation(JSONContributor, ABC):
    pass

@dataclass
class UVAnimationFPS(UVAnimation):
    uvStep: tuple[Number, Number]
    frameCount: MolangNumber
    fps: float
    loopFrames: bool = False
        
    def toLifetime(self) -> float:
        if isinstance(self.frameCount, float) or isinstance(self.frameCount, int):
            return self.frameCount/self.fps
        raise TypeError("This operation does not work with Molang frameCounts")
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard#uv#flipbook")
        contrib.contribute("step_UV", self.uvStep)
        contrib.contribute("max_frame", self.frameCount)
        contrib.contribute_or_default("loop", self.loopFrames, False)
        contrib.contribute("frames_per_second", self.fps)
        return contrib
        
@dataclass
class UVAnimationLifetime(UVAnimation):
    uvStep: tuple[Number, Number]
    frameCount: MolangNumber

    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard#uv#flipbook")
        contrib.contribute("step_UV", self.uvStep)
        contrib.contribute("max_frame", self.frameCount)
        contrib.contribute("stretch_to_lifetime", True)
        return contrib



@dataclass
class ParticleTexture(JSONContributor):
    texture: str
    textureSize: tuple[int, int]
    uv: MolangVector2
    uvSize: MolangVector2
    animation: UVAnimation | None = None
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard#uv")
        if self.animation is None:
            contrib.contribute("texture_width", self.textureSize[0])
            contrib.contribute("texture_height", self.textureSize[1])
            contrib.contribute("uv", self.uv)
            contrib.contribute("uv_size", self.uvSize)
        else:
            contrib.contribute("texture_width", self.textureSize[0])
            contrib.contribute("texture_height", self.textureSize[1])
            contrib.contribute("flipbook#base_UV", self.uv)
            contrib.contribute("flipbook#size_UV", self.uvSize)
            contrib.merge(self.animation._contributeJson())
            
        desc_contrib = JSONContributions()
        desc_contrib.contribute("particle_effect#description#basic_render_parameters#texture", self.texture)
        
        contrib.merge(desc_contrib)
            
        return contrib



class ParticleTint(JSONContributor, ABC):
    pass

@dataclass
class ParticleTintExpression(ParticleTint):
    color: Color
    
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_tinting")
        contrib.contribute("color", self.color)
        return contrib

@dataclass
class ParticleTintGradient(ParticleTint):
    interpolant: MolangNumber
    colors: dict[Number, Color]

    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_tinting#color")
        contrib.contribute("interpolant", self.interpolant)
        contrib.contribute("gradient", self.colors)
        return contrib



@dataclass
class ParticleMaterial(JSONContributor):
    material: str = "particles_alpha"
    recieveLighting: bool = False
    tint: ParticleTint | None = None
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions()
        contrib.contribute("particle_effect#description#basic_render_parameters#material", self.material)
        
        if self.recieveLighting:
            contrib.contribute("particle_effect#components#minecraft:particle_appearance_lighting", {})
            
        if self.tint is not None:
            contrib.merge(self.tint._contributeJson())
        
        return contrib



type FacingMode = Literal[
    "rotate_xyz", 
    "rotate_y", 
    "lookat_xyz", 
    "lookat_y", 
    "direction_x", 
    "direction_y", 
    "direction_z", 
    "emitter_transform_xy", 
    "emitter_transform_xz", 
    "emitter_transform_yz",
    "lookat_direction"
]

class ParticleFacing(JSONContributor, ABC):
    pass

@dataclass
class ParticleFacingVelocity(ParticleFacing):
    facingMode: FacingMode = "rotate_xyz"
    minVelocity: Number = 0.01
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard")
        contrib.contribute("facing_camera_mode", self.facingMode)
        contrib.contribute("direction#mode", "derive_from_velocity")
        contrib.contribute("direction#min_speed_threshold", self.minVelocity)
        return contrib

@dataclass
class ParticleFacingExpression(ParticleFacing):
    facingMode: FacingMode = "rotate_xyz"
    direction: MolangVector3 = (0, 1, 0)
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard")
        contrib.contribute("facing_camera_mode", self.facingMode)
        contrib.contribute("direction#mode", "custom")
        contrib.contribute("direction#custom_direction", self.direction)
        
        return contrib



@dataclass
class ParticleAppearance(JSONContributor):
    texture: ParticleTexture
    material: ParticleMaterial
    size: MolangVector2
    facing: ParticleFacing
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard")
        contrib.contribute("size", self.size)
        
        contrib.merge(self.texture._contributeJson())
        contrib.merge(self.material._contributeJson())
        contrib.merge(self.facing._contributeJson())
        
        return contrib



@dataclass
class Particle(JSONContributor):
    lifetime: ParticleLifetime
    motion: ParticleTranslation
    rotation: ParticleRotation
    appearance: ParticleAppearance
    collision: ParticleCollision | None = None
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions()
        
        contrib.merge(self.lifetime._contributeJson())
        contrib.merge(self.motion._contributeJson())
        contrib.merge(self.rotation._contributeJson())
        contrib.merge(self.appearance._contributeJson())
        
        if self.collision is not None:
            contrib.merge(self.collision._contributeJson())
        
        return contrib