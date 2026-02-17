#!/usr/bin/env python3
"""
Auto-crop images to remove excess whitespace/transparent areas.
Resizes pictures to fit the edges of the subject.
"""

from PIL import Image, ImageChops
import sys
from pathlib import Path


def autocrop_image(image_path, output_path=None, padding=0, background_color=(255, 255, 255)):
    """
    Auto-crop an image to remove excess background/whitespace.

    Args:
        image_path: Path to the image file
        output_path: Optional custom output path (default: same name with _cropped suffix)
        padding: Number of pixels to add around the cropped content (default: 0)
        background_color: RGB tuple for white/background color to remove (default: white)
    """
    try:
        # Open image
        img = Image.open(image_path)
        original_format = img.format

        # Convert to RGBA to handle transparency
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Get the bounding box of non-transparent content
        # For images with alpha channel
        alpha = img.split()[3]
        bbox = alpha.getbbox()

        if bbox is None:
            print(f"⚠ No content found in {image_path}, skipping")
            return

        # Add padding if specified
        x1, y1, x2, y2 = bbox
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(img.width, x2 + padding)
        y2 = min(img.height, y2 + padding)

        # Crop the image
        cropped = img.crop((x1, y1, x2, y2))

        # Determine output path
        if output_path is None:
            input_path = Path(image_path)
            output_path = input_path.parent / f"{input_path.stem}_cropped.png"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save the cropped image
        cropped.save(output_path, "PNG")
        old_size = Path(image_path).stat().st_size
        new_size = output_path.stat().st_size
        print(f"✓ Cropped: {image_path} → {output_path} ({old_size} → {new_size} bytes)")

    except Exception as e:
        print(f"✗ Error processing {image_path}: {e}")


def main():
    if len(sys.argv) < 2:
        # Default: crop all PNG files in resources/models recursively
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

    # Recursively find all image files
    image_files = (
        list(input_dir.glob("**/*.png"))
        + list(input_dir.glob("**/*.PNG"))
        + list(input_dir.glob("**/*.jpg"))
        + list(input_dir.glob("**/*.jpeg"))
        + list(input_dir.glob("**/*.JPG"))
        + list(input_dir.glob("**/*.JPEG"))
    )

    if image_files:
        print(f"Found {len(image_files)} image file(s). Cropping...")
        for img_file in image_files:
            # For output to same folder, add _cropped suffix
            if output_dir == input_dir:
                rel_path = img_file.relative_to(input_dir)
                output_path = (
                    output_dir / rel_path.parent / f"{rel_path.stem}_cropped{rel_path.suffix}"
                )
            else:
                # For different output folder, preserve structure
                rel_path = img_file.relative_to(input_dir)
                output_path = output_dir / rel_path

            autocrop_image(img_file, output_path)
        print("\nDone!")
    else:
        print(f"No image files found in {input_dir}/")


if __name__ == "__main__":
    main()
