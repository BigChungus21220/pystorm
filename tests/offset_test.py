from pystorm import *
from pathlib import Path
import numpy as np
import typing
    
name = "offset_test"
folder = Path("tests/test_outputs/")

spritesheet = SpriteSheet.fromASE("tests/textures/CharacterTemplate.aseprite")

texture = spritesheet.textureFPS(
    path = "textures/animation",
    fps = 16,
    loop = True
)

effect = ParticleEffect(
    identifier = f"test:{name}",
    emitter = Emitter(
        lifetime = EmitterLifetimeOnce(1),
        rate = EmitterRateInstant(1),
        shape = EmitterShapePoint(
            offset=(1, spritesheet.halfSize[1], 1)
        )
    ),
    particle = Particle(
        lifetime = ParticleLifetime(5),
        appearance = ParticleAppearance(
            texture = texture,
            size = spritesheet.halfSize,
            facing = ParticleFacingExpression(
                facingMode = "lookat_y"
            )
        )
    )
)

folder.mkdir(parents=True, exist_ok=True)
effect.saveAs(folder / f"{name}.particle.json")
spritesheet.saveImage(folder / f"{name}.png")

previewEffect(effect.asJSON(), spritesheet.pngBytes())