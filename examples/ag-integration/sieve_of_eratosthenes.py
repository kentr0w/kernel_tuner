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

void sieve_of_eratosthenes(int limit, bool *is_prime) {
  #pragma tuner start sieve_of_eratosthenes is_prime(bool*:VECTOR_SIZE) limit(int:VECTOR_SIZE)

  #pragma omp target parallel for
  for (int i = 2; i <= limit; ++i) 
  {
      is_prime[i] = true;
  }

  #pragma omp target teams distribute parallel for
  for (int p = 2; p <= limit; ++p) 
  {
      if (p * p > limit) {
        break;
      }
      if (is_prime[p]) 
      {
          for (int i = p * p; i <= limit; i += p) 
          {
              is_prime[i] = false;
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
    "sieve_of_eratosthenes",
    code,
    0,
    # tune_params=tune_params,
    compiler_options=["-fopenmp", "-mp=gpu"],
    compiler="nvc++",
    directive=directive
)

