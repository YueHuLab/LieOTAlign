import torch
import torch.optim as optim
import argparse
import numpy as np
import os
import datetime

# --- Constants ---
AA_3_TO_1 = {
    'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D', 'CYS': 'C', 'GLN': 'Q', 
    'GLU': 'E', 'GLY': 'G', 'HIS': 'H', 'ILE': 'I', 'LEU': 'L', 'LYS': 'K', 
    'MET': 'M', 'PHE': 'F', 'PRO': 'P', 'SER': 'S', 'THR': 'T', 'TRP': 'W', 
    'TYR': 'Y', 'VAL': 'V'
}

# --- PDB Parsing & Writing ---

def parse_pdb(file_path, chain_id=None, c_alpha_only=True):
    """A robust PDB parser that handles alternative locations to prevent length mismatches."""
    coords, atom_lines, sequence = [], [], []
    seen_residues = set()
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if not line.startswith("ATOM"):
                    continue
                if c_alpha_only and line[12:16].strip() != "CA":
                    continue
                if chain_id and line[21].strip() != chain_id:
                    continue
                
                alt_loc = line[16]
                if alt_loc not in (' ', 'A'):
                    continue

                if c_alpha_only:
                    residue_uid = (line[21], line[22:27]) # (Chain ID, Residue Sequence Number + Insertion Code)
                    if residue_uid in seen_residues:
                        continue
                    seen_residues.add(residue_uid)
                coords.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
                atom_lines.append(line)
                sequence.append(AA_3_TO_1.get(line[17:20], 'X'))

    except FileNotFoundError:
        print(f"Error: PDB file not found at {file_path}")
        return None, None, None
    if not coords:
        print(f"Error: No matching C-alpha atoms found in {file_path} for specified chain.")
        return None, None, None
    return torch.tensor(coords, dtype=torch.float32), atom_lines, "".join(sequence)

def write_pdb(file_path, coords, atom_lines):
    with open(file_path, 'w') as f:
        for i, line in enumerate(atom_lines):
            x, y, z = coords[i]
            f.write(f"{line[:30]}{x:8.3f}{y:8.3f}{z:8.3f}{line[54:].rstrip()}\n")

# --- Core Alignment & Optimization Logic ---

def get_transformation_matrix(params_vector):
    w, u = params_vector[:3], params_vector[3:]
    W = torch.zeros((3, 3), dtype=params_vector.dtype, device=params_vector.device)
    W[0, 1], W[0, 2] = -w[2], w[1]; W[1, 0], W[1, 2] = w[2], -w[0]; W[2, 0], W[2, 1] = -w[1], w[0]
    return torch.linalg.matrix_exp(W), u

def get_d0(length):
    return 1.24 * (length - 15)**(1/3) - 1.8 if length > 15 else 0.5

def kabsch(A, B):
    assert A.shape == B.shape
    centroid_A, centroid_B = torch.mean(A, dim=0), torch.mean(B, dim=0)
    A_c, B_c = A - centroid_A, B - centroid_B
    H = A_c.T @ B_c
    U, S, V = torch.svd(H)
    R = V @ U.T
    if torch.det(R) < 0:
        V[:, -1] *= -1
        R = V @ U.T
    t = centroid_B - R @ centroid_A
    return R, t

def sinkhorn_iterations(M, num_iters=10):
    P = M
    for _ in range(num_iters):
        P = P / (P.sum(dim=1, keepdim=True) + 1e-8)
        P = P / (P.sum(dim=0, keepdim=True) + 1e-8)
    return P

def get_sinkhorn_alignment_score(coords_a, coords_b, len_a, len_b, cutoff=7.0, steepness=2.0, gamma=20.0, sinkhorn_iters=10):
    d0 = get_d0(len_b)
    dist_matrix = torch.cdist(coords_a, coords_b)
    s_ij = 1.0 / (1.0 + (dist_matrix / d0)**2)
    w_ij = torch.sigmoid(-(dist_matrix - cutoff) * steepness)
    reward_matrix = s_ij * w_ij
    P = sinkhorn_iterations(torch.exp(gamma * reward_matrix), num_iters=sinkhorn_iters)
    score = torch.sum(P * reward_matrix) / len_b
    return score, P

def decode_alignment_matrix(P):
    aligned_pairs = []
    used_cols = set()
    row_indices = torch.arange(P.shape[0])
    best_cols = torch.argmax(P, dim=1)
    confidences = P[row_indices, best_cols]
    sorted_indices = torch.argsort(confidences, descending=True)
    for i in sorted_indices:
        j = best_cols[i]
        if j.item() not in used_cols:
            aligned_pairs.append((i.item(), j.item()))
            used_cols.add(j.item())
    return sorted(aligned_pairs)

# --- Main Execution ---
def main():
    start_time = datetime.datetime.now()
    parser = argparse.ArgumentParser(description="A custom tool for protein structure alignment.", formatter_class=argparse.RawTextHelpFormatter,
        epilog="""    Author: Yue Hu (huyue@qlu.edu.cn)\n    Affiliation: Qilu University of Technology (Shandong Academy of Sciences)\n\n    Example Usage:\n      # Find the optimal superposition and save the matrix and superposed structure
      python3 gemini_tm_align_final.py --mobile mobile.pdb --reference ref.pdb --matrix_out matrix.txt --output aligned.pdb""")
    parser.add_argument("--mobile", required=True, help="Path to the mobile PDB file.")
    parser.add_argument("--reference", required=True, help="Path to the reference PDB file.")
    parser.add_argument("--output", default=None, help="Path to save the aligned mobile PDB.")
    parser.add_argument("--matrix_out", default=None, help="File to save the final transformation matrix.")
    parser.add_argument("--mobile_chain", default=None, help="Chain ID for the mobile protein.")
    parser.add_argument("--reference_chain", default=None, help="Chain ID for the reference protein.")
    parser.add_argument("--steps", type=int, default=5000, help="Number of optimization steps.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate.")
    parser.add_argument("--print_freq", type=int, default=100, help="Frequency of printing progress.")
    parser.add_argument("--cutoff", type=float, default=7.0, help="Distance cutoff for sigmoid weight.")
    parser.add_argument("--steepness", type=float, default=2.0, help="Steepness of the sigmoid cutoff.")
    parser.add_argument("--gamma", type=float, default=20.0, help="Sharpness factor for Sinkhorn.")
    parser.add_argument("--sinkhorn_iters", type=int, default=10, help="Number of Sinkhorn iterations.")
    args = parser.parse_args()

    print(f"\n**************************************************************************\n *              gemini_tm_align_final.py (2025)                       *\n * A tool to find the optimal superposition for protein structures      *\n * Developed with Gemini based on the principles of TM-align            *\n * Author: Yue Hu (huyue@qlu.edu.cn)                                  *\n **************************************************************************\n\nProgram started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    c_alpha_only = True
    mobile_coords, mobile_lines, mobile_seq = parse_pdb(args.mobile, args.mobile_chain, c_alpha_only=c_alpha_only)
    ref_coords, _, ref_seq = parse_pdb(args.reference, args.reference_chain, c_alpha_only=c_alpha_only)
    if mobile_coords is None or ref_coords is None: return

    len_mobile, len_ref = len(mobile_seq), len(ref_seq)
    print(f"Name of Chain_1: {os.path.basename(args.mobile)} (chain {args.mobile_chain or 'All'})\nName of Chain_2: {os.path.basename(args.reference)} (chain {args.reference_chain or 'All'})\nLength of Chain_1: {len_mobile} residues\nLength of Chain_2: {len_ref} residues\n")

    mobile_center, ref_center = mobile_coords.mean(dim=0), ref_coords.mean(dim=0)
    mobile_coords_opt, ref_coords_opt = mobile_coords - mobile_center, ref_coords - ref_center

    transform_params = torch.randn(1, 6, requires_grad=True); torch.nn.init.zeros_(transform_params)
    optimizer = optim.AdamW([transform_params], lr=args.lr)

    print("--- Finding Optimal Superposition (Sinkhorn Differentiable TM-score) ---")
    final_P = None
    for step in range(args.steps):
        optimizer.zero_grad()
        R, u = get_transformation_matrix(transform_params.squeeze(0))
        transformed_mobile = torch.matmul(mobile_coords_opt, R.T) + u
        score, P = get_sinkhorn_alignment_score(transformed_mobile, ref_coords_opt, len_mobile, len_ref, cutoff=args.cutoff, steepness=args.steepness, gamma=args.gamma, sinkhorn_iters=args.sinkhorn_iters)
        loss = -score
        if step % args.print_freq == 0 or step == args.steps - 1:
            print(f"Step {step:05d}: Sinkhorn Score = {score.item():.4f}")
        loss.backward();
        optimizer.step()
    final_P = P.detach()
    print("--- Global Search Finished ---\n")

    R_final, u_final = get_transformation_matrix(transform_params.detach().clone().squeeze(0))
    final_aligned_coords = torch.matmul(mobile_coords_opt, R_final.T) + u_final

    aligned_pairs = decode_alignment_matrix(final_P)
    aligned_len = len(aligned_pairs)
    
    print("--- Alignment Analysis ---")
    print(f"Found {aligned_len} residue pairs from the optimized alignment matrix.")

    if aligned_len > 0:
        mobile_indices, ref_indices = zip(*aligned_pairs)
        mobile_indices, ref_indices = list(mobile_indices), list(ref_indices)
        
        # Kabsch RMSD for the found alignment
        kabsch_R, kabsch_t = kabsch(mobile_coords_opt[mobile_indices], ref_coords_opt[ref_indices])
        kabsch_superposed_coords = (kabsch_R @ mobile_coords_opt[mobile_indices].T).T + kabsch_t
        d_sq_kabsch = torch.sum((kabsch_superposed_coords - ref_coords_opt[ref_indices])**2, dim=1)
        kabsch_rmsd = torch.sqrt(torch.mean(d_sq_kabsch)).item()
        print(f"Kabsch RMSD for the {aligned_len} aligned pairs = {kabsch_rmsd:.2f} Å")

        # Standard TM-score for the alignment found by our algorithm
        d_sq = torch.sum((final_aligned_coords[mobile_indices] - ref_coords_opt[ref_indices])**2, dim=1)
        tm_score_ref = (torch.sum(1.0 / (1.0 + d_sq / get_d0(len_ref)**2)) / len_ref).item()
        tm_score_mob = (torch.sum(1.0 / (1.0 + d_sq / get_d0(len_mobile)**2)) / len_mobile).item()

        print(f"Standard TM-score (normalized by reference, L={len_ref}) = {tm_score_ref:.5f}")
        print(f"Standard TM-score (normalized by mobile,   L={len_mobile}) = {tm_score_mob:.5f}")
        
        n_identical = sum(1 for i, j in aligned_pairs if mobile_seq[i] == ref_seq[j])
        seq_id = n_identical / aligned_len
        print(f"Sequence identity in aligned region = {seq_id:.3f}")

    print("\n--- Aligned Pairs (mobile, reference) ---")
    for i in range(0, len(aligned_pairs), 6):
        print(" ".join(map(str, aligned_pairs[i:i+6])))

    if args.output:
        print(f"\n--- Generating Final Aligned Structure ---")
        mobile_coords_full, mobile_lines_full, _ = parse_pdb(args.mobile, args.mobile_chain, c_alpha_only=False)
        mobile_center_full = mobile_coords_full.mean(dim=0)
        centered_mobile_full = mobile_coords_full - mobile_center_full
        final_full_coords_out = (torch.matmul(centered_mobile_full, R_final.T) + u_final) + ref_center
        print(f"Writing aligned mobile protein to '{args.output}'...")
        write_pdb(args.output, final_full_coords_out, mobile_lines_full)
        print(f"Success! You can now load '{args.reference}' and '{args.output}' into a viewer.")
        print(f"To verify, you can run: ./TMalign/TMalign {args.reference} {args.output}")

    if args.matrix_out:
        print(f"\n--- Saving Transformation Matrix ---")
        with open(args.matrix_out, 'w') as f:
            f.write(f"# Transformation matrix for {os.path.basename(args.mobile)} -> {os.path.basename(args.reference)}\n")
            f.write(f"# This matrix should be applied to the CENTERED coordinates of the mobile protein.\n")
            f.write(f"t[0] = {u_final[0]:.8f}, t[1] = {u_final[1]:.8f}, t[2] = {u_final[2]:.8f}\n")
            f.write(f"u[0][0] = {R_final[0,0]:.8f}, u[0][1] = {R_final[0,1]:.8f}, u[0][2] = {R_final[0,2]:.8f}\n")
            f.write(f"u[1][0] = {R_final[1,0]:.8f}, u[1][1] = {R_final[1,1]:.8f}, u[1][2] = {R_final[1,2]:.8f}\n")
            f.write(f"u[2][0] = {R_final[2,0]:.8f}, u[2][1] = {R_final[2,1]:.8f}, u[2][2] = {R_final[2,2]:.8f}\n")
        print(f"Transformation matrix saved to '{args.matrix_out}'")

    end_time = datetime.datetime.now()
    print(f"\nProgram finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\nTotal execution time: {end_time - start_time}")

if __name__ == '__main__':
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    main()