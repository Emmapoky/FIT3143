#!/bin/bash
####################################################################
# run_benchmarks.sh
# ------------------------------------------------------------------
# FIT3143 Lab #1 Task 4: collects the timings for our graphs.
#
# Writes three csv files:
#   results_by_n.csv        times for increasing n        (graphs 1, 2, 5, 6, 7)
#   results_by_threads.csv  times for increasing threads  (graphs 3, 4, 8)
#   results_extra.csv       block vs chunk, and the OpenMP schedules
#
# Written by: Erwyna Soo Wen Xin (36555789)
#
# Run: chmod +x run_benchmarks.sh && ./run_benchmarks.sh
####################################################################

set -u

# Settings. The spec asks for at least 30 different values of n, and says to
# test above 10 million and go up from there. This sweep runs 1M to 30M in
# steps of 1M, which is 30 values with 20 of them above the 10 million mark.
#
# Note on seq: BSD/macOS seq prints large numbers in scientific notation
# ("1e+06"), and atol() stops at the 'e' and reads that as 1. That silently
# turns the whole sweep into a search below n=1. The -f "%.0f" format string
# forces plain integers, which is what the programs need.
N_MIN=${N_MIN:-1000000}
N_STEP=${N_STEP:-1000000}
N_MAX=${N_MAX:-30000000}
N_FIXED=${N_FIXED:-30000000}    # n we hold still while changing the thread count
REPS=${REPS:-3}                 # run each timing this many times and keep the fastest

# How many cores this machine has. We sweep up to double that on purpose so we
# can see what happens when there are more threads than cores.
CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu)
T_MAX=$((CORES * 2))

# OpenMP on macOS: Apple's clang needs libomp from Homebrew and does not accept
# a bare -fopenmp. On Linux, plain "gcc -fopenmp" works, so we pick at run time.
if [ -d /opt/homebrew/opt/libomp ]; then
	OMP_BUILD="clang -O2 -Xpreprocessor -fopenmp -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp"
else
	OMP_BUILD="gcc -O2 -fopenmp"
fi

echo "Cores on this machine: $CORES"
echo "Thread sweep will run 1 to $T_MAX"
echo "n sweep will run $N_MIN to $N_MAX in steps of $N_STEP"
echo "Each timing is the fastest of $REPS runs"
echo ""

echo "--- Building ---"
gcc -O2 task1.c -o task1 -lm || exit 1
gcc -O2 task2.c -o task2 -lm -lpthread || exit 1
$OMP_BUILD task3.c -o task3 -lm || exit 1
gcc -O2 -DUSE_BLOCK task2.c -o task2_block -lm -lpthread || exit 1
echo "Build OK (all four at -O2 so the comparison is fair)"
echo ""

# The three OpenMP schedules we compare in results_extra.csv. task3.c has
# schedule(dynamic, CHUNK) hard coded, so rather than edit the file we are
# submitting, we copy it aside and swap the clause in the copy.
mkdir -p .sched_build
for sched in static dynamic guided; do
	sed "s/schedule(dynamic, CHUNK)/schedule($sched, CHUNK)/" task3.c > ".sched_build/task3_$sched.c"
	$OMP_BUILD ".sched_build/task3_$sched.c" -o ".sched_build/task3_$sched" -lm || exit 1
done
echo "Built the three schedule variants for the comparison"
echo ""

# Check all three agree before we bother timing anything. There are 664579
# primes below ten million, so if we do not get that number something is wrong.
echo "--- Correctness check at n = 10000000 ---"
./task1 10000000 > /dev/null
./task2 10000000 "$CORES" > /dev/null
./task3 10000000 "$CORES" > /dev/null
if ! diff -q primes_serial.txt primes_pthread.txt > /dev/null; then
	echo "FAIL: pthread output does not match serial"; exit 1
fi
if ! diff -q primes_serial.txt primes_omp.txt > /dev/null; then
	echo "FAIL: openmp output does not match serial"; exit 1
fi
FOUND=$(head -1 primes_serial.txt)
if [ "$FOUND" != "664579" ]; then
	echo "FAIL: expected 664579 primes but got $FOUND"; exit 1
fi
echo "PASS: all three gave the same sorted list of 664579 primes"
echo ""

# Pulls the number out of "Computational time only(s): 3.906362", runs the
# program REPS times and keeps the fastest. The fastest run is the one least
# disturbed by other things happening on the laptop at the time.
gettime () {
	local best="" t i
	for i in $(seq 1 "$REPS"); do
		t=$("$@" | grep "Computational time only" | awk '{print $NF}')
		if [ -z "$t" ]; then
			echo "ERROR: no timing line from: $*" >&2
			exit 1
		fi
		if [ -z "$best" ] || awk -v a="$t" -v b="$best" 'BEGIN{exit !(a<b)}'; then
			best="$t"
		fi
	done
	echo "$best"
}

echo "--- Sweep 1: changing n (this part takes a while) ---"
echo "n,serial_s,pthread_s,omp_s" > results_by_n.csv
for n in $(seq -f "%.0f" $N_MIN $N_STEP $N_MAX); do
	s=$(gettime ./task1 "$n")
	p=$(gettime ./task2 "$n" "$CORES")
	o=$(gettime ./task3 "$n" "$CORES")
	echo "$n,$s,$p,$o" >> results_by_n.csv
	echo "  n = $n   serial $s   pthread $p   omp $o"
done
echo ""

echo "--- Sweep 2: changing the thread count at n = $N_FIXED ---"
SERIAL_REF=$(gettime ./task1 "$N_FIXED")
echo "  serial reference time: $SERIAL_REF"
echo "threads,serial_s,pthread_s,omp_s" > results_by_threads.csv
for t in $(seq 1 $T_MAX); do
	p=$(gettime ./task2 "$N_FIXED" "$t")
	o=$(gettime ./task3 "$N_FIXED" "$t")
	echo "$t,$SERIAL_REF,$p,$o" >> results_by_threads.csv
	echo "  threads = $t   pthread $p   omp $o"
done
echo ""

# The two workload distribution comparisons. First one is our block
# version against our chunk version, second is the three OpenMP schedules.
echo "--- Sweep 3: our two workload distribution comparisons ---"
echo "label,time_s,serial_s" > results_extra.csv
b=$(gettime ./task2_block "$N_FIXED" "$CORES")
c=$(gettime ./task2       "$N_FIXED" "$CORES")
echo "pthread block,$b,$SERIAL_REF"  >> results_extra.csv
echo "pthread chunk,$c,$SERIAL_REF"  >> results_extra.csv
echo "  pthread one block per thread: $b"
echo "  pthread chunks:               $c"

for sched in static dynamic guided; do
	v=$(gettime ".sched_build/task3_$sched" "$N_FIXED" "$CORES")
	echo "omp $sched,$v,$SERIAL_REF" >> results_extra.csv
	echo "  omp schedule($sched): $v"
done
echo ""

echo "=== Done ==="
echo "  results_by_n.csv        $(($(wc -l < results_by_n.csv) - 1)) values of n"
echo "  results_by_threads.csv  $(($(wc -l < results_by_threads.csv) - 1)) thread counts"
echo "  results_extra.csv       $(($(wc -l < results_extra.csv) - 1)) comparisons"
echo ""
echo "Next step: CORES=$CORES N_FIXED=$N_FIXED python3 make_graphs.py"
