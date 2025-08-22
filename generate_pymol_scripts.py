import os

# --- Configuration ---
PAIR_FILE = "RPIC_all/id_pair.txt"
GEMINI_ALIGNED_DIR = "batch_outputs_cutoff_7.0"
OFFICIAL_ALIGNED_DIR = "official_tmalign_results"
REFERENCE_DIR = "RPIC_all"
PYMOL_SCRIPT_DIR = "pymol_scripts"
IMAGE_DIR = "pymol_images"
DATE = "0821"

def create_pymol_script(script_path, ref_pdb, mobile_pdb, image_path):
    ref_pdb_abs = os.path.abspath(ref_pdb)
    mobile_pdb_abs = os.path.abspath(mobile_pdb)
    image_path_abs = os.path.abspath(image_path)
    image_path_no_ext, _ = os.path.splitext(image_path_abs)

    content = f"""
reinitialize
bg_color white
load {ref_pdb_abs}, reference
load {mobile_pdb_abs}, mobile

color green, reference
color magenta, mobile

set ray_trace_frames, 1
set ray_shadows, off

orient

png {image_path_no_ext}, width=800, height=600, dpi=300, ray=1
"""
    with open(script_path, 'w') as f:
        f.write(content)

def main():
    os.makedirs(PYMOL_SCRIPT_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    with open(PAIR_FILE, 'r') as f:
        protein_pairs = [line.strip().split() for line in f if line.strip()]

    all_scripts_to_run = []

    for pdb1, pdb2 in protein_pairs:
        # --- Gemini-Align Script ---
        gemini_mobile_pdb = os.path.join(GEMINI_ALIGNED_DIR, f"{pdb1}_aligned_to_{pdb2}_{DATE}.pdb")
        ref_pdb_path = os.path.join(REFERENCE_DIR, f"{pdb2}.pdb")
        if os.path.exists(gemini_mobile_pdb) and os.path.exists(ref_pdb_path):
            image_path = os.path.join(IMAGE_DIR, f"gemini_{pdb1}_vs_{pdb2}.png")
            script_filename = f"gemini_{pdb1}_vs_{pdb2}.pml"
            script_path = os.path.join(PYMOL_SCRIPT_DIR, script_filename)
            create_pymol_script(script_path, ref_pdb_path, gemini_mobile_pdb, image_path)
            all_scripts_to_run.append(script_filename)

        # --- Official TM-align Script ---
        official_mobile_pdb = os.path.join(OFFICIAL_ALIGNED_DIR, f"{pdb1}_vs_{pdb2}.pdb")
        if os.path.exists(official_mobile_pdb) and os.path.exists(ref_pdb_path):
            image_path = os.path.join(IMAGE_DIR, f"official_{pdb1}_vs_{pdb2}.png")
            script_filename = f"official_{pdb1}_vs_{pdb2}.pml"
            script_path = os.path.join(PYMOL_SCRIPT_DIR, script_filename)
            create_pymol_script(script_path, ref_pdb_path, official_mobile_pdb, image_path)
            all_scripts_to_run.append(script_filename)

    # Create a master script to run all other scripts
    with open(os.path.join(PYMOL_SCRIPT_DIR, "run_all.pml"), 'w') as f:
        for script_name in all_scripts_to_run:
            f.write(f"run {script_name}\n")

    print(f"Generated PyMOL scripts in '{PYMOL_SCRIPT_DIR}'")
    print(f"Images will be saved in '{IMAGE_DIR}'")
    print("\nTo run the scripts, open a terminal and execute:")
    print(f"pymol -c -d 'cd {os.path.abspath(PYMOL_SCRIPT_DIR)}; run run_all.pml'")

if __name__ == "__main__":
    main()
