from pystorm import *

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
            texture = ParticleTexture(
                texture="textures/animation",
                textureSize=(32,8),
                uv=(0,0),
                uvSize=(8,8),
                animation = UVAnimationFPS(
                    uvStep=(8,0),
                    frameCount=4,
                    fps=16,
                    loopFrames=True
                )
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