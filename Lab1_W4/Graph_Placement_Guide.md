# Graph placement guide for the Canva deck

All nine PNGs live in Lab1_W4/graphs. Drag each one from Finder straight onto
the Canva page, then size and position as below. Every graph already carries
its own title, axis labels and a grey caption line inside the image, so you
never need to add text under a graph. The deck grows from 11 to 13 pages.
When you are done, tell me and I will renumber every footer, retitle the two
new pages and split the speaker notes for them.

Canva sizing tip: click the placed image, then use the position panel and type
the width, x and y numbers exactly. Height sets itself.

## Page 4, NEW page. Duplicate the slide "POSIX Threads: Scaling on 14 Cores"

Right click that slide, choose Duplicate page, and drag the copy to sit
BEFORE the original. On the copy:

* Delete the four bars, the four time labels, the four thread labels and the
  Plateau text. Keep only the section label, the title and the footer.
* Retitle to: POSIX Threads: Faster at Every n
* Place graph1_runtime_serial_vs_pthread_by_n.png
  width 800, x 130, y 280
* Place graph2_speedup_pthread_by_n.png
  width 800, x 990, y 280

## Page 5, the original "POSIX Threads: Scaling on 14 Cores"

* Delete the four bars, the four time labels, the four thread labels and the
  Plateau ≈ 9.7× text. The graphs show all of it.
* Place graph3_runtime_serial_vs_pthread_by_threads.png
  width 800, x 130, y 280
* Place graph4_speedup_pthread_by_threads.png
  width 800, x 990, y 280

## Page 7, "OpenMP: Steady Speedup at Any n"

* Delete the teal curve segments, the two axis lines, the 1M to 30M axis
  text, the big 9.37× number and its caption line. Keep title and footer.
* Place graph5_runtime_serial_vs_omp_by_n.png
  width 800, x 130, y 280
* Place graph6_speedup_omp_by_n.png
  width 800, x 990, y 280

## Page 8, NEW page. Duplicate "OpenMP Edges Ahead"

Duplicate it and drag the copy to sit BEFORE the original. On the copy:

* Delete the two big numbers, their two captions, the two grey description
  lines, the vertical divider and the green bottom line. Keep the section
  label, title and footer.
* Retitle to: Pthreads vs OpenMP, Measured
* Place graph7_runtime_pthread_vs_omp_by_n.png
  width 760, x 150, y 300
* Place graph8_runtime_pthread_vs_omp_by_threads.png
  width 760, x 1010, y 300
* White graph cards on the dark background is intended, they read as panels.

## Page 9, the original "OpenMP Edges Ahead"

No change. It stays as the summary slide after the measured comparison.

## Page 12, "How the Numbers Were Measured" (appendix)

* Click the stock laptop photo on the right and delete it.
* Place graph9_workload_distribution.png
  width 800, x 1010, y 260
  This puts the block against chunk and schedule comparison evidence into the
  deck, which backs the claims on pages 3 and 6.

## Pages that do not change

Title, Problem Overview, Split Smarter, One Pragma, What We Learned,
Questions, Thank you.

## Final page order, 13 pages

1 Title
2 Problem Overview and Baseline
3 POSIX Threads: Split Smarter
4 POSIX Threads: Faster at Every n, graphs 1 and 2
5 POSIX Threads: Scaling on 14 Cores, graphs 3 and 4
6 OpenMP: One Pragma, Same Parallelism
7 OpenMP: Steady Speedup at Any n, graphs 5 and 6
8 Pthreads vs OpenMP, Measured, graphs 7 and 8
9 OpenMP Edges Ahead
10 What We Learned
11 Questions and Key Numbers
12 Appendix: How the Numbers Were Measured, graph 9
13 Thank you

All eight required graphs then appear in the required sections in spec order,
plus the extra comparison in the clearly labelled appendix. The speaking
script does not change: the notes on page 4 old numbering already narrate
graphs 1 to 4 and the notes on the comparison slide narrate graphs 7 and 8.
Once your images are in, ping me and I will fix every footer number, the new
titles if you skipped them, and move the right half of each speaker note onto
the new pages.
