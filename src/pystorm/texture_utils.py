from typing import Literal
import cv2
import numpy as np
from .common_types import Vector2
from .spritesheet import FramesType
from math import floor, ceil

type ScalingMode = Literal["nearmean", "cubic", "nearest"]
"""A texture scaling mode

nearmean: Modification of cubic sampling for pixel art. Takes the color closest to the cubic scaling value. Best for pixel art downscaling, but somewhat works with upscaling too.\n
cubic: Cubic sampling, interpolates between pixels smoothly. Best for gradients or images (not pixel art).\n
nearest: Nearest neighbor sampling, takes the color of the pixel closest to the sample point. Good for integer scaling factors.
"""

def resizeImage(image: FramesType, new_size: Vector2, mode: ScalingMode = "nearmean") -> FramesType:
    """Rescales an image (or frame stack) to a new size. 

    Args:
        image: Shape (frames, width, height, channels) frame stack
        new_size: New image size (rounds to nearest int)
        mode: Image scaling mode (see :class:`ScalingMode`)
    """
    size = image.shape[1:3]
    if isinstance(new_size, np.ndarray):
        if new_size.ndim != 1 or new_size.shape[0] != 2:
            raise ValueError(f"Unexpected new size. Expected tuple[Number, Number] or shape (2) np array, got {new_size.shape}.")
    
    f, W, H, c = image.shape
    w = int(round(new_size[0]))
    h = int(round(new_size[1]))
    
    if mode == "nearmean":
        # finds the color near the sample point nearest to the average color near the sample point
        # good for pixel art scaling (at least downscaling)
        
        # cheap hack to make opencv do a batched resize
        channel_image = np.transpose(image, (1, 2, 0, 3)).reshape(W, H, f * c)
        channel_mean = cv2.resize(channel_image, (h, w), interpolation=cv2.INTER_CUBIC)
        mean = np.transpose(channel_mean.reshape(w, h, f, c), (2, 0, 1, 3))
        
        # extract relevant sizes
        xs, ys = np.maximum(size[0]/w, 2), np.maximum(size[1]/h, 2)
        kx, ky = int(np.ceil(xs)), int(np.ceil(ys))

        # get the sampling grids
        xv, yv = np.meshgrid(np.arange(w), np.arange(h), indexing='ij')
        dx, dy = np.meshgrid(np.arange(kx), np.arange(ky), indexing='ij')

        pxl, pxr = int(np.floor(xs/2)), int(np.ceil(xs/2))
        pyl, pyr = int(np.floor(ys/2)), int(np.ceil(ys/2))

        sample_points = np.round(np.stack((xv.ravel(), yv.ravel())) * np.array((size[0]/w, size[1]/h))[:, None]).astype(int)

        X = sample_points[0, :, None, None] + dx
        Y = sample_points[1, :, None, None] + dy
        
        padded = np.pad(image, ((0,0), (pxl, pxr), (pyl, pyr), (0,0)), mode='edge')

        # sample each scaling kernel
        cols = padded[:, X, Y, :].reshape((f, w*h, kx*ky, c))
        flat_mean = mean.reshape((f, w*h, c))
        # find the distance from the mean color to each color in the kernel
        diff: np.ndarray = np.linalg.norm(cols - flat_mean[:, :, None, :], axis = -1) # (f, w*h, kx*ky, 1)
        
        # choose the color closest to the mean
        best_idx = np.argmin(diff, axis=2)
        f_idx = np.arange(f)[:, None]
        wh_idx = np.arange(w*h)[None, :]
        
        # get the final image
        res = cols[f_idx, wh_idx, best_idx, :] # (f, w*h, c)
        
        return res.reshape(f, w, h, c)
    
    elif mode == "cubic":
        channel_image = np.transpose(image, (1, 2, 0, 3)).reshape(W, H, f * c)
        channel_mean = cv2.resize(channel_image, (h, w), interpolation=cv2.INTER_CUBIC)
        mean = np.transpose(channel_mean.reshape(w, h, f, c), (2, 0, 1, 3))
        
        return mean # type: ignore
    
    elif mode == "nearest":
        channel_image = np.transpose(image, (1, 2, 0, 3)).reshape(W, H, f * c)
        channel_mean = cv2.resize(channel_image, (h, w), interpolation=cv2.INTER_NEAREST)
        mean = np.transpose(channel_mean.reshape(w, h, f, c), (2, 0, 1, 3))
        
        return mean # type: ignore
        
        
def reorient(image: FramesType, rotate: int = 0, mirror: Literal["horizontal", "vertical", "none"] = "none") -> FramesType:
    """Applies a combination of 90 ccw degree rotations and an axis aligned flip.

    Args:
        rotate: Rotation in 90 degree increments. `rotation = 1` applies a counter-clockwise 90 degree rotation.
        mirror: Mirror operation if any. Applied after rotation.
    """
    
    res = np.rot90(image, k=rotate, axes=(1,2)).copy()
    if mirror == "horizontal":
        res = np.flip(res, axis=1)
    elif mirror == "vertical":
        res = np.flip(res, axis=2)
        
    return res # type: ignore
    
    
# basic transforms
#  clean transforms (v/h flip, 90*n rotations)
#  arbitrary transforms + filtering modes
#  cropping

# colors
# color replace (by filter(s))
# posterize / dither
# change color space
#  lin rgb
#  hsv
# filter
#  gaussian
#  bokeh

# gradients