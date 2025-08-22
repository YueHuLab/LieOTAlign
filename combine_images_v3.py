import os
import glob
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
PAIR_FILE = "RPIC_all/id_pair.txt"
IMAGE_DIR = "pymol_images"
OUTPUT_IMAGE = "comparison_grid_v3.png"
FONT_SIZE = 24
IMAGES_PER_ROW = 4

def get_image_pairs(protein_pairs):
    image_pairs = []
    for pdb1, pdb2 in protein_pairs:
        gemini_img = os.path.join(IMAGE_DIR, f"gemini_{pdb1}_vs_{pdb2}.png")
        official_img = os.path.join(IMAGE_DIR, f"official_{pdb1}_vs_{pdb2}.png")
        if os.path.exists(gemini_img) and os.path.exists(official_img):
            image_pairs.append(((pdb1, pdb2), (gemini_img, official_img)))
    return image_pairs

def create_labeled_pair_image(pdb_pair, image_paths, font):
    pdb1, pdb2 = pdb_pair
    img1_path, img2_path = image_paths

    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)

    # Create a new image with space for labels
    label_height = FONT_SIZE + 10
    new_width = img1.width + img2.width
    new_height = img1.height + label_height
    pair_image = Image.new('RGB', (new_width, new_height), 'white')

    # Paste the images
    pair_image.paste(img1, (0, label_height))
    pair_image.paste(img2, (img1.width, label_height))

    # Add labels
    draw = ImageDraw.Draw(pair_image)
    label1 = f"{pdb1} vs {pdb2} (LieOTAlign)"
    label2 = f"{pdb1} vs {pdb2} (Official)"
    draw.text((10, 5), label1, font=font, fill='black')
    draw.text((img1.width + 10, 5), label2, font=font, fill='black')

    return pair_image

def main():
    with open(PAIR_FILE, 'r') as f:
        protein_pairs = [line.strip().split() for line in f if line.strip()]

    image_pairs = get_image_pairs(protein_pairs)
    if not image_pairs:
        print("No image pairs found. Make sure you have run the PyMOL scripts first.")
        return

    try:
        font = ImageFont.truetype("Arial.ttf", FONT_SIZE)
    except IOError:
        print("Arial font not found, using default font.")
        font = ImageFont.load_default()

    labeled_images = [create_labeled_pair_image(pair[0], pair[1], font) for pair in image_pairs]

    # Create the grid
    num_images = len(labeled_images)
    num_rows = (num_images + IMAGES_PER_ROW - 1) // IMAGES_PER_ROW
    
    if not labeled_images:
        print("No labeled images to combine.")
        return

    max_width = labeled_images[0].width * IMAGES_PER_ROW
    max_height = labeled_images[0].height * num_rows

    grid_image = Image.new('RGB', (max_width, max_height), 'white')

    for i, img in enumerate(labeled_images):
        row = i // IMAGES_PER_ROW
        col = i % IMAGES_PER_ROW
        x_offset = col * img.width
        y_offset = row * img.height
        grid_image.paste(img, (x_offset, y_offset))

    grid_image.save(OUTPUT_IMAGE)
    print(f"Combined image saved to {OUTPUT_IMAGE}")

if __name__ == "__main__":
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow library not found. Please install it with: pip install Pillow")
        exit(1)
    main()