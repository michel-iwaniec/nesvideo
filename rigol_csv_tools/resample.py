#!/usr/bin/env python3
"""
Script for for resampling a png horizontally using lanzcos, with optional y-repeat and sample scaling.

This script is mainly intended for resampling very-high-samplerate images of NES NTSC video
to more reasonable sizes for navigation using a conventional image viewer.
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

def resample(img, scale = 1.0, pixel_width = 93, pixel_height = 1):
    """
    Resample image.
    
    If the sample scaling resulted in clipping, a warning message is printed to stdout.
    
    :param IMG: PIL image
    :param scale: Scaling factor for samples
    :param pixel_width: Width of 1 output pixel (pixel is stretched with filtering)
    :param pixel_height: Height of 1 output pixel (pixel is stretched without filtering)
    
    :return: PIL image scaled / stretched
    """
    w, h = img.size
    img = img.resize((PIXELS_PER_SCANLINE * pixel_width, h), resample=Image.LANCZOS)
    img = img.resize((PIXELS_PER_SCANLINE * pixel_width, h * pixel_height), resample=Image.NEAREST)
    return img
  
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=f"Resample / stretch grayscale image")
    parser.add_argument("-s", "--scale",
                        type=float,
                        default=1.0,
                        help=f"Scaling factor to apply to output image (default: {1.0})")
    parser.add_argument("-x", "--pixel_size_x",
                        type=int,
                        default=10,
                        help=f"Width of 1 pixel in the output image (default: {10})")
    parser.add_argument("-y", "--pixel_size_y",
                        type=int,
                        default=10,
                        help=f"Height of 1 pixel in the output image (default: {10})")
    parser.add_argument("-w", "--window",
                        type=int,
                        default=0,
                        help=f"Enable savgol filter and change window size (default: {SAVGOL_WINDOW}")
    parser.add_argument("-p", "--polyorder",
                        type=int,
                        default=0,
                        help=f"Enable savgol filter and change polynomial order (default: {SAVGOL_POLYORDER}")
    parser.add_argument("filenames",
                        type=str, 
                        nargs="+",
                        help=f"Images to resample. Each will create a single new .png file with the suffix _resampled_x_y")
    args = parser.parse_args()
    savgol_enabled = args.window != 0 or args.polyorder != 0
    if args.window == 0:
        args.window = SAVGOL_WINDOW
    if args.polyorder == 0:
        args.polyorder = SAVGOL_POLYORDER
    filenames = expand_filenames(args.filenames)
    for filename in filenames:
        img = Image.open(filename)
        # Do optional savgol filtering if requested
        if savgol_enabled:
            print(f"Filtering {filename} with savgol: window size = {args.window}, polynomial order = {args.polyorder}")
            savgol_suffix = f"_w{args.window}_p{args.polyorder}"
            img = filter_savgol_img(img, window_size=args.window, poly_order=args.polyorder)
        else:
            savgol_suffix = ""
        # Resample to desired pixel size
        img = resample(img,
                       scale=args.scale,
                       pixel_width=args.pixel_size_x,
                       pixel_height=args.pixel_size_y)
        # Save output
        img.save(f"{Path(Path(filename).stem).stem}_resampled_{args.pixel_size_x}_{args.pixel_size_y}{savgol_suffix}.png")
