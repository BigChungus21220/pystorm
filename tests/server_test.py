import pystorm as ps

with open("tests/particles/spiral.particle.json", "r", encoding="utf-8") as file:
    particle = file.read()
    
with open("tests/textures/opaque.png", "rb") as file:
    texture = file.read()
    
ps.previewEffect(particle, texture)

