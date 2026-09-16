#!/usr/bin/env python3
"""
make_code_cards.py

Draws small code sample cards for the approach slides, in the same navy style
as make_diagrams.py. The lines are copied from the submitted task1.c and
task2.c (line numbers in each card's caption), and the slide 13 card is the
real output of task1.c at n = 130,000,000 on 3 processes.

    python3 make_code_cards.py      writes slide_code/code_slide3.png and so on

These are for the Canva deck only, so they are not in graphs/ and not in the zip.
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'slide_code')

BG, TEXT, SUB = '#0F172A', '#F8FAFC', '#94A3B8'
MPI, OMP, NOTE = '#00D2D3', '#FDCB6E', '#FF7675'

CARDS = [
    ('code_slide3.png', 'task1.c, lines 100 and 130 to 133',
     [(MPI, 'MPI_Bcast(&n, 1, MPI_UNSIGNED_LONG_LONG, 0, MPI_COMM_WORLD);'),
      (TEXT, ''),
      (TEXT, 'uint64_t start_val = 3 + (2 * rank);'),
      (TEXT, 'uint64_t step = 2 * size;'),
      (TEXT, 'for (uint64_t i = start_val; i < n; i += step) {')]),
    ('code_slide4.png', 'task1.c, lines 159, 173 and 184 to 186',
     [(MPI, 'MPI_Gather(&local_cnt_int, 1, MPI_INT, recv_counts, 1, MPI_INT, 0, MPI_COMM_WORLD);'),
      (TEXT, 'displacements[i] = displacements[i - 1] + recv_counts[i - 1];'),
      (MPI, 'MPI_Gatherv(local_primes, local_cnt_int, MPI_UNSIGNED_LONG_LONG,'),
      (MPI, '            all_primes, recv_counts, displacements, MPI_UNSIGNED_LONG_LONG,'),
      (MPI, '            0, MPI_COMM_WORLD);')]),
    ('code_slide8.png', 'task2.c, lines 82, 136 and 148 to 149',
     [(MPI, 'MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);'),
      (OMP, '#pragma omp parallel'),
      (TEXT, '{'),
      (OMP, '    #pragma omp for schedule(dynamic, 1000) nowait'),
      (TEXT, '    for (uint64_t i = 3 + (2 * rank); i < n; i += (2 * size)) {')]),
    ('code_slide15_threads.png', 'Output of task2.c at the same 6 workers, n = 130,000,000',
     [(SUB, 'OMP_NUM_THREADS=2 mpirun -np 3 ./task2    (3 x 2)'),
      (NOTE, '  rank   0,         2 primes: 0.0063 0.0063'),
      (TEXT, '  rank   1,   3689241 primes: 3.8596 3.8598'),
      (TEXT, '  rank   2,   3688944 primes: 3.8587 3.8590'),
      (SUB, '  Slowest thread / average thread: 1.50'),
      (TEXT, ''),
      (SUB, 'OMP_NUM_THREADS=3 mpirun -np 2 ./task2    (2 x 3)'),
      (TEXT, '  rank   0,   3689323 primes: 2.5599 2.5602 2.5601'),
      (TEXT, '  rank   1,   3688864 primes: 2.5599 2.5597 2.5600'),
      (SUB, '  Slowest thread / average thread: 1.00')]),
    ('code_slide13.png', 'Output of task1.c, mpirun -np 3 ./task1 130000000',
     [(TEXT, 'Search time per rank:'),
      (NOTE, '  rank   0:   0.0121 s          2 primes'),
      (TEXT, '  rank   1:   7.6711 s    3689241 primes'),
      (TEXT, '  rank   2:   7.6824 s    3688944 primes'),
      (SUB, 'Slowest rank / average rank: 1.50')]),
]


def card(fname, caption, lines):
    longest = max(len(t) for _, t in lines)
    w = max(6.0, 0.085 * longest + 0.6)
    h = 0.55 + 0.27 * len(lines)
    fig = plt.figure(figsize=(w, h), facecolor=BG, dpi=300)
    fig.text(0.3 / w, 1 - 0.28 / h, caption, fontsize=8.5, color=SUB, va='center',
             family='sans-serif')
    for i, (colour, text) in enumerate(lines):
        y = 1 - (0.62 + 0.27 * i) / h
        fig.text(0.3 / w, y, text, fontsize=9.5, color=colour, va='center', family='Menlo')
    path = os.path.join(OUT, fname)
    fig.savefig(path, facecolor=BG)
    plt.close(fig)
    print('wrote', path)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for c in CARDS:
        card(*c)
