#!/usr/bin/env python3
"""
Script for converting a 1-frame NES PPU VOUT signal to a .png, with optional stretching and sample scaling.

.csv is assumed to be captured from a Rigol DS1104-Z oscilloscope with a compensated probe
attached to PPU pin 21 (VOUT), at a high-resolution sample rate.
This is currently hard-coded by SAMPLES_PER_PIXEL = 93.121 (equivalent to 2ns).
"""
import sys
import random
import math
import copy
import argparse
import glob
from collections import defaultdict
import numpy as np
import pandas as pd
from PIL import Image
from pathlib import Path

from common import *

def find_hsync(w):
    """
    Find the start of the next hblank period in a waveform capture.
    
    :param w: Waveform (a pandas time series)
    
    :return: Two integer indices denoting start of scanline / hblank, and end-of-scanline
    """
    i = 0
    while w[i] > SYNC_THRESHOLD:
        i += 1
    return i, i + SAMPLES_PER_SCANLINE

def frame_to_nparray(w, sample_rate_ns):
    """
    Convert a waveform representing a frame to a numpy array

    :param w: Waveform (a pandas time series)
    :param sample_rate_ns: Sample rate in nanoseconds
    
    :return: Two integer indices denoting start of scanline / hblank, and end-of-scanline
    """
    samples_per_pixel = PPU_PIXEL_DURATION_NS / sample_rate_ns
    samples_per_scanline = PIXELS_PER_SCANLINE * samples_per_pixel
    samples_per_frame = SCANLINES_PER_FRAME * samples_per_scanline
    a_scanlines = w.to_numpy()
    a_scanlines = a_scanlines[:int(samples_per_frame)]
    if len(a_scanlines) < int(samples_per_frame):
        a_scanlines = np.resize(a_scanlines, int(samples_per_frame))
    samples_per_scanline_i = int(math.ceil(samples_per_scanline))
    a = np.zeros((0, samples_per_scanline_i), dtype=np.uint8)
    # Estimate a more correct samples per scanline from hsyncs to avoid pixel start drifting.
    # Omit first 20 scanlines from estimation to avoid shorter scanline affecting the result.
    hblank_start_old = None
    hblank_sum = 0
    n = 0
    hblank_start, _ = find_hsync(a_scanlines)
    hblank_diff = samples_per_scanline
    for i, y in enumerate(range(SCANLINES_PER_FRAME)):
        begin = int(hblank_start)
        end = begin + samples_per_scanline_i
        if end <= len(a_scanlines):
            s = a_scanlines[begin:end]
            s = np.resize(s, samples_per_scanline_i)
            hblank_start, _ = find_hsync(a_scanlines[end-int(samples_per_pixel):])
            hblank_start += end-int(samples_per_pixel)
            if i >= 20:
                hblank_diff = hblank_start - hblank_start_old
                hblank_sum += hblank_diff
                n += 1
            hblank_start_old = hblank_start
    samples_per_scanline_estimated = hblank_sum / n
    # Find first hsync
    hblank_start, _ = find_hsync(a_scanlines)
    # Copy scanlines
    for i, y in enumerate(range(SCANLINES_PER_FRAME)):
        begin = int(hblank_start)
        end = begin + samples_per_scanline_i
        if end <= len(a_scanlines):
            s = a_scanlines[begin:end]
            s = np.resize(s, samples_per_scanline_i)
            a = np.vstack([a, s])
            hblank_start += samples_per_scanline_estimated
    return a

def nparray_to_image(a, scale = 1.0, pixel_width = 93, pixel_height = 1):
    """
    Convert numpy array to image with optional sample scaling and stretching
    
    If the sample scaling resulted in clipping, a warning message is printed to stdout.
    
    :param a: numpy array
    :param scale: Scaling factor for samples
    :param pixel_width: Width of 1 output pixel (pixel is stretched with filtering)
    :param pixel_height: Height of 1 output pixel (pixel is stretched without filtering)
    
    :return: PIL image scaled / stretched
    """
    h, w = a.shape
    warned_clip = False
    a8 = np.zeros((0, w), dtype=np.uint8)
    for y in range(h):
        s = a[y, :]
        s_scaled = s * scale
        if any(ss < 0.0 or ss > 255.0 for ss in s_scaled) and not warned_clip:
            print(f"WARNING: Clipping ocurred at scanline {y}")
            warned_clip = True
        s8 = np.clip(s_scaled, 0, 255).astype(np.uint8)
        a8 = np.vstack([a8, s8])
    img = Image.fromarray(a8, "L")
    w, h = img.size
    img = img.resize((PIXELS_PER_SCANLINE * pixel_width, h), resample=Image.LANCZOS)
    img = img.resize((PIXELS_PER_SCANLINE * pixel_width, h * pixel_height), resample=Image.NEAREST)
    return img
  
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=f"Convert .csv / .csv.gz of PPU VOUT into a grayscale image, optionally scaled / stretched")
    parser.add_argument("-n", "--name",
                        type=str,
                        default=CSV_VOUT_CHANNEL_NAME,
                        help=f"Name of channel in .csv data storing VOUT capture (default: {CSV_VOUT_CHANNEL_NAME})")
    parser.add_argument("-s", "--scale",
                        type=float,
                        default=100.0,
                        help=f"Scaling factors to apply to output image (default: {100.0})")
    parser.add_argument("-x", "--pixel_size_x",
                        type=int,
                        default=int(SAMPLES_PER_PIXEL),
                        help=f"Width of 1 pixel in the output image (default: {int(SAMPLES_PER_PIXEL)})")
    parser.add_argument("-y", "--pixel_size_y",
                        type=int,
                        default=1,
                        help=f"Height of 1 pixel in the output image (default: {1})")
    parser.add_argument("filenames",
                        type=str, 
                        nargs="+",
                        help=f".csv / .csv.gz filenames to convert to .png. Each will create a single new .png file")
    args = parser.parse_args()
    filenames = expand_filenames(args.filenames)
    for filename in filenames:
        waveforms = pd.read_csv(f"{filename}", header=0, skiprows=[1], usecols=[1,2,3], dtype=np.float64)
        vout = waveforms[args.name]
        a = frame_to_nparray(vout, CSV_VOUT_CHANNEL_PIXEL_DURATION_NS)
        img = nparray_to_image(a, scale = args.scale, pixel_width = args.pixel_size_x, pixel_height = args.pixel_size_y)
        img.save(f"{Path(Path(filename).stem).stem}_img.png")
