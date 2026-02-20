#!/usr/bin/env python3
"""
Convert JPG images to PNG with transparent background.
Removes white/light backgrounds and converts to PNG with alpha channel.
"""

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


def main():
    if len(sys.argv) < 2:
        # Default: convert all JPG files in resources/models recursively
        input_dir = Path("resources/models")
        output_dir = input_dir
    elif len(sys.argv) == 2:
        # Only input folder provided, output to same location
        input_dir = Path(sys.argv[1])
        output_dir = input_dir
    else:
        # Both input and output folders provided
        input_dir = Path(sys.argv[1])
        output_dir = Path(sys.argv[2])

    if not input_dir.exists():
        print(f"✗ Input directory not found: {input_dir}")
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
            jpg_to_transparent_png(jpg_file, output_path)
        print("\nDone!")
    else:
        print(f"No JPG files found in {input_dir}/")


if __name__ == "__main__":
    main()
