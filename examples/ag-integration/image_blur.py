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


void image_blur(int width, int height, double *image, double *output) {
	#pragma tuner start image_blur image(double*:VECTOR_SIZE) output(double*:VECTOR_SIZE) width(int:WIDTH) height(int:HEIGHT)
  #pragma omp target teams distribute parallel for num__threads(nthreads)
  for (int i = 1; i < height-1; ++i) 
  {
    for (int j = 1; j < width-1; ++j)
    {
        output[i * width + j] = (image[i * width + j - width] + image[i * width + j + width] + image[i * width + j - 1] + image[i * width + j + 1] + image[i * width + j]) / 5.0;
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
    "image_blur",
    code,
    0,
    # tune_params=tune_params,
    compiler_options=["-fopenmp", "-mp=gpu"],
    compiler="nvc++",
    directive=directive
)

