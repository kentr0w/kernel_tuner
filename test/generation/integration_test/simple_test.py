import kernel_tuner.utils.directives as directives_util
from kernel_tuner.generation.generation import generate_kernel_sources
import kernel_tuner.util as util
from kernel_tuner.utils.directives import (
    DirectiveCode,
    OpenMP,
    Cxx,
)

kernel_source = """

#define N 1000
#define M 1000
#define P 1000

extern "C" float compute_values(int N, int M, int P, double *array, double **matrix, double ***tensor) {

    #pragma omp target enter data map(to: array[0:N])
    #pragma omp target enter data map(to: matrix[0:M*M])
    #pragma omp target enter data map(to: tensor[0:P*P*P])

    double sum = 0.0;

    // Rule: Add simdlen(1) - Applicable
    #pragma omp target teams distribute parallel for simd
    for (int i = 0; i < N; ++i) {
        array[i] = compute_value(i);
    }

    // Rule: Add chunk size - Applicable
    #pragma omp target teams distribute parallel for schedule(static)
    for (int j = 0; j < M; ++j) {
        matrix[0][j] = compute_value(j);
    }

    // Rule: Add teams and thread limit - Applicable
    #pragma omp target parallel for reduction(+:sum)
    for (int k = 0; k < P; ++k) {
        sum += compute_value(k);
    }

    // Rule: Add simdlen(1) - Not applicable (already specified)
    #pragma omp target teams distribute parallel for simd simdlen(4)
    for (int l = 0; l < M; ++l) {
        matrix[1][l] = compute_value(l);
    }

    // Rule: Remove target - Not applicable
    #pragma omp target teams distribute parallel for
    for (int m = 0; m < N; ++m) {
        for (int n = 0; n < M; ++n) {
            matrix[m][n] = compute_value(m, n);
        }
    }

    // Rule: Add simdlen(1) - Not applicable (no simd directive)
    #pragma omp target teams distribute parallel for
    for (int p = 0; p < N; ++p) {
        for (int q = 0; q < M; ++q) {
            for (int r = 0; r < P; ++r) {
                tensor[p][q][r] = compute_value(p, q, r);
            }
        }
    }

    // Rule: Add chunk size - Not applicable (dynamic schedule)
    #pragma omp target teams distribute parallel for schedule(dynamic)
    for (int s = 0; s < N; ++s) {
        matrix[2][s] = compute_value(s);
    }

    #pragma omp target exit data map(to: array[0:N])
    #pragma omp target exit data map(to: matrix[0:M*M])
    #pragma omp target exit data map(to: tensor[0:P*P*P])
}
"""

# directive = DirectiveCode(OpenMP(), Cxx())
# initial_kernel_source, arguments = directives_util.preprocess_directive_source("compute_values", kernel_source, directive)
# print(initial_kernel_source)

debug_file = util.get_temp_filename()

q = generate_kernel_sources(
  kernel_source,
  [],
  rules = ['simd_len'],
  exclude_rules = [''],
  debug_file
)

print(len(q))