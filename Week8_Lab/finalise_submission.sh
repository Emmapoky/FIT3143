#!/bin/bash
# finalise_submission.sh
#
# Brings a submission folder on the Desktop up to date and zips it. Run it as
# the very last step before uploading to Moodle:
#
#   ~/FIT3143/Week8_Lab/finalise_submission.sh                       (FIT3143_Lab2_Submission)
#   ~/FIT3143/Week8_Lab/finalise_submission.sh ~/Desktop/SomeFolder  (any other folder)
#
# 1. Rebuilds AI_Declaration.pdf, so the Claude prompt record is complete.
# 2. Copies into the folder: the two programs, the Task 3 PDF, the declaration,
#    the README, and supporting/ (caas evidence, graphs, instruments, results,
#    scripts, experiments, primes_output). Any slides PDF already in the folder
#    is left alone.
# 3. Rebuilds supporting/caas from caas/job39361, so it holds only the job file
#    that actually ran on CAAS, its exact output and our analysis.
# 4. Zips the folder next to itself and checks the zip.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="${1:-$HOME/Desktop/FIT3143_Lab2_Submission}"
DEST="${DEST%/}"
[ -d "$DEST" ] || { echo "no submission folder at $DEST"; exit 1; }

cd "$HERE"
python3 make_ai_declaration.py

cp "$HERE/task1.c" "$HERE/task2.c" "$HERE/Task3_Performance_Evaluation.pdf" "$HERE/AI_Declaration.pdf" "$DEST/"
cp "$HERE/SUBMISSION_README.md" "$DEST/README.md"

S="$DEST/supporting"
mkdir -p "$S"/{graphs,instruments,results,scripts,experiments,primes_output}

# CAAS: start clean, so job files that never ran on CAAS cannot stay behind.
rm -rf "$S/caas"
mkdir -p "$S/caas"
cp "$HERE"/caas/job39361/run_all.job "$HERE"/caas/job39361/caas_results.txt \
   "$HERE"/caas/job39361/README.md "$HERE"/caas/results/CAAS_Analysis.pdf "$S/caas/"
# Screenshots taken on CAAS, and files fetched straight from CAAS, if any were saved there.
find "$HERE/caas/job39361" -maxdepth 1 -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.out" -o -iname "caas_headnode_*.txt" \) -exec cp {} "$S/caas/" \;

cp "$HERE"/graphs/*.png "$S/graphs/"
cp "$HERE"/serial_instr.c "$HERE"/task1_instr.c "$HERE"/task2_instr.c "$S/instruments/"
cp "$HERE"/*.csv "$S/results/"
cp "$HERE"/make_diagrams.py "$HERE"/make_graphs.py "$HERE"/measure_launch.py \
   "$HERE"/run_benchmarks.sh "$HERE"/run_phases.py "$HERE"/run_phases_by_n.py "$S/scripts/"
cp "$HERE"/experiments/partition_variants.c "$HERE"/experiments/run_partition_comparison.py \
   "$HERE"/experiments/make_partition_graph.py "$HERE"/experiments/partition_comparison.csv \
   "$HERE"/experiments/partition_comparison.png "$S/experiments/"
cp "$HERE"/primes_output/* "$S/primes_output/"

ZIP="$DEST.zip"
rm -f "$ZIP"
( cd "$(dirname "$DEST")" && zip -r -X -q "$ZIP" "$(basename "$DEST")" -x "*.DS_Store" )
unzip -tq "$ZIP"
echo "zip: $ZIP ($(du -h "$ZIP" | cut -f1), $(unzip -l "$ZIP" | tail -1 | awk '{print $2}') entries)"
echo "upload: the slides PDF, $ZIP and $DEST/AI_Declaration.pdf"
