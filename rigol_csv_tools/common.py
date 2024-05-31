import glob
import numpy as np
import scipy
from PIL import Image

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

# Constants for Savitzky-Golay filtering
SAVGOL_WINDOW = 150
SAVGOL_POLYORDER = 3

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

def filter_savgol(a, window_size, poly_order):
    """
    Filter numpy array using Savitzky-Golay filter.
    
    The lines are filtered independently using a specified window
    size and order
    
    :param a: 2-dimensional numpy array to filter
    :param window_size: Window size for Savitzky-Golay filter
    :param poly_order: Polynomial order for Savitzky-Golay filter
       
    :return: New numpy array with filtering applied
    """
    a_filtered = scipy.signal.savgol_filter(x=a, window_length=window_size, polyorder=poly_order, axis=1)
    return a_filtered

def filter_savgol_img(img, window_size, poly_order):
    """
    Filter lines of a PIL image using Savitzky-Golay filter.
    
    This is a helper function that takes and returns a PIL image,
    and converts it to a numpy array to call filter_savgol.
    
    :param a: PIL image to filter
    :param window_size: Window size for Savitzky-Golay filter
    :param poly_order: Polynomial order for Savitzky-Golay filter
       
    :return: New PIL image with filtering applied
    """
    a = np.array(img.convert('L')).astype(np.float64)
    a_filtered = filter_savgol(a, window_size, poly_order)    
    img_filtered = Image.fromarray(a_filtered.astype(np.uint8), 'L')
    return img_filtered
