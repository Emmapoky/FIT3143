#include <stdio.h>
#include <mpi.h>
int main(int argc,char**argv){MPI_Init(&argc,&argv);
printf("MPI_PROC_NULL=%d\n",MPI_PROC_NULL);
int ns[]={4,6,7,8,9,12,16,24};for(int k=0;k<8;k++){int d[2]={0,0};MPI_Dims_create(ns[k],2,d);printf("Dims_create(%d,2,{0,0}) -> [%d x %d]\n",ns[k],d[0],d[1]);}
int d3[3]={0,0,0};MPI_Dims_create(24,3,d3);printf("Dims_create(24,3) -> [%d x %d x %d]\n",d3[0],d3[1],d3[2]);
int d4[2]={0,3};MPI_Dims_create(12,2,d4);printf("Dims_create(12,2,{0,3}) -> [%d x %d]\n",d4[0],d4[1]);
MPI_Finalize();}
