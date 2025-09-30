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
# %%
import pyvips
import sys
import os
import aicspylibczi
import numpy
import traceback
import argparse

def convert_czi_to_tiff(input_path, output_path, verbose=False):
    """
    Reads a CZI file, converts it to a pyramidal TIFF, and saves it.
    
    Args:
        input_path (str): The file path for the input CZI file.
        output_path (str): The file path for the output pyramidal TIFF file.
        verbose (bool): If True, prints detailed debug information.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file not found. Please check the path: {input_path}", file=sys.stderr)
        return

    try:
        print(f"Reading '{input_path}' with aicspylibczi... (this may consume a lot of memory)")
        
        czi = aicspylibczi.CziFile(input_path)
        mosaic_image_data = czi.read_mosaic(C=0, scale_factor=1.0)
        
        # --- Verbose Output ---
        if verbose:
            print(f"  > Shape of the loaded image: {mosaic_image_data.shape}")
            print(f"  > Data type (dtype): {mosaic_image_data.dtype}")

        mosaic_image_data = numpy.squeeze(mosaic_image_data)
        
        # --- Verbose Output ---
        if verbose:
            print(f"  > Shape after squeezing: {mosaic_image_data.shape}")

        image = pyvips.Image.new_from_array(mosaic_image_data)
        
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
        print("--- Traceback Info ---", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("----------------------", file=sys.stderr)


def main():
    """
    Parses command-line arguments and runs the conversion process.
    """
    parser = argparse.ArgumentParser(
        description="Convert a CZI file to a pyramidal TIFF.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
        Example usage:
        python czi2svs.py /path/to/my_image.czi /path/to/output.tif
        python czi2svs.py /path/to/my_image.czi /path/to/output.tif -v
        """
    )
    parser.add_argument("input_file", help="The path to the input .czi file.")
    parser.add_argument("output_file", help="The path for the output pyramidal .tif file.")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output to show detailed debug information."
    )
    
    args = parser.parse_args()
    
    convert_czi_to_tiff(args.input_file, args.output_file, args.verbose)

if __name__ == "__main__":
    main()
