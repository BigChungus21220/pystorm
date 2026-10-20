from pystorm import *
from PIL import Image, ImageChops
import numpy as np

def images_eq(a, b):
    img1 = Image.open(a)
    img2 = Image.open(b)
    
    if img1.size != img2.size or img1.mode != img2.mode:
        return False
        
    diff = ImageChops.difference(img1, img2)
    return diff.getbbox() is None


in_tex = "tests/textures/animation.png"
out_tex = "tests/test_outputs/frame.png"

def normalize_binary():
    with open(in_tex, 'rb') as f:
        png_bytes = f.read()

    frames = normalizeImageFrames(png_bytes)
    numpyAsImage(frames[0,:,:,:]).save(out_tex)
    assert images_eq(in_tex, out_tex), "Output texture does not match input texture"

def normalize_path():
    frames = normalizeImageFrames(in_tex)
    numpyAsImage(frames[0,:,:,:]).save(out_tex)
    assert images_eq(in_tex, out_tex), "Output texture does not match input texture"
    
def normalize_array():
    frames = normalizeImageFrames(in_tex)
    frames = (frames*np.iinfo(np.int32).max).astype(np.int32)
    
    frames = normalizeImageFrames(frames)
    numpyAsImage(frames[0,:,:,:]).save(out_tex)
    assert images_eq(in_tex, out_tex), "Output texture does not match input texture"

def normalize_frames():
    frames = normalizeImageFrames([in_tex])
    numpyAsImage(frames[0,:,:,:]).save(out_tex)
    assert images_eq(in_tex, out_tex), "Output texture does not match input texture"

tests = [normalize_binary, normalize_path, normalize_array, normalize_frames]

passed = 0
i = 0
for test in tests:
    try:
        test()
        passed += 1
    except Exception as e:
        print(f"Print failed test {i}, {test.__name__}: {e}")
    i += 1
    
print(f"Passed {passed}/{i} tests.")

spritesheet = SpriteSheet.fromASE("tests/textures/CharacterTemplate.aseprite")
spritesheet.saveImage("tests/test_outputs/base.png")

spritesheet.frames = resizeImage(spritesheet.frames, (100, 100))
spritesheet.saveImage("tests/test_outputs/resize.png")

