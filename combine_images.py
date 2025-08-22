import os
import glob
from PIL import Image

# --- Configuration ---
PAIR_FILE = "RPIC_all/id_pair.txt"
IMAGE_DIR = "pymol_images"
OUTPUT_IMAGE = "comparison_grid.png"

def get_image_pairs(protein_pairs):
    image_pairs = []
    for pdb1, pdb2 in protein_pairs:
        gemini_img = os.path.join(IMAGE_DIR, f"gemini_{pdb1}_vs_{pdb2}.png")
        official_img = os.path.join(IMAGE_DIR, f"official_{pdb1}_vs_{pdb2}.png")
        if os.path.exists(gemini_img) and os.path.exists(official_img):
            image_pairs.append((gemini_img, official_img))
    return image_pairs

def combine_pair_images(img1_path, img2_path):
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)
    dst = Image.new('RGB', (img1.width + img2.width, img1.height))
    dst.paste(img1, (0, 0))
    dst.paste(img2, (img1.width, 0))
    return dst

def main():
    with open(PAIR_FILE, 'r') as f:
        protein_pairs = [line.strip().split() for line in f if line.strip()]

    image_pairs = get_image_pairs(protein_pairs)
    if not image_pairs:
        print("No image pairs found. Make sure you have run the PyMOL scripts first.")
        return

    combined_images = [combine_pair_images(p[0], p[1]) for p in image_pairs]

    # Create a grid
    # For simplicity, we'll just stack them vertically. A grid would be more complex.
    max_width = max(img.width for img in combined_images)
    total_height = sum(img.height for img in combined_images)

    grid_image = Image.new('RGB', (max_width, total_height))
    y_offset = 0
    for img in combined_images:
        grid_image.paste(img, (0, y_offset))
        y_offset += img.height

    grid_image.save(OUTPUT_IMAGE)
    print(f"Combined image saved to {OUTPUT_IMAGE}")

if __name__ == "__main__":
    try:
        from PIL import Image
    except ImportError:
        print("Pillow library not found. Please install it with: pip install Pillow")
        exit(1)
    main()
