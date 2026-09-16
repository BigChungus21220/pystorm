## PyStorm

A Python package for generating Minecraft: Bedrock Edition particle effects.

### Basic Usage

```py
from pystorm import *

name = "my_particle"

# Load your texture
with open(name + ".png", "rb") as file:
    png_file = file.read()

# Currently spritesheets must tile horizontally
spritesheet = ps.SpriteSheet(png_file, (0,0), (8, 8), 4)

# Define the particle effect
JSON = makeParticleEffect(
    identifier = "test:" + name,
    emitter = Emitter(
        lifetime = EmitterLifetimeOnce(1),
        rate = EmitterRateInstant(1),
        shape = EmitterShapePoint()
    ),
    particle = Particle(
        lifetime = ParticleLifetime(
            maxLifetime=5
        ),
        motion = ParticleTranslationDynamic(),
        rotation = ParticleRotationDynamic(),
        appearance = ParticleAppearance(
            texture = spritesheet.textureLifetime(
                path = "textures/particles/my_particle"
            ),
            material = ParticleMaterial(),
            size=(0.2, 0.2),
            facing = ParticleFacingExpression()
        )
    )
)

# Save the particle to a file
with open(name + ".particle.json", "w") as file:
    file.write(JSON)

# Preview the effect
previewEffect(JSON, spritesheet.texture)
```


### Aseprite Animations

Spritesheets can be directly loaded from Aseprite files and exported as spritesheet pngs

```py
with open("my_particle.ase", "rb") as file:
    aseprite_file = file.read()

spritesheet = ps.SpriteSheet.fromASE(aseprite_file)

spritesheet.saveImage(Path("my_particle.png"))
```


### Acknowledgements

Special thanks to Jannis for creating the [Wintersky](https://github.com/JannisX11/wintersky) library and the [Snowstorm](https://snowstorm.app/) particle editor.
And to Andrew for creating the [aseprite-reader](https://github.com/kennedy0/aseprite-reader) library.