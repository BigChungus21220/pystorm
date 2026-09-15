from .common import JSONContributor, MolangValue, MolangInt, MolangNumber, MolangVector3, Molang, JSONContributions, Number, MolangVector2, Color
from abc import ABC
from typing import Literal


class ParticleLifetime(JSONContributor):
    def __init__(self, maxLifetime: MolangValue, expire: MolangValue = 0, expireIn: list[str] = [], surviveIn: list[str] = [], killPlane: tuple[Number, Number, Number, Number] | None = None) -> None:
        super().__init__()
        self.maxLifetime = maxLifetime
        self.expire = expire
        self.expireIn = expireIn
        self.surviveIn = surviveIn
        self.killPlane = killPlane
        
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

class ParticleRotationDynamic(ParticleRotation):
    def __init__(self, initialRotation: MolangNumber = 0, initialVelocity: MolangNumber = 0, acceleration: MolangNumber = 0, drag: MolangNumber = 0) -> None:
        super().__init__()
        self.initialRotation = initialRotation
        self.initialVelocity = initialVelocity
        self.acceleration = acceleration
        self.drag = drag
        
    def _contributeJson(self) -> JSONContributions:
        contrib_initial = JSONContributions("particle_effect#components#minecraft:particle_initial_spin")
        contrib_initial.contribute_or_default("rotation", self.initialRotation, 0)
        contrib_initial.contribute_or_default("rotation_rate", self.initialVelocity, 0)
        
        contrib = JSONContributions("particle_effect#components#minecraft:particle_motion_dynamic")
        contrib.contribute_or_default("rotation_acceleration", self.acceleration, 0)
        contrib.contribute_or_default("rotation_drag_coefficient", self.drag, 0)
        
        contrib.merge(contrib_initial)
        
        return contrib

class ParticleRotationParametric(ParticleRotation):
    def __init__(self, rotation: MolangNumber = 0) -> None:
        super().__init__()
        self.rotation = rotation
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_motion_parametric")
        contrib.contribute_or_default("rotation", self.rotation, 0)
        return contrib



class ParticleTranslation(JSONContributor, ABC):
    pass

class ParticleTranslationDynamic(ParticleTranslation):
    def __init__(self, initialSpeed: MolangNumber = 0, acceleration: MolangVector3 = (0, 0, 0), drag: MolangNumber = 0) -> None:
        super().__init__()
        self.initialSpeed = initialSpeed
        self.acceleration = acceleration
        self.drag = drag
        
    def _contributeJson(self) -> JSONContributions:
        contrib_initial = JSONContributions()
        contrib_initial.contribute_or_default("particle_effect#components#minecraft:particle_initial_speed", self.initialSpeed, 0)
        
        contrib = JSONContributions("particle_effect#components#minecraft:particle_motion_dynamic")
        contrib.contribute_or_default("linear_acceleration", self.acceleration, 0)
        contrib.contribute_or_default("linear_drag_coefficent", self.drag, 0)
        
        contrib.merge(contrib_initial)
        
        return contrib

class ParticleTranslationParametric(ParticleTranslation):
    def __init__(self, position: MolangVector3 = (0, 0, 0), direction: MolangVector3 | None = None) -> None:
        super().__init__()
        self.position = position
        self.direction = direction
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_motion_parametric")
        contrib.contribute_or_default("relative_position", self.position, (0, 0, 0))
        contrib.contribute("direction", self.direction)
        
        return contrib



class ParticleCollision(JSONContributor):
    def __init__(self, enabled: MolangValue = True, drag: Number = 0, restitution: Number = 0, radius: Number = 0, expireOnContact: bool = False) -> None:
        super().__init__()
        self.enabled = enabled
        self.drag = drag
        self.restitution = restitution
        self.radius = radius
        self.expireOnContact = expireOnContact
        
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

class UVAnimationFPS(UVAnimation):
    def __init__(self, uvStep: tuple[Number, Number], frameCount: MolangNumber, fps: float, loopFrames: bool = False) -> None:
        super().__init__()
        self.uvStep = uvStep
        self.frameCount = frameCount
        self.fps = fps
        self.loopFrames = loopFrames
        
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
        
class UVAnimationLifetime(UVAnimation):
    def __init__(self, uvStep: tuple[Number, Number], frameCount: MolangNumber) -> None:
        super().__init__()
        self.uvStep = uvStep
        self.frameCount = frameCount

    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard#uv#flipbook")
        contrib.contribute("step_UV", self.uvStep)
        contrib.contribute("max_frame", self.frameCount)
        contrib.contribute("stretch_to_lifetime", True)
        return contrib



class ParticleTexture(JSONContributor):
    def __init__(self, texture: str, textureSize: tuple[int, int], uv: MolangVector2, uvSize: MolangVector2, animation: UVAnimation | None = None) -> None:
        super().__init__()
        self.texture = texture
        self.textureSize = textureSize
        self.uv = uv
        self.uvSize = uvSize
        self.animation = animation
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard#uv")
        if self.animation == None:
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

class ParticleTintExpression(ParticleTint):
    def __init__(self, color: Color) -> None:
        super().__init__()
        self.color = color
    
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_tinting")
        contrib.contribute("color", self.color)
        return contrib
    
class ParticleTintGradient(ParticleTint):
    def __init__(self, interpolant: MolangNumber, colors: dict[Number, Color]) -> None:
        super().__init__()
        self.interpolant = interpolant
        self.colors = colors

    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_tinting#color")
        contrib.contribute("interpolant", self.interpolant)
        contrib.contribute("gradient", self.colors)
        return contrib



class ParticleMaterial(JSONContributor):
    def __init__(self, material: str = "particles_alpha", recieveLighting: bool = False, tint: ParticleTint | None = None) -> None:
        super().__init__()
        self.material = material
        self.recieveLighting = recieveLighting
        self.tint = tint
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions()
        contrib.contribute("particle_effect#description#basic_render_parameters#material", self.material)
        
        if self.recieveLighting:
            contrib.contribute("particle_effect#components#minecraft:particle_appearance_lighting", {})
            
        if self.tint != None:
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

class ParticleFacingVelocity(ParticleFacing):
    def __init__(self, facingMode: FacingMode = "rotate_xyz", minVelocity: Number = 0.01) -> None:
        super().__init__()
        self.facingMode = facingMode
        self.minVelocity = minVelocity
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard")
        contrib.contribute("facing_camera_mode", self.facingMode)
        contrib.contribute("direction#mode", "derive_from_velocity")
        contrib.contribute("direction#min_speed_threshold", self.minVelocity)
        return contrib
    
class ParticleFacingExpression(ParticleFacing):
    def __init__(self, facingMode: FacingMode = "rotate_xyz", direction: MolangVector3 = (0, 1, 0)) -> None:
        super().__init__()
        self.facingMode = facingMode
        self.direction = direction
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard")
        contrib.contribute("facing_camera_mode", self.facingMode)
        contrib.contribute("direction#mode", "custom")
        contrib.contribute("direction#custom_direction", self.direction)
        
        return contrib



class ParticleAppearance(JSONContributor):
    def __init__(self, texture: ParticleTexture, material: ParticleMaterial, size: MolangVector2, facing: ParticleFacing) -> None:
        super().__init__()
        self.texture = texture
        self.material = material
        self.size = size
        self.facing = facing
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard")
        contrib.contribute("size", self.size)
        
        contrib.merge(self.texture._contributeJson())
        contrib.merge(self.material._contributeJson())
        contrib.merge(self.facing._contributeJson())
        
        return contrib



class Particle(JSONContributor):
    def __init__(self, lifetime: ParticleLifetime, motion: ParticleTranslation, rotation: ParticleRotation, appearance: ParticleAppearance, collision: ParticleCollision | None = None) -> None:
        super().__init__()
        self.lifetime = lifetime
        self.motion = motion
        self.rotation = rotation
        self.collision = collision
        self.appearance = appearance
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions()
        
        contrib.merge(self.lifetime._contributeJson())
        contrib.merge(self.motion._contributeJson())
        contrib.merge(self.rotation._contributeJson())
        contrib.merge(self.appearance._contributeJson())
        
        if self.collision != None:
            contrib.merge(self.collision._contributeJson())
        
        return contrib