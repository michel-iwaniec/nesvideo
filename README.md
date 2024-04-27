# nesvideo

This repo contains some ad-hoc tools for processing NES composite video captures.

It is intended for use with the data captures stored at https://github.com/michel-iwaniec/nesvideo_captures

## Current tools

The current tools in this repo process .csv data files from a Rigol DS1104-Z oscilloscope.

### extract_frames.py

This script will split a .csv capture consisting of multiple frames into separate .csv files per frame, by detecting vblank.

### vout2png.py

The script will convert a 1-frame .csv capture into a .png image.

To make the resulting .png easier to view, the pixel scaling factor, horizontal stretching and vertical stretching can be set to appropriate values on the command-line.

## Example usage

```
# Clone this repo and install dependencies
git clone https://github.com/michel-iwaniec/nesvideo
cd nesvideo
pip3 install -r requirements.txt
cd ..
# Clone data repo
git clone https://github.com/michel-iwaniec/nesvideo_captures
# Split the 'tvtest_bw' capture into separate frames
cd nesvideo_captures/oscilloscope/rigol_csv/tvtest_bw
mkdir -p csv_split
cd csv_split
python3 ../../../../../nesvideo/rigol_csv_tools/extract_frames.py --compress ../csv/*.gz
cd ..
# Create .png files from the split .csv files, with a default voltage scaling factor of 100.0, and 10x10 image pixels per PPU pixel
mkdir -p png
cd png
python3 ../../../../../nesvideo/rigol_csv_tools/vout2png.py -x 10 -y 10 ../csv_split/*.gz
cd ..
cd ../../..
```

