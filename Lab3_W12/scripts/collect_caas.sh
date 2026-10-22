#!/bin/bash
# Waits for the CAAS jobs, copies every output back UNEDITED, saves sacct,
# rebuilds the submission zip and refreshes the vault copy.
# Needs the open ssh master: ControlPath=/Users/erwynasoo/.ssh/caas.sock
JOBS=${1:-200554,200572,200573,200574}
SSH="ssh -o ControlPath=/Users/erwynasoo/.ssh/caas.sock -o ControlMaster=no esoo0013@student-caas-headnode.rep.monash.edu"
cd "$(dirname "$0")/.."
for i in $(seq 1 170); do
  out=$($SSH 'squeue -u $USER -h' 2>&1)
  case "$out" in *onnection*|*ontrol*|*denied*) echo "LOST SESSION: $out"; exit 2;; esac
  [ -z "$out" ] && break
  sleep 60
done
echo "queue empty, collecting"
rsync -a -e "ssh -o ControlPath=/Users/erwynasoo/.ssh/caas.sock -o ControlMaster=no" \
  --exclude wsn --exclude 'wsn_demo.job' --exclude 'wsn_sweep.job' \
  esoo0013@student-caas-headnode.rep.monash.edu:Lab3_W12/caas/ caas/
$SSH "sacct -j $JOBS --format=JobID,JobName%20,State,Elapsed,NodeList,ExitCode -P" > caas/sacct_lab3.txt
cat caas/sacct_lab3.txt
./scripts/make_submission.sh
V="/Users/erwynasoo/Desktop/Obsidian Vault/FIT3143_Parallel_Computing/01_Weekly_Materials/Week_12/Lab_3"
rsync -a --exclude wsn --exclude '*.o' --exclude .DS_Store --exclude 'logs/e*' --exclude 'FIT3143_Lab3_Submission/' ./ "$V/submission/"
cp FIT3143_Lab3_Submission.zip "$V/"
echo "COLLECTED"
