#!/bin/bash

# Script to run gemini_tm_align_final.py on a list of protein pairs.

# Get current date in MMDD format
DATE=$(date +%m%d)

# The file containing pairs of protein IDs
PAIR_FILE="RPIC_all/id_pair.txt"

# Directory to store the results
OUTPUT_DIR="batch_outputs_cutoff_7.0"

# --- Script Start ---

# Check if the pair file exists
if [ ! -f "$PAIR_FILE" ]; then
    echo "Error: Pair file not found at $PAIR_FILE"
    exit 1
fi

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "Starting batch alignment process with cutoff 7.0..."

# Read the file line by line, assuming PDB1 is mobile and PDB2 is reference
while read -r PDB1 PDB2; do
    # Skip empty or invalid lines
    if [ -z "$PDB1" ] || [ -z "$PDB2" ]; then
        continue
    fi

    echo "-----------------------------------------------------"
    echo "Processing pair: Mobile=${PDB1}, Reference=${PDB2}"

    # Define full file paths
    MOBILE_PDB="RPIC_all/${PDB1}.pdb"
    REFERENCE_PDB="RPIC_all/${PDB2}.pdb"
    OUTPUT_PDB="${OUTPUT_DIR}/${PDB1}_aligned_to_${PDB2}_${DATE}.pdb"
    LOG_FILE="${OUTPUT_DIR}/${PDB1}_vs_${PDB2}_${DATE}.log"

    # Check if the required PDB files exist before running
    if [ ! -f "$MOBILE_PDB" ]; then
        echo "Warning: Mobile PDB not found: $MOBILE_PDB. Skipping."
        continue
    fi
    if [ ! -f "$REFERENCE_PDB" ]; then
        echo "Warning: Reference PDB not found: $REFERENCE_PDB. Skipping."
        continue
    fi

    # Construct and display the command
    COMMAND="KMP_DUPLICATE_LIB_OK=True python3 gemini_tm_align_final.py --mobile \"$MOBILE_PDB\" --reference \"$REFERENCE_PDB\" --steps 5000 --cutoff 7.0 --output \"$OUTPUT_PDB\""
    echo "Executing command..."

    # Execute the command, redirecting all output (stdout and stderr) to the log file
    eval $COMMAND > "$LOG_FILE" 2>&1

    # Check the exit code of the last command
    if [ $? -eq 0 ]; then
        echo "Success. Log saved to: $LOG_FILE"
    else
        echo "Error during execution. Please check log file: $LOG_FILE"
    fi

done < "$PAIR_FILE"

echo "-----------------------------------------------------"
echo "Batch alignment process finished."