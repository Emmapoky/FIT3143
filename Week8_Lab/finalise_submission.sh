#!/bin/bash
# finalise_submission.sh
#
# Brings the submission folder on the Desktop up to date and zips it. Run it
# as the very last step before uploading to Moodle:
#
#   ~/FIT3143/Week8_Lab/finalise_submission.sh
#
# 1. Rebuilds AI_Declaration.pdf, so the Claude prompt record is complete.
# 2. Copies the declaration, the README and the partitioning experiment into
#    ~/Desktop/FIT3143_Lab2_Submission.
# 3. Zips that folder to ~/Desktop/FIT3143_Lab2_Submission.zip and checks it.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/Desktop/FIT3143_Lab2_Submission"
[ -d "$DEST" ] || { echo "no submission folder at $DEST"; exit 1; }

cd "$HERE"
python3 make_ai_declaration.py

cp "$HERE/AI_Declaration.pdf" "$DEST/AI_Declaration.pdf"
cp "$HERE/SUBMISSION_README.md" "$DEST/README.md"
mkdir -p "$DEST/supporting/experiments"
cp "$HERE"/experiments/partition_variants.c "$HERE"/experiments/run_partition_comparison.py \
   "$HERE"/experiments/make_partition_graph.py "$HERE"/experiments/partition_comparison.csv \
   "$HERE"/experiments/partition_comparison.png "$DEST/supporting/experiments/"

cd "$HOME/Desktop"
rm -f FIT3143_Lab2_Submission.zip
zip -r -X -q FIT3143_Lab2_Submission.zip FIT3143_Lab2_Submission -x "*.DS_Store"
unzip -tq FIT3143_Lab2_Submission.zip
echo "zip entries: $(unzip -l FIT3143_Lab2_Submission.zip | tail -1 | awk '{print $2}')"
echo "upload: the slides PDF, ~/Desktop/FIT3143_Lab2_Submission.zip and $DEST/AI_Declaration.pdf"
