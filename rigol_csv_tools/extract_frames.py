#!/usr/bin/env python3
"""
Script for splitting a high-resolution .csv of the NES PPU VOUT signal into separate frames.

.csv is assumed to be captured from a Rigol DS1104-Z oscilloscope with a compensated probe
attached to PPU pin 21 (VOUT), at a high-resolution sample rate.
This is currently hard-coded by SAMPLES_PER_PIXEL = 93.121 (equivalent to 2ns).

Only full frames qualify for splitting. A partial frame with missing start / end will be ignored.
"""
import sys
import argparse
import glob
import gzip
import numpy as np
import pandas as pd
from pathlib import Path

from common import *

def find_vblank(w):
    """
    Find the start of the next vblank period in a waveform capture.
    
    :param w: Waveform (a pandas time series)
    
    :return: Two integer indices denoting start of scanline / vblank, and end-of-frame
    """
    sync_start = find_sync_start(w, VERTICAL_BLANKING_PULSE_LENGTH_SAMPLES, SYNC_THRESHOLD)
    if sync_start is not None:
        frame_end = sync_start + SAMPLES_PER_FRAME
        return sync_start, frame_end
    else:
        return None, None

def iterate_frames(w):
    """
    Generator to extract one frame at a time from a waveform.
    
    :param w: The waveform (a pandas time series)
    
    :return: Index in w where vblank was detected
    """
    index = 0
    while True:
        vblank_index, vblank_index_end = find_vblank(w)
        if vblank_index is not None and vblank_index_end <= len(w):
            yield vblank_index + index
            index += SAMPLES_PER_FRAME
            w = w[SAMPLES_PER_FRAME:].reset_index(drop=True)
        else:
            return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"Split .csv / .csv.gz of PPU VOUT into individual frames")
    parser.add_argument("-n", "--name",
                        type=str,
                        default=CSV_VOUT_CHANNEL_NAME,
                        help=f"Name of channel in .csv data storing VOUT capture (default: {CSV_VOUT_CHANNEL_NAME})")
    parser.add_argument("-c", "--compress",
                        action="store_true", 
                        help=f"Compress output .csv with gzip")
    parser.add_argument("filenames",
                        type=str, 
                        nargs="+",
                        help=f"Filenames to split. Each will create a number of new files with suffix '_frameN'.csv")
    args = parser.parse_args()
    filenames = expand_filenames(args.filenames)
    for filename in filenames:
        filename = Path(filename)
        waveforms = pd.read_csv(f"{filename}", header=0, skiprows=[1], usecols=[1,2,3], dtype=np.float64)
        vout = waveforms[args.name]
        print(f"Processing {filename}")
        for i, sample_pos in enumerate(iterate_frames(vout)):
            output_filename = f"{Path(filename.stem).stem}_frame{i}.csv{'.gz' if args.compress else ''}"
            print(f"  vblank found at index {sample_pos} -> writing frame to {output_filename}")
            waveforms_frame = waveforms[:][sample_pos:sample_pos+SAMPLES_PER_FRAME]
            waveforms_frame.to_csv(output_filename, compression="gzip" if args.compress else None)
