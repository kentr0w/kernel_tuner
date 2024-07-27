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

#define VECTOR_SIZE 1000000

void dot_product(float *a, float *b, int N) {
	#pragma tuner start dot_product a(float*:VECTOR_SIZE) b(float*:VECTOR_SIZE) c(float*:VECTOR_SIZE) N(int:VECTOR_SIZE)
  float result = 0.0;
  #pragma omp target teams for
  for (int i = 0; i < N; ++i) 
  {
      result += a[i] * b[i];
  }
	#pragma tuner stop
}
"""

# Extract tunable directive
directive = DirectiveCode(OpenMP(), Cxx())



auto_tune_kernel(
    "dot_product",
    code,
    0,
    # tune_params=tune_params,
    compiler_options=["-fopenmp", "-mp=gpu"],
    compiler="nvc++",
    directive=directive
)

