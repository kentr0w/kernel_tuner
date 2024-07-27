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


void parallel_bubble_sort(int *arr, int n) {
  
  #pragma tuner start parallel_bubble_sort arr(float*:VECTOR_SIZE) n(int:VECTOR_SIZE)

  bool swapped = true;
  for (int i = 0; i < n-1 && swapped; ++i) 
  {
      swapped = false;
      #pragma omp target parallel for schedule(static)
      for (int j = 0; j < n-i-1; ++j) 
      {
          if (arr[j] > arr[j+1]) 
          {
              int temp = arr[j];
              arr[j] = arr[j+1];
              arr[j+1] = temp;
              swapped = true;
          }
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
    "parallel_bubble_sort",
    code,
    0,
    # tune_params=tune_params,
    # exclude_rules=['teams_and_threads_limit'],
    compiler_options=["-fopenmp", "-mp=gpu"],
    compiler="nvc++",
    directive=directive
)

