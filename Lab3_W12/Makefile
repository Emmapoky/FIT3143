# FIT3143 Lab 3 - build the WSN simulator.
# Team: Erwyna Soo Wen Xin (36555789), Taabish Farooq Bhat (35473932)
#
# macOS (Homebrew clang) needs libomp spelled out; Linux/CAAS gcc only needs -fopenmp.
UNAME := $(shell uname)
ifeq ($(UNAME),Darwin)
OMPFLAGS = -Xpreprocessor -fopenmp -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp
else
OMPFLAGS = -fopenmp
endif

CC = mpicc
CFLAGS = -O2 -Wall -Wextra -std=gnu11
SRC = main.c node.c base_station.c common.c
HDR = wsn.h

wsn: $(SRC) $(HDR)
	$(CC) $(CFLAGS) $(SRC) -o wsn $(OMPFLAGS)

clean:
	rm -f wsn
