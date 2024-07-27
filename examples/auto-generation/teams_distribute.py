from kernel_tuner import tune_kernel
from kernel_tuner.interface import auto_tune_kernel
from kernel_tuner.utils.directives import (
    DirectiveCode,
    OpenMP,
    Cxx,
)

code = """
#include <stdlib.h>
#include <omp.h>

#define VECTOR_SIZE 10000
#define DOUBLE_VECTOR_SIZE 100000000

void vector_add(float *a, float *b, float *c) {  
	#pragma tuner start vector_add a(float*:DOUBLE_VECTOR_SIZE) b(float*:DOUBLE_VECTOR_SIZE) c(float*:DOUBLE_VECTOR_SIZE) size(int:DOUBLE_VECTOR_SIZE)
	#pragma omp target parallel for num_threads(nthreads)
    for ( int i = 0; i < VECTOR_SIZE; i++ ) 
    {
        for ( int j = 0; j < VECTOR_SIZE; j++ )
        {
            c[i*VECTOR_SIZE + j] = a[i*VECTOR_SIZE + j] + b[i*VECTOR_SIZE + j];
        }
    }
	#pragma tuner stop
}
"""

# Extract tunable directive
directive = DirectiveCode(OpenMP(), Cxx())

tune_params = dict()
tune_params["nthreads"] = [4, 8]

auto_tune_kernel(
    "vector_add",
    code,
    0,
    tune_params=tune_params,
    rules=['distribute_with_threads'],
    compiler_options=["-fopenmp", "-mp=gpu"],
    compiler="nvc++",
    directive=directive
)
