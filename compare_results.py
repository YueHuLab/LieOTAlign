import os
import re
import glob

def parse_gemini_log(file_path):
    """Parses the log file from our gemini_tm_align_final.py script."""
    results = {
        'len': 'N/A', 'rmsd': 'N/A', 'tm1': 'N/A', 'tm2': 'N/A'
    }
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if "Found" in line and "residue pairs" in line:
                    match = re.search(r"Found (\d+) residue pairs", line)
                    if match: results['len'] = match.group(1)
                elif "Kabsch RMSD" in line:
                    match = re.search(r"Kabsch RMSD.*?=\s*([\d\.]+)", line)
                    if match: results['rmsd'] = match.group(1)
                elif "Standard TM-score (normalized by mobile" in line:
                    match = re.search(r"=\s*([\d\.]+)$", line)
                    if match: results['tm1'] = match.group(1)
                elif "Standard TM-score (normalized by reference" in line:
                    match = re.search(r"=\s*([\d\.]+)$", line)
                    if match: results['tm2'] = match.group(1)
    except FileNotFoundError:
        pass
    return results

def parse_tmalign_log(file_path):
    """Parses the log file from the official TM-align program."""
    results = {
        'len': 'N/A', 'rmsd': 'N/A', 'tm1': 'N/A', 'tm2': 'N/A'
    }
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            len_match = re.search(r"Aligned length=\s*(\d+)", content)
            if len_match: results['len'] = len_match.group(1)

            rmsd_match = re.search(r"RMSD=\s*([\d\.]+)", content)
            if rmsd_match: results['rmsd'] = rmsd_match.group(1)

            tm1_match = re.search(r"TM-score=\s*([\d\.]+) \(if normalized by length of Chain_1", content)
            if tm1_match: results['tm1'] = tm1_match.group(1)
            
            tm2_match = re.search(r"TM-score=\s*([\d\.]+) \(if normalized by length of Chain_2", content)
            if tm2_match: results['tm2'] = tm2_match.group(1)

    except FileNotFoundError:
        # This is expected if a corresponding official log doesn't exist
        pass
    return results

def main():
    gemini_log_dir_cutoff_5 = "batch_outputs"
    gemini_log_dir_cutoff_3 = "batch_outputs_cutoff_3.0"
    gemini_log_dir_cutoff_7 = "batch_outputs_cutoff_7.0"
    tmalign_log_dir = "official_tmalign_results"

    pair_file_path = "RPIC_all/id_pair.txt"
    if not os.path.exists(pair_file_path):
        print(f"Error: Pair file not found at {pair_file_path}")
        return

    with open(pair_file_path, 'r') as f:
        protein_pairs = [line.strip().split() for line in f if line.strip()]

    # Prepare table content
    header1 = f"{' ':<25} | {'Gemini-Align (Cutoff 3.0)':^48} | {'Gemini-Align (Cutoff 5.0)':^48} | {'Gemini-Align (Cutoff 7.0)':^48} | {'Official TM-align':^48}"
    header2 = f"{'Mobile':<12} {'Reference':<12} | {'AlignLen':>10} {'RMSD':>10} {'TM-score(mob)':>12} {'TM-score(ref)':>12} | {'AlignLen':>10} {'RMSD':>10} {'TM-score(mob)':>12} {'TM-score(ref)':>12} | {'AlignLen':>10} {'RMSD':>10} {'TM-score(mob)':>12} {'TM-score(ref)':>12} | {'AlignLen':>10} {'RMSD':>10} {'TM-score(mob)':>12} {'TM-score(ref)':>12}"
    separator = "-" * 253
    
    table_content = [separator, header1, header2, separator]

    gemini_cutoff_5_totals = {'len': 0, 'rmsd': 0, 'tm1': 0, 'tm2': 0, 'count': 0}
    gemini_cutoff_3_totals = {'len': 0, 'rmsd': 0, 'tm1': 0, 'tm2': 0, 'count': 0}
    gemini_cutoff_7_totals = {'len': 0, 'rmsd': 0, 'tm1': 0, 'tm2': 0, 'count': 0}
    tmalign_totals = {'len': 0, 'rmsd': 0, 'tm1': 0, 'tm2': 0, 'count': 0}

    for pdb1, pdb2 in protein_pairs:
        gemini_cutoff_5_log_pattern = os.path.join(gemini_log_dir_cutoff_5, f"{pdb1}_vs_{pdb2}_*.log")
        gemini_cutoff_3_log_pattern = os.path.join(gemini_log_dir_cutoff_3, f"{pdb1}_vs_{pdb2}_*.log")
        gemini_cutoff_7_log_pattern = os.path.join(gemini_log_dir_cutoff_7, f"{pdb1}_vs_{pdb2}_*.log")
        tmalign_log_pattern = os.path.join(tmalign_log_dir, f"{pdb1}_vs_{pdb2}.log")
        
        gemini_cutoff_5_log_files = glob.glob(gemini_cutoff_5_log_pattern)
        gemini_cutoff_3_log_files = glob.glob(gemini_cutoff_3_log_pattern)
        gemini_cutoff_7_log_files = glob.glob(gemini_cutoff_7_log_pattern)
        tmalign_log_files = glob.glob(tmalign_log_pattern)

        gemini_cutoff_5_log_path = gemini_cutoff_5_log_files[0] if gemini_cutoff_5_log_files else ""
        gemini_cutoff_3_log_path = gemini_cutoff_3_log_files[0] if gemini_cutoff_3_log_files else ""
        gemini_cutoff_7_log_path = gemini_cutoff_7_log_files[0] if gemini_cutoff_7_log_files else ""
        tmalign_log_path = tmalign_log_files[0] if tmalign_log_files else ""

        if not all([gemini_cutoff_5_log_path, gemini_cutoff_3_log_path, gemini_cutoff_7_log_path]):
            continue

        gemini_cutoff_5_results = parse_gemini_log(gemini_cutoff_5_log_path)
        gemini_cutoff_3_results = parse_gemini_log(gemini_cutoff_3_log_path)
        gemini_cutoff_7_results = parse_gemini_log(gemini_cutoff_7_log_path)
        tmalign_results = parse_tmalign_log(tmalign_log_path)

        # Accumulate totals
        for totals, results in [(gemini_cutoff_5_totals, gemini_cutoff_5_results), 
                                (gemini_cutoff_3_totals, gemini_cutoff_3_results), 
                                (gemini_cutoff_7_totals, gemini_cutoff_7_results), 
                                (tmalign_totals, tmalign_results)]:
            if results['len'] != 'N/A':
                totals['len'] += int(results['len'])
                totals['rmsd'] += float(results['rmsd'])
                totals['tm1'] += float(results['tm1'])
                totals['tm2'] += float(results['tm2'])
                totals['count'] += 1

        row = f"{pdb1:<12} {pdb2:<12} | " \
              f"{gemini_cutoff_3_results['len']:>10} {gemini_cutoff_3_results['rmsd']:>10} {gemini_cutoff_3_results['tm1']:>12} {gemini_cutoff_3_results['tm2']:>12} | " \
              f"{gemini_cutoff_5_results['len']:>10} {gemini_cutoff_5_results['rmsd']:>10} {gemini_cutoff_5_results['tm1']:>12} {gemini_cutoff_5_results['tm2']:>12} | " \
              f"{gemini_cutoff_7_results['len']:>10} {gemini_cutoff_7_results['rmsd']:>10} {gemini_cutoff_7_results['tm1']:>12} {gemini_cutoff_7_results['tm2']:>12} | " \
              f"{tmalign_results['len']:>10} {tmalign_results['rmsd']:>10} {tmalign_results['tm1']:>12} {tmalign_results['tm2']:>12}"
        table_content.append(row)

    table_content.append(separator)

    # Calculate and add averages
    if gemini_cutoff_5_totals['count'] > 0:
        gemini_cutoff_5_avg = {k: v / gemini_cutoff_5_totals['count'] for k, v in gemini_cutoff_5_totals.items() if k != 'count'}
        gemini_cutoff_3_avg = {k: v / gemini_cutoff_3_totals['count'] for k, v in gemini_cutoff_3_totals.items() if k != 'count'}
        gemini_cutoff_7_avg = {k: v / gemini_cutoff_7_totals['count'] for k, v in gemini_cutoff_7_totals.items() if k != 'count'}
        tmalign_avg = {k: v / tmalign_totals['count'] for k, v in tmalign_totals.items() if k != 'count'}
        
        avg_row = f"{'Average':<25} | " \
                  f"{gemini_cutoff_3_avg['len']:>10.2f} {gemini_cutoff_3_avg['rmsd']:>10.2f} {gemini_cutoff_3_avg['tm1']:>12.4f} {gemini_cutoff_3_avg['tm2']:>12.4f} | " \
                  f"{gemini_cutoff_5_avg['len']:>10.2f} {gemini_cutoff_5_avg['rmsd']:>10.2f} {gemini_cutoff_5_avg['tm1']:>12.4f} {gemini_cutoff_5_avg['tm2']:>12.4f} | " \
                  f"{gemini_cutoff_7_avg['len']:>10.2f} {gemini_cutoff_7_avg['rmsd']:>10.2f} {gemini_cutoff_7_avg['tm1']:>12.4f} {gemini_cutoff_7_avg['tm2']:>12.4f} | " \
                  f"{tmalign_avg['len']:>10.2f} {tmalign_avg['rmsd']:>10.2f} {tmalign_avg['tm1']:>12.4f} {tmalign_avg['tm2']:>12.4f}"
        table_content.append(avg_row)
        table_content.append(separator)

    # Print to console and save to file
    final_table = "\n".join(table_content)
    print(final_table)
    with open("comparison_summary.txt", "w") as f:
        f.write(final_table)
    print("\nComparison summary saved to comparison_summary.txt")

if __name__ == "__main__":
    main()