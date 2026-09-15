#!/bin/bash
####################################################################
# run_benchmarks.sh
# ------------------------------------------------------------------
# FIT3143 Lab #2 Task 3: collects every timing the seven required
# graphs are built from.
#
# Written by: Erwyna Soo Wen Xin (36555789)
#
# Team:
#   Erwyna Soo Wen Xin  (36555789)  esoo0013@student.monash.edu
#   Taabish Farooq Bhat (35473932)  ttaa0006@student.monash.edu
#
# Writes:
#   results_by_n.csv         graphs 1 and 2   run time and speedup vs n
#   results_by_procs.csv     graphs 3 and 6   speedup vs process/thread count
#   results_hybrid_t.csv     graph 4          hybrid vs MPI, threads growing
#   results_hybrid_total.csv graphs 5 and 7   hybrid vs OpenMP at matched width
#   phases_serial.csv        Task 3           serial phase split
#   phases_task1.csv         Task 3 + graph 6 MPI phase split
#   phases_task2.csv         Task 3 + graph 7 hybrid phase split
#
# Erwyna: how the timing works. Every headline number in results_*.csv
# is the wall clock of the WHOLE command as the shell sees it, mpirun
# included. That's on purpose. The overall speedup is meant to include
# communication, computation, sorting and file writing, and starting 14
# processes is time a user really waits for. Using the program's own
# timer instead would give Open MPI a free 0.2 to 0.3 seconds that the
# serial version never gets. The internal timers are still used, in the
# phases_*.csv files, but only to split each run into its serial and
# parallel parts for Amdahl's Law.
#
# Erwyna: fastest of REPS runs, not the mean. A slow run means
# something else on the laptop stole a core; a fast run cannot be
# faster than the work actually takes. The minimum is the closest
# thing to a noise free measurement I can get without a quiet machine.
#
# Run: chmod +x run_benchmarks.sh && ./run_benchmarks.sh
####################################################################

set -u

W4=${W4:-../Lab1_W4}             # where the Week 4 serial / pthread / OpenMP sources live
OUT=${OUT:-.}
BUILD=${BUILD:-./build}

# The spec asks for at least 30 values of n, and warns off run times
# under a second. 10M to 130M in steps of 4M is 31 values; at the top
# end the serial version takes about half a minute and even the widest
# parallel configuration stays above a second.
N_MIN=${N_MIN:-10000000}
N_STEP=${N_STEP:-4000000}
N_MAX=${N_MAX:-130000000}
N_FIXED=${N_FIXED:-130000000}    # n held still while the width changes
REPS=${REPS:-2}
REPS_SERIAL=${REPS_SERIAL:-1}    # the serial sweep is the expensive one

CORES=$(sysctl -n hw.ncpu 2>/dev/null || nproc)

# Erwyna: 1 to 14 covers every core, then 16, 20, 24, 28 to see what
# happens past the core count without paying for every value in
# between. Oversubscription is the interesting part, not its shape.
WIDTHS=${WIDTHS:-"1 2 3 4 5 6 7 8 9 10 11 12 13 14 16 20 24 28"}

# The n sweep holds the width still at the core count.
W_FIXED=${W_FIXED:-14}
HP=${HP:-2}                      # hybrid processes for the n sweep
HT=${HT:-7}                      # hybrid threads per process, 2 x 7 = 14

MPIRUN="mpirun --oversubscribe"

if [ -d /opt/homebrew/opt/libomp ]; then
	OMPFLAGS="-Xpreprocessor -fopenmp -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp"
	OMPCC="clang"
else
	OMPFLAGS="-fopenmp"
	OMPCC="gcc"
fi

mkdir -p "$BUILD"

echo "Cores on this machine: $CORES"
echo "n sweep: $N_MIN to $N_MAX step $N_STEP, width held at $W_FIXED"
echo "width sweep: $WIDTHS at n = $N_FIXED"
echo "each timing is the fastest of $REPS runs ($REPS_SERIAL for the serial sweep)"
echo ""

echo "--- Building (everything at -O2 so the comparison is about the parallelism, not the optimiser) ---"
gcc -O2 "$W4/task1.c" -o "$BUILD/serial"  -lm                          || exit 1
gcc -O2 "$W4/task2.c" -o "$BUILD/pthread" -lm -lpthread                || exit 1
$OMPCC -O2 "$W4/task3.c" -o "$BUILD/omp" -lm $OMPFLAGS                 || exit 1
mpicc -O2 task1.c -o "$BUILD/mpi" -lm                                 || exit 1
mpicc -O2 task2.c -o "$BUILD/hybrid" -lm $OMPFLAGS                    || exit 1
gcc -O2 serial_instr.c -o "$BUILD/serial_instr" -lm                    || exit 1
mpicc -O2 task1_instr.c -o "$BUILD/mpi_instr" -lm                     || exit 1
mpicc -O2 task2_instr.c -o "$BUILD/hybrid_instr" -lm $OMPFLAGS        || exit 1
echo "Build OK"
echo ""

now() { python3 -c 'import time;print("%.6f"%time.time())'; }

# best <reps> <command...>  -> prints the fastest wall clock in seconds
best() {
	local reps=$1; shift
	local b=""
	for _ in $(seq 1 "$reps"); do
		local t0 t1 d
		t0=$(now)
		"$@" > /dev/null 2>&1
		t1=$(now)
		d=$(python3 -c "print('%.6f'%($t1-$t0))")
		if [ -z "$b" ]; then b=$d; else
			b=$(python3 -c "print('%.6f'%min($b,$d))")
		fi
	done
	echo "$b"
}

# phase <outfile> <reps> <command...>  -> keeps the PHASE line from the
# fastest run, judged on the last field (total)
phase() {
	local out=$1; shift
	local reps=$1; shift
	local bestline="" bestval=""
	for _ in $(seq 1 "$reps"); do
		local line val
		line=$("$@" 2>/dev/null | grep '^PHASE,')
		[ -z "$line" ] && continue
		# total is always the third field from the end (total, comp_min, comp_mean)
		val=$(echo "$line" | awk -F, '{print $(NF-2)}')
		if [ -z "$bestval" ] || python3 -c "import sys;sys.exit(0 if $val < $bestval else 1)"; then
			bestval=$val; bestline=$line
		fi
	done
	[ -n "$bestline" ] && echo "${bestline#PHASE,}" >> "$out"
}

############################################################
# 1. n sweep - graphs 1 and 2
############################################################
echo "--- n sweep (graphs 1, 2) ---"
echo "n,serial_s,pthread_s,omp_s,mpi_s,mpi_internal_s,hybrid_s" > "$OUT/results_by_n.csv"
for n in $(seq -f "%.0f" $N_MIN $N_STEP $N_MAX); do
	ts=$(best $REPS_SERIAL "$BUILD/serial" "$n")
	tp=$(best $REPS "$BUILD/pthread" "$n" "$W_FIXED")
	to=$(best $REPS "$BUILD/omp" "$n" "$W_FIXED")
	tm=$(best $REPS $MPIRUN -np "$W_FIXED" "$BUILD/mpi" "$n")
	# the same MPI run as the program itself measures it, so we can show
	# on a slide how much of the gap is just mpirun starting up
	ti=$($MPIRUN -np "$W_FIXED" "$BUILD/mpi" "$n" 2>/dev/null | awk '/Total Wall Clock/{print $(NF-1)}')
	export OMP_NUM_THREADS=$HT
	th=$(best $REPS $MPIRUN -x OMP_NUM_THREADS -np "$HP" "$BUILD/hybrid" "$n")
	unset OMP_NUM_THREADS
	echo "$n,$ts,$tp,$to,$tm,$ti,$th" >> "$OUT/results_by_n.csv"
	echo "  n=$n serial=$ts pthread=$tp omp=$to mpi=$tm hybrid=$th"
done
echo ""

############################################################
# 2. width sweep - graphs 3 and 6
############################################################
echo "--- width sweep at n=$N_FIXED (graphs 3, 6) ---"
SERIAL_FIXED=$(best 2 "$BUILD/serial" "$N_FIXED")
echo "serial baseline at n=$N_FIXED: $SERIAL_FIXED s"
echo "width,serial_s,pthread_s,omp_s,mpi_s" > "$OUT/results_by_procs.csv"
for w in $WIDTHS; do
	tp=$(best $REPS "$BUILD/pthread" "$N_FIXED" "$w")
	to=$(best $REPS "$BUILD/omp" "$N_FIXED" "$w")
	tm=$(best $REPS $MPIRUN -np "$w" "$BUILD/mpi" "$N_FIXED")
	echo "$w,$SERIAL_FIXED,$tp,$to,$tm" >> "$OUT/results_by_procs.csv"
	echo "  width=$w pthread=$tp omp=$to mpi=$tm"
done
echo ""

############################################################
# 3. hybrid, threads growing at fixed processes - graph 4
############################################################
echo "--- hybrid threads sweep at n=$N_FIXED, $HP MPI processes (graph 4) ---"
MPI_REF=$(best $REPS $MPIRUN -np 4 "$BUILD/mpi" "$N_FIXED")
echo "threads,mpi_4proc_s,hybrid_4proc_s" > "$OUT/results_hybrid_t.csv"
for t in 1 2 3 4 5 6 7; do
	export OMP_NUM_THREADS=$t
	th=$(best $REPS $MPIRUN -x OMP_NUM_THREADS -np 4 "$BUILD/hybrid" "$N_FIXED")
	unset OMP_NUM_THREADS
	echo "$t,$MPI_REF,$th" >> "$OUT/results_hybrid_t.csv"
	echo "  threads=$t hybrid(4 proc)=$th  mpi(4 proc)=$MPI_REF"
done
echo ""

############################################################
# 4. hybrid at matched total width - graphs 5 and 7
############################################################
# Erwyna: the spec is specific here. If the hybrid runs 3 processes of
# 2 threads then the OpenMP version it is compared against has to run
# 6 threads, not 3. Same number of workers on the machine, different
# way of organising them. That is the only comparison that says
# anything about the model rather than about the head count.
echo "--- hybrid vs OpenMP at matched width (graphs 5, 7) ---"
COMBOS=${COMBOS:-"2:1 2:2 2:3 2:4 3:2 2:6 4:3 2:7 4:4 7:3 4:6 7:4"}
echo "procs,threads,width,hybrid_s,omp_s,pthread_s,mpi_s" > "$OUT/results_hybrid_total.csv"
for c in $COMBOS; do
	p=${c%%:*}; t=${c##*:}; w=$((p * t))
	export OMP_NUM_THREADS=$t
	th=$(best $REPS $MPIRUN -x OMP_NUM_THREADS -np "$p" "$BUILD/hybrid" "$N_FIXED")
	unset OMP_NUM_THREADS
	to=$(best $REPS "$BUILD/omp" "$N_FIXED" "$w")
	tp=$(best $REPS "$BUILD/pthread" "$N_FIXED" "$w")
	tm=$(best $REPS $MPIRUN -np "$w" "$BUILD/mpi" "$N_FIXED")
	echo "$p,$t,$w,$th,$to,$tp,$tm" >> "$OUT/results_hybrid_total.csv"
	echo "  ${p}x${t} (width $w) hybrid=$th omp=$to pthread=$tp mpi=$tm"
done
echo ""

############################################################
# 5. phase measurements - Task 3 proper
############################################################
echo "--- phase measurements (Task 3) ---"

echo "n,procs,threads,primes,comp_s,write_s,total_s" > "$OUT/phases_serial.csv"
for n in $N_FIXED 30000000 70000000; do
	phase "$OUT/phases_serial.csv" 2 "$BUILD/serial_instr" "$n"
done

echo "n,procs,threads,primes,bcast_s,comp_s,imbal_s,gather_s,sort_s,write_s,total_s,comp_min_s,comp_mean_s" > "$OUT/phases_task1.csv"
for w in $WIDTHS; do
	phase "$OUT/phases_task1.csv" $REPS $MPIRUN -np "$w" "$BUILD/mpi_instr" "$N_FIXED"
	echo "  phases task1 width=$w done"
done

echo "n,procs,threads,primes,bcast_s,comp_s,merge_s,imbal_s,gather_s,sort_s,write_s,total_s,comp_min_s,comp_mean_s" > "$OUT/phases_task2.csv"
for c in $COMBOS; do
	p=${c%%:*}; t=${c##*:}
	export OMP_NUM_THREADS=$t
	phase "$OUT/phases_task2.csv" $REPS $MPIRUN -x OMP_NUM_THREADS -np "$p" "$BUILD/hybrid_instr" "$N_FIXED"
	unset OMP_NUM_THREADS
	echo "  phases task2 ${p}x${t} done"
done
echo ""

############################################################
# 6. correctness check - the numbers are worthless if the output is wrong
############################################################
echo "--- correctness ---"
"$BUILD/serial" 30000000 > /dev/null
tail -n +2 primes_serial.txt > "$BUILD/ref.txt"
$MPIRUN -np 8 "$BUILD/mpi" 30000000 > /dev/null
export OMP_NUM_THREADS=3
$MPIRUN -x OMP_NUM_THREADS -np 4 "$BUILD/hybrid" 30000000 > /dev/null
unset OMP_NUM_THREADS
diff -q "$BUILD/ref.txt" primes_task1.txt && echo "Task 1 output matches the serial reference"
diff -q "$BUILD/ref.txt" primes_task2.txt && echo "Task 2 output matches the serial reference"
echo ""
echo "Done. CSVs are in $OUT."
