#include <stdio.h> 
#include <stdlib.h> 
#include <math.h> 
#include <time.h>

int main(int argc, char* argv[])
{
	int i;
	double sum = 0.0; double piVal;
	struct timespec start, end, startCompute, endCompute; 
	double time_taken_compute, time_taken_overall;
	
	clock_gettime(CLOCK_MONOTONIC, &start);
	if(argc < 2){
		printf("Error, insufficient arguments\n");
		return 0;
	}
	unsigned long N =  atoi(argv[1]);

	// Get current clock time. 
	clock_gettime(CLOCK_MONOTONIC, &startCompute);
	for(i = 0; i < N; i++)
	{
		sum += 4.0 / (1 + pow((2.0 * i + 1.0)/(2.0 * N), 2));
	}
	piVal = sum / (double)N;

	// Get the clock current time again
	// Subtract end from start to get the CPU time used. 
	clock_gettime(CLOCK_MONOTONIC, &endCompute);
	time_taken_compute = (endCompute.tv_sec - startCompute.tv_sec) * 1e9;
	time_taken_compute = (time_taken_compute + (endCompute.tv_nsec - startCompute.tv_nsec)) * 1e-9;

	printf("Calculated Pi value (Serial-AlgoI) = %12.9f\n", piVal);
	printf("Compute time (s): %lf\n", time_taken_compute);
	
	clock_gettime(CLOCK_MONOTONIC, &end);
	time_taken_overall = (end.tv_sec - start.tv_sec) * 1e9;
	time_taken_overall = (time_taken_overall + (end.tv_nsec - start.tv_nsec)) * 1e-9;
	printf("Overall time (s): %lf\n", time_taken_overall);

	return 0;
}
