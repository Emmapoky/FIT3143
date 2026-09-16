#!/bin/bash
# make_zip.sh
#
# Builds FIT3143_Lab2_Submission.zip from this folder. Everything for Lab 2
# lives in Week8_Lab; this script stages a clean copy of the files the marker
# should see, in the layout named in SUBMISSION_README.md, and zips it.
#
#   ./make_zip.sh
#
# Erwyna: run this last, after make_pdfs.py and make_prompt_records.py, so the
# zip always holds the newest PDFs.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/FIT3143_Lab2_Submission.zip"
STAGE="$(mktemp -d)/FIT3143_Lab2_Submission"

mkdir -p "$STAGE"/supporting/{caas,graphs,instruments,results,scripts,experiments}

cp "$HERE/SUBMISSION_README.md"                "$STAGE/README.md"
cp "$HERE/task1.c" "$HERE/task2.c"             "$STAGE/"
cp "$HERE/Task3_Performance_Evaluation.pdf"    "$STAGE/"
cp "$HERE/AI_Declaration.pdf"                  "$STAGE/"

cp "$HERE"/caas/*.job "$HERE"/caas/README.md   "$STAGE/supporting/caas/"
cp "$HERE"/caas/results/CAAS_Analysis.pdf \
   "$HERE"/caas/results/caas_results.txt       "$STAGE/supporting/caas/"

cp "$HERE"/graphs/*.png                        "$STAGE/supporting/graphs/"
cp "$HERE"/serial_instr.c "$HERE"/task1_instr.c "$HERE"/task2_instr.c \
                                               "$STAGE/supporting/instruments/"
cp "$HERE"/*.csv                               "$STAGE/supporting/results/"
cp "$HERE"/experiments/partition_variants.c "$HERE"/experiments/run_partition_comparison.py \
   "$HERE"/experiments/make_partition_graph.py "$HERE"/experiments/partition_comparison.csv \
   "$HERE"/experiments/partition_comparison.png "$STAGE/supporting/experiments/"
cp "$HERE"/make_diagrams.py "$HERE"/make_graphs.py "$HERE"/measure_launch.py \
   "$HERE"/run_benchmarks.sh "$HERE"/run_phases.py "$HERE"/run_phases_by_n.py \
                                               "$STAGE/supporting/scripts/"

rm -f "$OUT"
( cd "$(dirname "$STAGE")" && zip -r -X -q "$OUT" FIT3143_Lab2_Submission -x "*.DS_Store" )
rm -rf "$(dirname "$STAGE")"
echo "wrote $OUT"
unzip -l "$OUT" | tail -2
