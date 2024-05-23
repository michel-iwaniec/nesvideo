import glob
import numpy as np

# Default name for VOUT signal
CSV_VOUT_CHANNEL_NAME = "CH1"
# Default sample rate in nanoseconds
CSV_VOUT_CHANNEL_PIXEL_DURATION_NS = 2.0

# Constants for pixel / sample rates
SYNC_LEVEL = 0.3
SYNC_THRESHOLD = SYNC_LEVEL + 0.1
PPU_PIXEL_DURATION_NS = 186.2433925500408
SAMPLES_PER_PIXEL = PPU_PIXEL_DURATION_NS / CSV_VOUT_CHANNEL_PIXEL_DURATION_NS
VERTICAL_BLANKING_PULSE_LENGTH_PIXELS = 315
VERTICAL_BLANKING_PULSE_LENGTH_SAMPLES = int(VERTICAL_BLANKING_PULSE_LENGTH_PIXELS * SAMPLES_PER_PIXEL)
SCANLINES_PER_FRAME = 262
PIXELS_PER_SCANLINE = 341
PIXELS_PER_FRAME = SCANLINES_PER_FRAME * PIXELS_PER_SCANLINE
SAMPLES_PER_FRAME = int(PIXELS_PER_FRAME * SAMPLES_PER_PIXEL)
SAMPLES_PER_SCANLINE = int(PIXELS_PER_SCANLINE * SAMPLES_PER_PIXEL)

def expand_filenames(filenames):
    """
    Given a list of filenames that may contain wildcards, expands the wildcards to concrete filenames.
    
    This is needed to support wildcards in a Windows environment.
    In a Linux-based environment the shell expands the wildcards, making this function a no-op.
    
    :param filenames: List of filenames with wildcards
    
    :return: List of filenames without wildcards
    """
    expanded_filenames = []
    for filename in filenames:
        expanded_filenames += glob.glob(filename)
    return expanded_filenames

def find_sync_start(w, sync_length, sync_threshold):
    """
    Find the start of the next sync pulse
    
    :param w: Waveform (a pandas time series)
    :param sync_length: Required length to qualify as sync pulse
    :param sync_threshold: Minimum value to qualify as sync pulse
    
    :return: Integer index denoting sync position
    """
    i = 0
    while i < len(w):
        # Find potential sync start
        sync_start = np.argmax(w[i:] <= sync_threshold)
        # Lower threshold reached - find out length
        sync_end = np.argmax(w[i+sync_start:] > sync_threshold) + sync_start
        # If length qualifies - return start
        if sync_end - sync_start >= sync_length:
            return sync_start + i
        else:
            i += sync_end if sync_end > 0 else 1
    return None
