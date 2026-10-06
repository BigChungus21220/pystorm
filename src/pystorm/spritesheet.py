import aseprite_reader
import io
from pathlib import Path
from PIL import Image, ImageSequence
from .molang_types import Number
from .particle import ParticleTexture, UVAnimationFPS, UVAnimationLifetime, ParticleAppearance
from typing import Literal, Any, Self
import numpy as np
import numpy.typing as npt
from dataclasses import dataclass
from collections.abc import Buffer, Sequence

class _InMemoryPath:
    """Tricks libraries expecting a pathlib.Path into reading from memory."""
    def __init__(self, data: bytes):
        self.data = data
        
    def open(self, *args, **kwargs):
        return io.BytesIO(self.data)
    
    def exists(self): return True
    def is_file(self): return True
    
class _NamedBytesIO(io.BytesIO, Buffer):
    """Tricks libraries expecting a pathlib.Path into writing to memory."""
    
    def __buffer__(self, flags: int) -> memoryview:
        return self.getbuffer()
    
    @property
    def suffix(self):
        return ".png"
        
    @property
    def name(self):
        return "memory_frame.png"
        
    def open(self, mode="wb", *args, **kwargs):
        return self
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
    
    def exists(self): return False
    def is_file(self): return True

type ImageConvertible = str | Path | bytes | Buffer | np.ndarray[tuple[int, int], np.dtype[Any]] | np.ndarray[tuple[int, int, int], np.dtype[Any]]
type FramesConvertible = ImageConvertible | np.ndarray[tuple[int, int, int, int], np.dtype[Any]] | Sequence[ImageConvertible]
type FramesType = np.ndarray[tuple[int, int, int, int], np.dtype[np.uint8]]
"""`frameCount x width x height x channels` **Watch out for width / height ordering conventions when using.**"""

def normalizeImageFrames(data: FramesConvertible, float_max_value: float = 1.0) -> FramesType:
    """
    Converts a file path, image bytes, a numpy array to a numpy array of frames, or a list of things convertible to single frames to a numpy array of frames.

    Args:
        data (framesConvertible):
        float_max_value (float, optional): The maximum value use when mapping floats to uint8. Defaults to 1.0.

    Returns:
        framesType: A `frameCount x width x height x channels` array. **Watch out for width / height ordering conventions when using.**
    """

    if isinstance(data, Path) or isinstance(data, str):
        with open(data, "rb") as file:
            data = file.read()
            
    if isinstance(data, np.ndarray):
        if data.ndim >= 2 and data.ndim <= 4:
            if np.issubdtype(data.dtype, np.floating):
                arr = (data/float_max_value*255).astype(np.uint8)
            elif np.issubdtype(data.dtype, np.integer):
                arr = (data//(np.iinfo(data.dtype).max//255)).astype(np.uint8)
            else:
                raise ValueError(f"Array dtype not compatible. Expected integer or float, got {data.dtype}")
            
            if arr.ndim == 2:
                return arr[None, :, :, None] # type: ignore
            elif arr.ndim == 3:
                if arr.shape[-1] <= 4:
                    return arr[None, :, :, :] # type: ignore
                else:
                    return arr[:, :, :, None] # type: ignore
            
            return arr # type: ignore
            
        else:
            raise ValueError(f"Invalid array shape. (expected 2, 3, or 4 dimensions, got {data.ndim})")
            
    
    elif isinstance(data, bytes) or isinstance(data, Buffer):
        img = Image.open(io.BytesIO(data))
        
        if img.mode in ('RGBA', 'LA', 'PA') or (img.mode == 'P' and 'transparency' in img.info):
            target_mode = 'RGBA'
            target_channels = 4
        elif img.mode in ('L', '1', 'I', 'F'):
            target_mode = 'L'
            target_channels = 1
        else:
            target_mode = 'RGB'
            target_channels = 3
        
        frames = np.empty((getattr(img, "n_frames", 1), img.width, img.height, target_channels), dtype=np.uint8)
        i = 0
        for frame in ImageSequence.Iterator(img):
            converted_frame = frame.convert(target_mode)
            arr = np.array(converted_frame)
        
            if arr.ndim == 2:
                arr = arr[:,:,None]
            
            frames[i,:,:,:] = arr.transpose((1,0,2))
            i += 1

        return frames
    
    elif isinstance(data, Sequence):
        frames: np.ndarray | None = None
        i = 0
        for frame in data:
            image = normalizeImageFrames(frame)
            if image.shape[0] != 1: raise ValueError(f"Image for frame {i} contains multiple frames")
            if frames is None:
                frames = np.empty((len(data), image.shape[1], image.shape[2], image.shape[3]), dtype=np.uint8)
            else:
                if image.shape[1:] != frames.shape[1:]: raise ValueError(f"Image sizes in sequence must match. Size of frame 0 does not match frame {i}")
            #print(frames.shape)
            #print(image.shape)
            frames[i, :, :, :] = image
            i += 1
            
        if frames is None: raise ValueError(f"No frames in input")
        return frames

type Orientation = Literal["horizontal", "vertical"]


@dataclass
class SpriteSheet:
    """
    A spritesheet convertible to a :class:`ParticleTexture`
    """
    
    frames: FramesType
    """Frames of the animation. Can be safely modified"""
    uvStart: tuple[int, int] = (0,0)
    """The top left corner of the first frame. Do Not Modify"""
    tileDirection: Orientation = "horizontal"
    """How to tile frames of the animation"""
    _texture_size: tuple[int, int] | None = None
    
    @property
    def uvSize(self) -> tuple[int, int]:
        """Size of each frame"""
        return self.frames.shape[1:3]
    
    @property
    def frameCount(self) -> int:
        """Number of frames"""
        return self.frames.shape[0]
    
    @property
    def uvStep(self):
        """Pixels to step each frame"""
        return (self.uvSize[0], 0) if self.tileDirection == "horizontal" else (0, self.uvSize[1])
    
    @property
    def textureSize(self) -> tuple[int, int]:
        """Size of this animation on the texture"""
        if self._texture_size is None:
            return (self.uvSize[0] + self.uvStep[0]*(self.frameCount - 1), self.uvSize[1] + self.uvStep[1]*(self.frameCount - 1))
        else:
            return self._texture_size
    
    @property
    def channels(self) -> int:
        """Number of channels"""
        return self.frames.shape[3]
    
    @classmethod
    def fromFrames(cls, frames: FramesConvertible, tileDirection: Orientation = "horizontal"):
        """Constructs a spritesheet from frames

        Args:
            frames (framesConvertible):
            tileDirection (Orientation], optional): Direction to layout frames on the spritesheet. Defaults to "horizontal".
        """
        frames = normalizeImageFrames(frames)
        return cls(frames, (0,0), tileDirection)
        
    @classmethod
    def fromImage(cls, image: ImageConvertible, uvSize: tuple[int, int], frameCount: int, tileDirection: Orientation = "horizontal"):
        """Constructs a spritesheet from a spritesheet image

        Args:
            image (imageConvertible):
            uvStart (tuple[int, int]): Top left corner of first frame
            uvSize (tuple[int, int]): Size of each frame
            frameCount (int): Number of frames
            tileDirection (Orientation], optional): Direction to layout frames on the spritesheet. Defaults to "horizontal"
        """
        
        arr = normalizeImageFrames(image) # 1, w, h, c
        if arr.shape[0] != 1: raise ValueError("Image contains multiple layers / frames")
                
        tw, th = uvSize
        c = arr.shape[3]
        
        if tileDirection == "horizontal":
            strip = arr[0, 0 : tw * frameCount, 0 : th, :]
            frames = strip.reshape((frameCount, tw, th, c)).copy()
            
        else:
            strip = arr[0, 0 : tw, 0 : th * frameCount, :]
            frames = strip.reshape((tw, frameCount, th, c)).transpose((1,0,2,3)).copy()
        
        return cls(frames, (0,0), tileDirection)
    
    @classmethod
    def fromASE(cls, ase: bytes | Path | str, tileDirection: Orientation = "horizontal"):
        """Constructs a spritesheet from an Aseprite file

        Args:
            ase (bytes | Path | str): Aseprite file bytes or path
            tileDirection (Orientation, optional): Direction to layout frames on the spritesheet. Defaults to "horizontal".
        """
        if isinstance(ase, Path) or isinstance(ase, str):
            with open(ase, "rb") as file:
                ase = file.read()
        
        ase_buff = _InMemoryPath(ase)
        try:
            ase_file = aseprite_reader.AsepriteFile(ase_buff) # type: ignore
        except NotImplementedError:
            raise NotImplementedError("aseprite-reader does not support linked cels. Unlink them in Aseprite first (see https://www.aseprite.org/docs/linked-cels/#unlink-cels)")
        frame_count = len(ase_file.frames)
        
        frames = [_NamedBytesIO() for _ in range(frame_count)]
        for i, (_, frame) in enumerate(ase_file.iter_frames()):
            ase_file.render(frame, frames[i]) # type: ignore
            frames[i].seek(0)
        
        return cls.fromFrames(frames, tileDirection=tileDirection)
    
    def halfSize(self) -> tuple[float, float]:
        """The half dimensions of the particle to match Minecraft's pixel size. Use directly with :method:`ParticleAppearance`.

        Returns:
            tuple[float, float]:
        """
        return (self.frames.shape[1]/32.0, self.frames.shape[2]/32.0)
    
    def texture(self):
        """Texture as a `(f*w, h, c)` or `(w, f*h, c)` numpy array (depending on `tileDirection`)"""
        size = self.textureSize
        return self.frames.reshape((size[0], size[1], self.channels))
        
    def pngBytes(self):
        """Returns a the bytes of the png for the texture"""
        byte_arr = io.BytesIO()
        Image.fromarray(self.texture().transpose(1,0,2)).save(byte_arr, format='PNG')
        return byte_arr.getvalue()
    
    def saveImage(self, path: Path | str):
        """Saves the spritesheet as a single texture. **Will be invalid after calling SpriteAtlas.texture() with this spritesheet in the atlas**
        
        Args:
            path (Path | str): The file to save this texture to.
        """
        Image.fromarray(self.texture().transpose(1,0,2)).save(path)
    
    def textureFPS(self, path: str, fps: Number, loop: bool = False):
        """The texture descriptor for a particle effect whose animation stretches to it's lifetime

        Args:
            path (str): The path to where this texture will be stored in the resource pack. Eg: `textures/particle/particles`
            fps (Number): Frames per second of the animation
            loop: (bool, optional): Whether the animation loops to the start. Defaults to False.
        """
        return ParticleTexture(
            texture = path,
            textureSize = self.textureSize,
            uv = self.uvStart,
            uvSize = self.uvSize,
            animation = UVAnimationFPS(
                uvStep = (self.uvSize[0], 0),
                frameCount= self.frameCount,
                fps = fps,
                loopFrames = loop
            )
        )
    
    def textureLifetime(self, path: str):
        """The texture descriptor for a particle effect whose animation stretches to it's lifetime

        Args:
            path (str): The path to where this texture will be stored in the resource pack. Eg: `textures/particle/particles`
        """
        return ParticleTexture(
            texture = path,
            textureSize = self.textureSize,
            uv = self.uvStart,
            uvSize = self.uvSize,
            animation = UVAnimationLifetime(
                uvStep = (self.uvSize[0], 0),
                frameCount= self.frameCount
            )
        )
    
    def textureStatic(self, path: str):
        """The texture descriptor for a particle effect with a static texture

        Args:
            path (str): The path to where this texture will be stored in the resource pack. Eg: `textures/particle/particles`
        """
        return ParticleTexture(
            texture = path,
            textureSize = self.textureSize,
            uv = self.uvStart,
            uvSize = self.uvSize
        )
        
class SpriteAtlas:
    """
    A collection of spritesheets on the same texture.
    All spritesheets must have the same orientation.
    **IMPORTANT: call SpriteAtlas.texture() before generating particle**
    """
    
    sprites: list[SpriteSheet]
    
    def __init__(self, sprites: list[SpriteSheet] = [], textureSize: tuple[int, int] | None = None):
        """
        **IMPORTANT: call SpriteAtlas.texture() before generating particle**
        Args:
            sprites (list[SpriteSheet], optional): List of spritesheets to place on this atlas. Defaults to [].
            textureSize (tuple[int, int] | None, optional): A texture size to use. An error is thrown if your texture won't fit. Defaults to None.
        """
        self.sprites = sprites
        self.textureSize = textureSize
    
    def texture(self):
        """Gets the texture as a (w, h, c) np array. **IMPORTANT: call before generating particle**"""
        if len(self.sprites) > 0: raise ValueError("No spritesheets added to atlas")
        
        H = self.sprites[0].tileDirection == "horizontal"
        
        w = 0
        h = 0
        c = 1
        for sprite in self.sprites:
            if H:
                w = max(w, sprite.textureSize[0])
                h += sprite.textureSize[1]
            else:
                w += sprite.textureSize[0]
                h = max(h, sprite.textureSize[1])
            c = max(c, sprite.channels)
        
        if self.textureSize is not None: 
            if w > self.textureSize[0] or h > self.textureSize[1]:
                raise ValueError(f"Spritesheets do not fit on specified texture size")
            w = self.textureSize[0]
            h = self.textureSize[1]
        
        texture = np.zeros((w, h, c), dtype=np.uint8)
        pos = 0
        for sprite in self.sprites:
            sprite.uvStart = (0, pos) if H else (pos, 0)
            sprite._texture_size = (w, h)
            ox, oy = sprite.uvStart
            sx, sy = sprite.textureSize
            texture[ox:ox + sx, oy:oy + sy, :] = sprite.texture # type: ignore
            pos += sy if H else sx
            
        return texture

    def pngBytes(self):
        """Returns a the bytes of the png for the texture"""
        byte_arr = io.BytesIO()
        Image.fromarray(self.texture().transpose(1,0,2)).save(byte_arr, format='PNG')
        return byte_arr.getvalue()

    def saveImage(self, path: Path | str):
        """Saves the atlas to a file"""
        Image.fromarray(self.texture().transpose(1,0,2)).save(path)