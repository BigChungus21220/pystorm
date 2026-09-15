from aseprite_reader import AsepriteFile
import io
from pathlib import Path
from PIL import Image
from .common import Number
from .particle import ParticleTexture, UVAnimationFPS, UVAnimationLifetime

class _InMemoryPath:
    """Tricks libraries expecting a pathlib.Path into reading from memory."""
    def __init__(self, data: bytes):
        self.data = data
        
    def open(self, *args, **kwargs):
        return io.BytesIO(self.data)
    
    def exists(self): return True
    def is_file(self): return True
    
class _NamedBytesIO(io.BytesIO):
    """Tricks libraries expecting a pathlib.Path into writing to memory."""
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


class SpriteSheet:
    def __init__(self, texture: bytes, uvStart: tuple[Number, Number], uvSize: tuple[Number, Number], frames: int) -> None:
        self.texture = texture
        with Image.open(io.BytesIO(self.texture)) as img:
            self.textureSize = (img.width, img.height)
        self.uvStart = uvStart
        self.uvSize = uvSize
        self.frames = frames
    
    @classmethod
    def fromASE(cls, ase: bytes):
        ase_buff = _InMemoryPath(ase)
        ase_file = AsepriteFile(ase_buff) # type: ignore
        frame_count = len(ase_file.frames)
        
        frames = [_NamedBytesIO() for _ in range(frame_count)]
        for i, (_, frame) in enumerate(ase_file.iter_frames()):
            ase_file.render(frame, frames[i]) # type: ignore
            frames[i].seek(0)
        
        with Image.open(frames[0]) as frame0:
            uvSize = (frame0.width, frame0.height)
        
        sheetSize = (uvSize[0]*frame_count, uvSize[1])
        spritesheet = Image.new("RGBA", sheetSize, (0, 0, 0, 0))
        
        for i, frame in enumerate(frames):
            with Image.open(frame) as frame_img:
                spritesheet.paste(frame_img, (i * uvSize[0], 0))
        
        out_buffer = io.BytesIO()
        spritesheet.save(out_buffer, format="PNG")
        
        return cls(out_buffer.getvalue(), (0,0), uvSize, frame_count)
        
    def saveImage(self, path: Path):
        with open(path, "wb") as file:
            file.write(self.texture)
    
    def textureFPS(self, path: str, fps: Number, loop: bool = False):
        return ParticleTexture(
            texture = path,
            textureSize = self.textureSize,
            uv = (0,0),
            uvSize = self.uvSize,
            animation = UVAnimationFPS(
                uvStep = (self.uvSize[0], 0),
                frameCount= self.frames,
                fps = fps,
                loopFrames = loop
            )
        )
    
    def textureLifetime(self, path: str):
        return ParticleTexture(
            texture = path,
            textureSize = self.textureSize,
            uv = (0,0),
            uvSize = self.uvSize,
            animation = UVAnimationLifetime(
                uvStep = (self.uvSize[0], 0),
                frameCount= self.frames
            )
        )
    
    def textureStatic(self, path: str):
        return ParticleTexture(
            texture = path,
            textureSize = self.textureSize,
            uv = (0,0),
            uvSize = self.uvSize
        )