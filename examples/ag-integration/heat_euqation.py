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
#define WIDTH 1000
#define HEIGHT 1000

void heat_equation(int width, int height, double *current, double *next) {
    #pragma tuner start heat_equation current(double*:VECTOR_SIZE) next(double*:VECTOR_SIZE) width(int:WIDTH) height(int:HEIGHT)
    #pragma omp target teams distribute parallel for
    for (int i = 1; i < height-1; ++i)
    {
        for (int j = 1; j < width-1; ++j)
        {
            next[i * width + j] = 0.25 * (current[i * width + j - width] + current[i * width + j + width] + current[i * width + j - 1] + current[i * width + j + 1]);
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
    "heat_equation",
    code,
    0,
    # tune_params=tune_params,
    compiler_options=["-fopenmp", "-mp=gpu"],
    compiler="nvc++",
    directive=directive
)

