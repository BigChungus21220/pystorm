import aseprite_reader
import io
from pathlib import Path
from PIL import Image, ImageSequence
from .common_types import Number, Vector2, Array2
from .particle import ParticleTexture, UVAnimationFPS, UVAnimationLifetime, ParticleAppearance
from typing import Literal, Any, Callable, Self, cast
import numpy as np
from dataclasses import dataclass, field
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
type FramesType = np.ndarray[tuple[int, int, int, int], np.dtype[np.float64]]
"""`frameCount x width x height x channels` **Watch out for width / height ordering conventions when using.**"""

def normalizeImageFrames(data: FramesConvertible) -> FramesType:
    """
    Converts a file path, image bytes, a numpy array to a numpy array of frames, or a list of things convertible to single frames to a numpy array of frames.

    Args:
        data: A path, buffer, bytes, or numpy array
        float_max_value: The maximum value use when mapping floats to uint8. Defaults to 1.0.

    Returns:
        A `frameCount x width x height x channels` array of floats in `[0, 1]^3`. **Watch out for width / height ordering conventions when using.**
    """

    if isinstance(data, Path) or isinstance(data, str):
        with open(data, "rb") as file:
            data = file.read()
            
    if isinstance(data, np.ndarray):
        if data.ndim >= 2 and data.ndim <= 4:
            if np.issubdtype(data.dtype, np.floating):
                arr = data.astype(np.float64)
            elif np.issubdtype(data.dtype, np.integer):
                arr = data.astype(np.float64)/np.iinfo(data.dtype).max
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
        
        frames = np.empty((getattr(img, "n_frames", 1), img.width, img.height, target_channels), dtype=np.float64)
        i = 0
        for frame in ImageSequence.Iterator(img):
            converted_frame = frame.convert(target_mode)
            arr = np.array(converted_frame)
        
            if arr.ndim == 2:
                arr = arr[:,:,None]
            
            frames[i,:,:,:] = arr.transpose((1,0,2))
            i += 1

        return frames.astype(np.float64)/255.0 # type: ignore
    
    elif isinstance(data, Sequence):
        frames: np.ndarray | None = None
        i = 0
        for frame in data:
            image = normalizeImageFrames(frame)
            if image.shape[0] != 1: raise ValueError(f"Image for frame {i} contains multiple frames")
            if frames is None:
                frames = np.empty((len(data), image.shape[1], image.shape[2], image.shape[3]), dtype=np.float64)
            else:
                if image.shape[1:] != frames.shape[1:]: raise ValueError(f"Image sizes in sequence must match. Size of frame 0 does not match frame {i}")
            frames[i, :, :, :] = image
            i += 1
            
        if frames is None: raise ValueError(f"No frames in input")
        return frames # type: ignore
    
def numpyAsImage(texture: np.ndarray[tuple[int, int, int], np.dtype[Any]]) -> Image.Image:
    """Converts a (w, h, c) numpy array to a 8 bit PIL image"""
    
    if np.issubdtype(texture.dtype, np.floating):
        return Image.fromarray((texture.transpose(1,0,2)*255).astype(np.uint8))
    elif np.issubdtype(texture.dtype, np.integer):
        return Image.fromarray((texture.transpose(1,0,2)/np.iinfo(texture.dtype).max*255.0).astype(np.uint8))
    else:
        raise TypeError(f"Unsupported image datatype: {texture.dtype}")
        

def imageAsPNGBytes(image: Image.Image) -> bytes:
    """Converts a PIL image to png bytes"""
    byte_arr = io.BytesIO()
    image.save(byte_arr, format='PNG')
    return byte_arr.getvalue()

type Orientation = Literal["horizontal", "vertical"]
type IntArray = np.ndarray[tuple[int], np.dtype[np.integer]]

@dataclass
class SpriteSheet:
    """
    A spritesheet convertible to a :class:`ParticleTexture`
    """
    
    frames: FramesType
    """Frames of the animation. Can be safely modified"""
    uvStart: IntArray = field(default_factory=np.zeros(2, dtype=int)) # type: ignore
    """The top left corner of the first frame."""
    tileDirection: Orientation = "horizontal"
    """How to tile frames of the animation"""
    _texture_size: IntArray | None = None
    
    @property
    def uvSize(self) -> IntArray:
        """Size of each frame"""
        return np.array(self.frames.shape[1:3], dtype=int) # type: ignore
    
    @property
    def frameCount(self) -> int:
        """Number of frames"""
        return self.frames.shape[0]
    
    @property
    def uvStep(self) -> IntArray:
        """Pixels to step each frame"""
        step = np.zeros_like(self.uvSize)
        step[int(self.tileDirection != "horizontal")] = self.uvSize[0]
        return step # type: ignore
    
    @property
    def textureSize(self) -> IntArray:
        """Size of this animation on the texture"""
        if self._texture_size is None:
            return self.uvStart + self.uvSize + self.uvStep*(self.frameCount - 1) # type: ignore
        else:
            return self.uvStart + self._texture_size # type: ignore
    
    @property
    def channels(self) -> int:
        """Number of channels"""
        return self.frames.shape[3]
    
    @property
    def halfSize(self) -> Array2:
        """The half dimensions of the particle to match Minecraft's pixel size. Use directly with :method:`ParticleAppearance`."""
        return self.uvSize/32.0 # type: ignore
    
    @classmethod
    def fromFrames(cls, frames: FramesConvertible, tileDirection: Orientation = "horizontal"):
        """Constructs a spritesheet from frames

        Args:
            frames:
            tileDirection: Direction to layout frames on the spritesheet. Defaults to "horizontal".
        """
        frames = normalizeImageFrames(frames)
        return cls(frames, np.zeros(2, dtype=int), tileDirection)
        
    @classmethod
    def fromImage(cls, image: ImageConvertible, uvSize: Vector2, frameCount: int, uvStart: Vector2 = (0,0), tileDirection: Orientation = "horizontal"):
        """Constructs a spritesheet from a spritesheet image

        Args:
            image:
            uvSize: Size of each frame
            frameCount: Number of frames
            uvStart: Top left corner of first frame. Defaults to (0,0)
            tileDirection: Direction to layout frames on the spritesheet. Defaults to "horizontal"
        """
        
        arr = normalizeImageFrames(image) # 1, w, h, c
        if arr.shape[0] != 1: raise ValueError("Image contains multiple layers / frames")
        
        arr = arr[:, uvStart[0]:, uvStart[1]:, :]
        
        tw, th = int(uvSize[0]), int(uvSize[1])
        c = arr.shape[3]
        
        if tileDirection == "horizontal":
            strip = arr[0, 0 : tw * frameCount, 0 : th, :]
            frames = strip.reshape((frameCount, tw, th, c)).copy()
            
        else:
            strip = arr[0, 0 : tw, 0 : th * frameCount, :]
            frames = strip.reshape((tw, frameCount, th, c)).transpose((1,0,2,3)).copy()
        
        return cls(frames, cast(np.ndarray[tuple[int], np.dtype[np.integer]], np.array(uvStart, dtype=int)), tileDirection)
    
    @classmethod
    def fromASE(cls, ase: bytes | Path | str, tileDirection: Orientation = "horizontal"):
        """Constructs a spritesheet from an Aseprite file

        Args:
            ase: Aseprite file bytes or path
            tileDirection: Direction to layout frames on the spritesheet. Defaults to "horizontal".
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
    
    def editFrames(self, callback: Callable[[FramesType], FramesType]) -> Self:
        """Applies a function to the frames of the spritesheet."""
        self.frames = callback(self.frames) # type: ignore
        return self
    
    def texture(self) -> np.ndarray[tuple[int, int, int], np.dtype[np.uint8]]:
        """Texture as a `(f*w, h, c)` or `(w, f*h, c)` uint8 numpy array (depending on `tileDirection`)"""
        img = np.zeros((self.textureSize[0], self.textureSize[1], self.channels), dtype=np.uint8)
        size = self.textureSize - self.uvStart
        img[self.uvStart[0]:, self.uvStart[1]:, :] = (self.frames.reshape((size[0], size[1], self.channels))*255).astype(np.uint8)
        return img # type: ignore
        
    def pngBytes(self):
        """Returns a the bytes of the png for the texture"""
        return imageAsPNGBytes(numpyAsImage(self.texture()))
    
    def saveImage(self, path: Path | str):
        """Saves the spritesheet as a single texture.
        
        Args:
            path: The file to save this texture to.
        """
        numpyAsImage(self.texture()).save(path)
    
    def textureFPS(self, path: str, fps: Number, loop: bool = False):
        """The texture descriptor for a particle effect whose animation stretches to it's lifetime

        Args:
            path: The path to where this texture will be stored in the resource pack. Eg: `textures/particle/particles`
            fps: Frames per second of the animation
            loop:: Whether the animation loops to the start. Defaults to False.
        """
        return ParticleTexture(
            texture = path,
            textureSize = self.textureSize.astype(np.floating),
            uv = self.uvStart.astype(np.floating),
            uvSize = self.uvSize.astype(np.floating),
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
            path: The path to where this texture will be stored in the resource pack. Eg: `textures/particle/particles`
        """
        return ParticleTexture(
            texture = path,
            textureSize = self.textureSize.astype(np.floating),
            uv = self.uvStart.astype(np.floating),
            uvSize = self.uvSize.astype(np.floating),
            animation = UVAnimationLifetime(
                uvStep = (self.uvSize[0], 0),
                frameCount= self.frameCount
            )
        )
    
    def textureStatic(self, path: str):
        """The texture descriptor for a particle effect with a static texture

        Args:
            path: The path to where this texture will be stored in the resource pack. Eg: `textures/particle/particles`
        """
        return ParticleTexture(
            texture = path,
            textureSize = self.textureSize.astype(np.floating),
            uv = self.uvStart.astype(np.floating),
            uvSize = self.uvSize.astype(np.floating)
        )