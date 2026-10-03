from pystorm import *
from pathlib import Path

with open("tests/textures/CharacterTemplate.aseprite", "rb") as file:
    aseprite_file = file.read()

spritesheet = SpriteSheet.fromASE(aseprite_file)

effect = ParticleEffect(
    identifier = "test:compilation_test",
    emitter = Emitter(
        lifetime = EmitterLifetimeOnce(1),
        rate = EmitterRateInstant(1),
        shape = EmitterShapePoint(
            offset=(0,1,0),
            direction=(1,0,0)
        )
    ),
    particle = Particle(
        lifetime = ParticleLifetime(
            maxLifetime=5
        ),
        motion = ParticleTranslationDynamic(
            initialSpeed=1,
            acceleration=(0,0,1),
            drag=1
        ),
        rotation = ParticleRotationDynamic(
            initialRotation=45,
            initialVelocity=10,
            acceleration=0
        ),
        appearance = ParticleAppearance(
            texture = spritesheet.textureFPS(
                path = "textures/animation",
                fps = 16,
                loop = True
            ),
            material = ParticleMaterial(
                recieveLighting=True
            ),
            size=(1,1),
            facing = ParticleFacingExpression()
        )
    )
)

spritesheet2 = SpriteSheet(Path("tests/textures/animation.png"), (0,0), (8,8), 4)

effect2 = ParticleEffect(
    identifier = "test:compilation_test2",
    emitter = Emitter(
        lifetime = EmitterLifetimeOnce(1),
        rate = EmitterRateInstant(1),
        shape = EmitterShapePoint(
            offset=(0,1,0),
            direction=(1,0,0)
        )
    ),
    particle = Particle(
        lifetime = ParticleLifetime(
            maxLifetime=5
        ),
        motion = ParticleTranslationDynamic(
            initialSpeed=1,
            acceleration=(0,0,1),
            drag=1
        ),
        rotation = ParticleRotationDynamic(
            initialRotation=45,
            initialVelocity=10,
            acceleration=0
        ),
        appearance = ParticleAppearance(
            texture = spritesheet2.textureFPS(
                path = "textures/animation",
                fps = 16,
                loop = True
            ),
            material = ParticleMaterial(
                recieveLighting=True
            ),
            size=(5,5),
            facing = ParticleFacingExpression()
        )
    )
)

with open("tests/test_outputs/output.json", "w") as file:
    file.write(effect.asStr())

startServer(timeout=None)
previewEffect(effect.asJSON(), spritesheet.texture)
previewEffect(effect2.asJSON(), spritesheet2.texture)
previewEffect(effect.asJSON(), spritesheet.texture)
previewEffect(effect2.asJSON(), spritesheet2.texture)
previewEffect(effect.asJSON(), spritesheet.texture)
previewEffect(effect2.asJSON(), spritesheet2.texture)
previewEffect(effect.asJSON(), spritesheet.texture)
previewEffect(effect2.asJSON(), spritesheet2.texture)
