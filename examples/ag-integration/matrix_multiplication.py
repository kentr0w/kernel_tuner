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
#define VECTOR_SIZE_2 100

void matrix_multiplication(int N, double *A, double *B, double *C) {    
    #pragma tuner start matrix_multiplication A(float*:VECTOR_SIZE) B(float*:VECTOR_SIZE) C(float*:VECTOR_SIZE) N(int:VECTOR_SIZE_2)
    #pragma omp target parallel for
    for (int i = 0; i < N; ++i) 
    {
        for (int j = 0; j < N; ++j) 
        {
          C[i*N + j] = 0;
        }
    }
    #pragma omp target parallel for
    for (int i = 0; i < N; ++i) 
    {
        for (int j = 0; j < N; ++j) 
        {
            for (int k = 0; k < N; ++k) 
            {
                C[i*N + j] += A[i*N + k] * B[k*N + j];
            }
        }
    }
    #pragma tuner stop
}
"""

# Extract tunable directive
directive = DirectiveCode(OpenMP(), Cxx())

auto_tune_kernel(
    "matrix_multiplication",
    code,
    0,
    # tune_params=tune_params,
    # rules=['teams_and_threads_limit'],
    # exclude_rules=['reduction', 'no_target', 'add_schedule'],
    compiler_options=["-fopenmp", "-mp=gpu"],
    compiler="nvc++",
    directive=directive
)

