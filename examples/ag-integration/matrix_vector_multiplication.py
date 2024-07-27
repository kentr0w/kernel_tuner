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

void matrix_vector_multiplication(int N, double *matrix, double *vector, double *result) {    
    #pragma tuner start matrix_vector_multiplication matrix(double*:VECTOR_SIZE) result(double*:VECTOR_SIZE_2) vector(double*:VECTOR_SIZE_2) N(int:VECTOR_SIZE_2)

    #pragma omp target teams distribute parallel for simd
    for (int i = 0; i < N; ++i) {
        result[i] = 0.0;
    }

    // Perform matrix-vector multiplication
    #pragma omp target teams distribute parallel for simd
    for (int i = 0; i < N; ++i) {
      for (int j = 0; j < N; ++j) {
          result[i] += matrix[i * N + j] * vector[j];
      }
    }
    #pragma tuner stop
}
"""

# Extract tunable directive
directive = DirectiveCode(OpenMP(), Cxx())

auto_tune_kernel(
    "matrix_vector_multiplication",
    code,
    0,
    # tune_params=tune_params,
    # rules=['teams_and_threads_limit'],
    # exclude_rules=['reduction', 'no_target', 'add_schedule'],
    compiler_options=["-fopenmp", "-mp=gpu"],
    compiler="nvc++",
    directive=directive
)

