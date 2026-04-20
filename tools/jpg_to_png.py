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
        img = Image.open(jpg_path)

        img = img.convert("RGBA")

        data = img.getdata()

        new_data = []
        for item in data:
            r, g, b = item[:3]

            if r > threshold and g > threshold and b > threshold:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)

        img.putdata(new_data)

        if output_path is None:
            output_path = Path(jpg_path).with_suffix(".png")
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        img.save(output_path, "PNG")
        print(f"\u2713 Converted: {jpg_path} \u2192 {output_path}")
    except Exception as e:
        print(f"\u2717 Error processing {jpg_path}: {e}")


def handle_convert(args):
    """Handle the convert command."""
    input_dir = args.input
    output_dir = args.output or input_dir
    threshold = args.threshold

    if not input_dir.exists():
        print(f"\u2717 Input directory not found: {input_dir}")
        sys.exit(1)

    if threshold < 0 or threshold > 255:
        print(f"\u2717 Threshold must be between 0 and 255, got {threshold}")
        sys.exit(1)

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
            rel_path = jpg_file.relative_to(input_dir)
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
