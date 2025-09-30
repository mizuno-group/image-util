#!/usr/bin/env python3
"""
Created on 2025-09-29 (Mon) 22:07:13

Converts a CZI (.czi) file to a pyramidal TIFF (.tif) file, which can be
treated like an SVS file by many viewers and libraries.

This script uses the aicspylibczi library to read the CZI file into memory
and then uses pyvips to perform the conversion to a tiled, pyramidal TIFF.

Usage:
    python czi2svs.py <path_to_input.czi> <path_to_output.tif>

@author: I.Azuma
"""
import pyvips
import sys
import os
import slideio 
import numpy
import traceback
import argparse

def convert_czi_to_tiff(input_path, output_path, verbose=False):
    """
    Converts CZI to pyramidal TIFF using slideio for reading and pyvips for writing.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return

    try:
        print(f"Reading '{input_path}' with slideio...")
        
        # open with slideio
        slide = slideio.open_slide(input_path, "CZI")
        scene = slide.get_scene(0)  # Get the first scene

        if verbose:
            print(f"  > Scene loaded successfully. Size (WxH): {scene.size[0]}x{scene.size[1]}")

        # Read the entire scene as a NumPy array
        # This may consume a lot of memory for large images
        image_data = scene.read_block()
        
        if verbose:
            print(f"  > Image data shape: {image_data.shape}, dtype: {image_data.dtype}")

        image = pyvips.Image.new_from_array(image_data)
        
        print(f"Starting conversion to '{output_path}'...")
        
        image.tiffsave(
            output_path,
            tile=True,
            pyramid=True,
            compression='jpeg',
            Q=100,
            bigtiff=True
        )

        print("✅ Conversion completed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Convert a CZI file to a pyramidal TIFF using slideio.",
        epilog="Example: python czi2svs.py input.czi output.tif"
    )
    parser.add_argument("input_file", help="The path to the input .czi file.")
    parser.add_argument("output_file", help="The path for the output pyramidal .tif file.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")
    
    args = parser.parse_args()
    
    convert_czi_to_tiff(args.input_file, args.output_file, args.verbose)

if __name__ == "__main__":
    main()