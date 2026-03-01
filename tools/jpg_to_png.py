#!/usr/bin/env python3
"""
Convert JPG images to PNG with transparent background.
Removes white/light backgrounds and converts to PNG with alpha channel.
"""

import argparse
import sys
from pathlib import Path

from PIL import Image


def jpg_to_transparent_png(jpg_path, output_path=None, threshold=240):
    """
    Convert JPG to PNG with transparent background.

    Args:
        jpg_path: Path to the JPG file
        output_path: Optional custom output path (default: same name with .png)
        threshold: RGB threshold for transparency (0-255, default 240 for white)
    """
    try:
        # Open image
        img = Image.open(jpg_path)

        # Convert to RGBA if not already
        img = img.convert("RGBA")

        # Get image data
        data = img.getdata()

        # Create new image data with transparency
        new_data = []
        for item in data:
            r, g, b = item[:3]

            # Make light colors (near white) transparent
            if r > threshold and g > threshold and b > threshold:
                new_data.append((255, 255, 255, 0))  # Transparent
            else:
                new_data.append(item)

        # Apply new data
        img.putdata(new_data)

        # Determine output path
        if output_path is None:
            output_path = Path(jpg_path).with_suffix(".png")
        else:
            # Ensure output directory exists
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save as PNG
        img.save(output_path, "PNG")
        print(f"✓ Converted: {jpg_path} → {output_path}")
    except Exception as e:
        print(f"✗ Error processing {jpg_path}: {e}")


def handle_convert(args):
    """Handle the convert command."""
    input_dir = args.input
    output_dir = args.output or input_dir
    threshold = args.threshold

    if not input_dir.exists():
        print(f"✗ Input directory not found: {input_dir}")
        sys.exit(1)

    if threshold < 0 or threshold > 255:
        print(f"✗ Threshold must be between 0 and 255, got {threshold}")
        sys.exit(1)

    # Recursively find all JPG/JPEG files
    jpg_files = (
        list(input_dir.glob("**/*.jpg"))
        + list(input_dir.glob("**/*.jpeg"))
        + list(input_dir.glob("**/*.JPG"))
        + list(input_dir.glob("**/*.JPEG"))
        + list(input_dir.glob("**/*.png"))
    )

    if jpg_files:
        print(f"Found {len(jpg_files)} JPG file(s). Converting...")
        for jpg_file in jpg_files:
            # Calculate relative path from input_dir
            rel_path = jpg_file.relative_to(input_dir)
            # Create output path with same structure
            output_path = output_dir / rel_path.with_suffix(".png")
            jpg_to_transparent_png(jpg_file, output_path, threshold=threshold)
        print("\nDone!")
    else:
        print(f"No JPG files found in {input_dir}/")


def main():
    parser = argparse.ArgumentParser(
        description="Convert JPG images to PNG with transparent background."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert", help="Convert JPG files to PNG with transparent background"
    )
    convert_parser.add_argument(
        "--input",
        type=Path,
        default=Path("resources/models"),
        help="Input directory containing JPG files (default: resources/models)",
    )
    convert_parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for PNG files (default: same as input)",
    )
    convert_parser.add_argument(
        "--threshold",
        type=int,
        default=240,
        help="RGB threshold for transparency, 0-255 (default: 240)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "convert":
        handle_convert(args)


if __name__ == "__main__":
    main()
