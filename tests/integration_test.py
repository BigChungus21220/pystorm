from pystorm import *

with open("tests/textures/CharacterTemplate.aseprite", "rb") as file:
    aseprite_file = file.read()

spritesheet = SpriteSheet.fromASE(aseprite_file)

JSON = makeParticleEffect(
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

with open("tests/test_outputs/output.json", "w") as file:
    file.write(JSON)

previewEffect(JSON, spritesheet.texture)