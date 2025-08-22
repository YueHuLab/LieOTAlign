#!/bin/bash

# Script to run the official TM-align on a list of protein pairs for comparison.

# The file containing pairs of protein IDs
PAIR_FILE="RPIC_all/id_pair.txt"

# Directory to store the results from the official TM-align
OUTPUT_DIR="official_tmalign_results"

# Path to the compiled TM-align executable
TMALIGN_EXEC="TMalign/TMalign"

# --- Script Start ---

# Check if the pair file exists
if [ ! -f "$PAIR_FILE" ]; then
    echo "Error: Pair file not found at $PAIR_FILE"
    exit 1
fi

# Check if the TM-align executable exists
if [ ! -x "$TMALIGN_EXEC" ]; then
    echo "Error: TM-align executable not found at $TMALIGN_EXEC"
    echo "Please ensure it is compiled correctly by running: g++ -O3 -ffast-math -lm -o $TMALIGN_EXEC TMalign/TMalign.cpp"
    exit 1
fi

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "Starting batch alignment process using official TM-align..."

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
    
    # Define output paths for TM-align
    # The -o option creates multiple files with this prefix
    SUP_PREFIX="${OUTPUT_DIR}/${PDB1}_vs_${PDB2}"
    LOG_FILE="${OUTPUT_DIR}/${PDB1}_vs_${PDB2}.log"

    # Check if PDB files exist
    if [ ! -f "$MOBILE_PDB" ]; then
        echo "Warning: Mobile PDB not found: $MOBILE_PDB. Skipping."
        continue
    fi
    if [ ! -f "$REFERENCE_PDB" ]; then
        echo "Warning: Reference PDB not found: $REFERENCE_PDB. Skipping."
        continue
    fi

    # Construct and run the command
    COMMAND="./$TMALIGN_EXEC \"$MOBILE_PDB\" \"$REFERENCE_PDB\" -o \"$SUP_PREFIX\""

    echo "Executing: $COMMAND"
    # Execute the command and redirect stdout to the log file
    eval $COMMAND > "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        echo "Success. Log and superposition files saved with prefix: $SUP_PREFIX"
    else
        echo "Error processing pair. Check log file for details: $LOG_FILE"
    fi

done < "$PAIR_FILE"

echo "-----------------------------------------------------"
echo "Official TM-align batch process finished."
