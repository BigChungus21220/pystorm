from .common import JSONContributor, JSONContributions
from .molang_types import MolangValue, MolangNumber, MolangVector3, Number, MolangVector2, Color
from abc import ABC
from typing import Literal
from dataclasses import dataclass, field

@dataclass
class ParticleLifetime(JSONContributor):
    """Lifetime of particle."""
    maxLifetime: MolangValue
    """Max particle lifetime (seconds). Eval once."""
    expire: MolangValue = 0
    """Expiration expression. Particle expires when this is true. Eval per frame."""
    expireIn: list[str] = field(default_factory=list)
    """Blocks this particle will despawn in. Precedence over `surviveIn` undocumented."""
    surviveIn: list[str] = field(default_factory=list)
    """Blocks this particle will not despawn in. Precedence over `expireIn` undocumented."""
    killPlane: tuple[Number, Number, Number, Number] | None = None
    """If the particle crosses this plane it despawns. Defined by `Ax + By + Cz + D = 0`. Let `n = (A,B,C)`, then if `length(n) = 1`, `n` is the plane normal and `-Dn` is a point on the plane."""
        
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
    """Base class for particle rotation modes. Use :class:`ParticleRotationDynamic` or :class:`ParticleRotationParametric` instead."""
    pass

@dataclass
class ParticleRotationDynamic(ParticleRotation):
    """Rotation defined by motion parameters"""
    initialRotation: MolangNumber = 0
    """Starting rotation of the particle (degrees). Eval once."""
    initialVelocity: MolangNumber = 0
    """Initial rotational velocity of the particle (degrees/second). Eval once."""
    acceleration: MolangNumber = 0
    """Rotational acceleration of the particle (degrees/second^2). Eval per frame."""
    drag: MolangNumber = 0
    """Rotational drag (unitless). Eval undocumented. Applies as `rotation_acceleration -= rotation_rate*rotation_drag_coefficient`"""
    
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
    """Rotation defined by a molang expression."""
    rotation: MolangNumber = 0
    """Particle rotation. Eval per frame."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_motion_parametric")
        contrib.contribute_or_default("rotation", self.rotation, 0)
        return contrib



class ParticleTranslation(JSONContributor, ABC):
    """Base class for particle translation (movement) modes. Use :class:`ParticleTranslationDynamic` or :class:`ParticleTranslationParametric` instead."""
    pass

@dataclass
class ParticleTranslationDynamic(ParticleTranslation):
    """Translation defined by motion parameters."""
    direction: Literal["inwards", "outwards"] | MolangVector3 = "outwards"
    """Initial velocity direction. Eval once."""
    initialSpeed: MolangNumber = 0
    """Initial velocity magnitude (blocks/sec). Eval once."""
    acceleration: MolangVector3 = (0, 0, 0)
    """Acceleration vector (blocks/sec^2). Eval per frame."""
    drag: MolangNumber = 0
    """Linear drag. Eval per frame. Applied as `acceleration -= linear_drag_coefficient*velocity`"""
        
    def _contributeJson(self) -> JSONContributions:
        contrib_initial = JSONContributions()
        contrib_initial.contribute_or_default("particle_effect#components#minecraft:particle_initial_speed", self.initialSpeed, 0)
        
        contrib = JSONContributions("particle_effect#components#minecraft:particle_motion_dynamic")
        contrib.contribute_or_default("linear_acceleration", self.acceleration, (0, 0, 0))
        contrib.contribute_or_default("linear_drag_coefficient", self.drag, 0)
        
        contrib_shape = JSONContributions("particle_effect#components")
        contrib_shape.contribute_or_default("minecraft:emitter_shape_disk?direction", self.direction, "outwards")
        contrib_shape.contribute_or_default("minecraft:emitter_shape_box?direction", self.direction, "outwards")
        contrib_shape.contribute_or_default("minecraft:emitter_shape_entity_aabb?direction", self.direction, "outwards")
        contrib_shape.contribute_or_default("minecraft:emitter_shape_point?direction", self.direction, "outwards")
        contrib_shape.contribute_or_default("minecraft:emitter_shape_sphere?direction", self.direction, "outwards")
        
        contrib.merge(contrib_initial)
        
        return contrib

@dataclass
class ParticleTranslationParametric(ParticleTranslation):
    """Translation defined by a molang expression. May be buggy."""
    position: MolangVector3 = (0, 0, 0)
    """Particle translation relative to the emitter. If used as an attached particle without `localPosition = true`, position is relative to the world origin. Eval per frame."""
    direction: MolangVector3 | None = None
    """Particle orientation for use with :class:`ParticleFacingVelocity` (I think). Eval per frame."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_motion_parametric")
        contrib.contribute_or_default("relative_position", self.position, (0, 0, 0))
        contrib.contribute("direction", self.direction)
        
        return contrib



@dataclass
class ParticleCollision(JSONContributor):
    """Particle collision parameters."""
    enabled: MolangValue = True
    """Whether to do collisions. Eval per frame."""
    drag: Number = 0
    """Drag while in contact with the surface. Units claim to be blocks/second, but this doesn't make sense."""
    restitution: Number = 0
    """Proportion of speed retained on impact. `speed' = |speed*restitution|`"""
    radius: Number = 0
    """Collision radius."""
    expireOnContact: bool = False
    """Whether the particle should expire on collision."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_motion_collision")
        contrib.contribute_or_default("enabled", self.enabled, True)
        contrib.contribute("collision_drag", self.drag)
        contrib.contribute("coefficient_of_restitution", self.restitution)
        contrib.contribute("collision_radius", self.radius)
        contrib.contribute("expire_on_contact", self.expireOnContact)
        
        return contrib



class UVAnimation(JSONContributor, ABC):
    """Animation mode base class. Use :class:`UVAnimationFPS` or :class:`UVAnimationLifetime`"""
    pass

@dataclass
class UVAnimationFPS(UVAnimation):
    """Animation with a set fps."""
    uvStep: tuple[Number, Number]
    """Pixels in each direction to step each frame."""
    frameCount: MolangNumber
    """Total number of frames."""
    fps: float
    """Frames per second."""
    loopFrames: bool = False
    """Whether to loop the animation or hold on the last frame."""
        
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
    """Animation which stretches to the particle lifetime."""
    uvStep: tuple[Number, Number]
    """Pixels in each direction to step each frame."""
    frameCount: MolangNumber
    """Total number of frames."""

    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard#uv#flipbook")
        contrib.contribute("step_UV", self.uvStep)
        contrib.contribute("max_frame", self.frameCount)
        contrib.contribute("stretch_to_lifetime", True)
        return contrib



@dataclass
class ParticleTexture(JSONContributor):
    """Descriptor for the particle's texture."""
    texture: str
    """Texture resource path. Eg: `textures/particle/particles`"""
    textureSize: tuple[int, int]
    """Size of the texture in pixels."""
    uv: MolangVector2
    """Top left corner of first frame in pixels if `animation != None`, evaluated once. Otherwise the top left corner of the uv, evaluated per frame."""
    uvSize: MolangVector2
    """Size of each frame in pixels. Eval per frame."""
    animation: UVAnimation | None = None
    """Animation mode. None for a static texture"""
        
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
    """Base class for animation modes. Use :class:`ParticleTintExpression` or :class:`ParticleTintGradient` instead."""
    pass

@dataclass
class ParticleTintExpression(ParticleTint):
    """Particle tint defined by a molang expression."""
    color: Color
    """Color tint applied by multiplication. (0,0,0,0) is black, 0 opacity, (1,1,1,1) is white, full opacity. Eval per frame."""
    
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_tinting")
        contrib.contribute("color", self.color)
        return contrib

@dataclass
class ParticleTintGradient(ParticleTint):
    """Particle tint defined by a gradient."""
    interpolant: MolangNumber
    """Interpolant or \"time\" value. Eval per frame."""
    colors: dict[Number, Color]
    """Keyframes to interpolate between. If you define a color at 0.5, and `interpolant = 0.5`, then the tint will be the color at 0.5. The interpolation method is not documented."""

    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_tinting#color")
        contrib.contribute("interpolant", self.interpolant)
        contrib.contribute("gradient", self.colors)
        return contrib



@dataclass
class ParticleMaterial(JSONContributor):
    """Particle material properties."""
    material: str = "particles_alpha"
    """Material to use. Vanilla options are `particles_alpha`, `particles_blend`, `particles_add`, `particles_opaque`, but others can be defined (see https://wiki.bedrock.dev/visuals/materials)."""
    recieveLighting: bool = False
    """Whether lighting should be applied to this particle. Keep disabled for glowing particles."""
    tint: ParticleTint | None = None
    """A tint to apply to the particle."""
        
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
"""Defines how a particle is oriented. \n
rotate_xyz - Particle plane aligns with camera plane.\n
rotate_y - Particle plane aligns with camera plane, maintaining the y-axis as a tangent vector. \n
lookat_xyz - Particle rotates to face camera. \n
lookat_y - Particle rotates to face camera, maintaining the y-axis as a tangent vector. \n
direction_x - Particle faces +x direction. \n
direction_y - Particle faces +y direction. \n
direction_z - Particle faces +z direction or the vector defined as the particle direction. \n
emitter_transform_xy - Face tangent to emitter xy plane. \n
emitter_transform_xz - Face tangent to emitter xz plane. \n
emitter_transform_yz - Face tangent to emitter yz plane. \n
lookat_direction - Like lookat_y, but particle faces the vector defined as the particle direction. \n
"""

class ParticleFacing(JSONContributor, ABC):
    """Base class for particle facing modes. Use :class:`ParticleFacingVelocity` or :class:`ParticleFacingExpression` instead."""
    pass

@dataclass
class ParticleFacingVelocity(ParticleFacing):
    """Particle facing defined by velocity."""
    facingMode: FacingMode = "rotate_xyz"
    """How to orient the particle with respect to the camera / world. Note: not all support orientation by direction/velocity. See :class:`FacingMode`."""
    minVelocity: Number = 0.01
    """Minimum velocity to apply an orientation. Defaults to (0, 0, 1) when velocity is too low."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard")
        contrib.contribute("facing_camera_mode", self.facingMode)
        contrib.contribute("direction#mode", "derive_from_velocity")
        contrib.contribute("direction#min_speed_threshold", self.minVelocity)
        return contrib

@dataclass
class ParticleFacingExpression(ParticleFacing):
    """Particle facing defined by custom direction."""
    facingMode: FacingMode = "rotate_xyz"
    """How to orient the particle with respect to the camera / world. Note: not all support orientation by direction/velocity. See :class:`FacingMode`."""
    direction: MolangVector3 = (0, 1, 0)
    """Direction vector. If `facingMode = \"direction_z\"`, this direction defines the normal of the particle plane."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard")
        contrib.contribute("facing_camera_mode", self.facingMode)
        contrib.contribute("direction#mode", "custom")
        contrib.contribute("direction#custom_direction", self.direction)
        
        return contrib



@dataclass
class ParticleAppearance(JSONContributor):
    """Defines particle appearance."""
    texture: ParticleTexture
    """Particle texture descriptor."""
    size: MolangVector2
    """Half size of particle rect in blocks."""
    facing: ParticleFacing = field(default_factory=ParticleFacingExpression)
    """Particle facing mode."""
    material: ParticleMaterial = field(default_factory=ParticleMaterial)
    """Particle material properties."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions("particle_effect#components#minecraft:particle_appearance_billboard")
        contrib.contribute("size", self.size)
        
        contrib.merge(self.texture._contributeJson())
        contrib.merge(self.material._contributeJson())
        contrib.merge(self.facing._contributeJson())
        
        return contrib



@dataclass
class Particle(JSONContributor):
    """Particle behavior and appearance."""
    lifetime: ParticleLifetime
    """Particle despawning rules."""
    appearance: ParticleAppearance
    """Particle appearance settings."""
    motion: ParticleTranslation = field(default_factory=ParticleTranslationDynamic)
    """Particle motion settings."""
    rotation: ParticleRotation = field(default_factory=ParticleRotationDynamic)
    """Particle rotation settings."""
    collision: ParticleCollision | None = None
    """Particle collision settings."""
        
    def _contributeJson(self) -> JSONContributions:
        contrib = JSONContributions()
        
        contrib.merge(self.lifetime._contributeJson())
        contrib.merge(self.motion._contributeJson())
        contrib.merge(self.rotation._contributeJson())
        contrib.merge(self.appearance._contributeJson())
        
        if self.collision is not None:
            contrib.merge(self.collision._contributeJson())
        
        return contrib