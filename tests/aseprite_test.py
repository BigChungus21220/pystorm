from pystorm import SpriteSheet

with open("tests/textures/CharacterTemplate.aseprite", "rb") as file:
    aseprite_file = file.read()

sheet = SpriteSheet.fromASE(aseprite_file)

with open("tests/test_outputs/output.png", "wb") as file:
    file.write(sheet.texture)