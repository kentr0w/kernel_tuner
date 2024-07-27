from kernel_tuner.generation.code.code import Code
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.tree.tree import TreeBuilder, Tree
from kernel_tuner.generation.rules.replace_simd_with_parallel_rule import AddParallelInsteadOfSimdRule


def common_init(initial_code_str: str):
  code = Code(initial_code_str.split('\n'))
  tree_builder = TreeBuilder(code)
  tree = tree_builder.build_tree()

  context = Context(code, [])

  return tree, context  

def test_1():
  before = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

  #pragma omp parallel for
  for (int i = 0; i < N; ++i) {
      #pragma omp simd
      for (int j = 0; j < M; ++j) {
          a[i][j] = func(i, j);
      }
  }

  #pragma omp simd
  for (int k = 0; k < P; ++k) {
      b[k] = another_func(qwe, c[k]);
  }
}
"""

  after = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

#pragma omp parallel for
for (int i = 0; i < N; ++i) {
#pragma omp target parallel for
for (int j = 0; j < M; ++j) {
a[i][j] = func(i, j);
}
}

#pragma omp target parallel for
for (int k = 0; k < P; ++k) {
b[k] = another_func(qwe, c[k]);
}
}
"""
  tree, context = common_init(before)
  rule = AddParallelInsteadOfSimdRule(tree, context, [])
  rule.run()
  rule_context = context.get(rule.rule_id)
  print(after == rule_context[0].to_text())

def test_2():
  before = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

  #pragma omp parallel for schedule(static)
    for (int i = 0; i < N; ++i) {
        #pragma omp simd
        for (int j = 0; j < M; ++j) {
            matrix[i][j] += i * j;
        }
    }

    #pragma omp parallel for
    for (int k = 0; k < P; ++k) {
        #pragma omp simd
        for (int l = 0; l < Q; ++l) {
            array[k][l] = k + l;
        }
    }
}
"""

  after = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

#pragma omp parallel for schedule(static)
for (int i = 0; i < N; ++i) {
#pragma omp target parallel for
for (int j = 0; j < M; ++j) {
matrix[i][j] += i * j;
}
}

#pragma omp parallel for
for (int k = 0; k < P; ++k) {
#pragma omp target parallel for
for (int l = 0; l < Q; ++l) {
array[k][l] = k + l;
}
}
}
"""
  tree, context = common_init(before)
  rule = AddParallelInsteadOfSimdRule(tree, context, [])
  rule.run()
  rule_context = context.get(rule.rule_id)
  print(after == rule_context[0].to_text())


def test_3():
  before = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

  #pragma omp parallel for
    for (int i = 0; i < N; ++i) {
        #pragma omp simd reduction(+:sum)
        for (int j = 0; j < M; ++j) {
            sum += data[i][j];
        }
    }

    #pragma omp simd
    for (int k = 0; k < P; ++k) {
        output[k] = process(k);
    }
}
"""

  after = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

#pragma omp parallel for
for (int i = 0; i < N; ++i) {
#pragma omp target parallel for reduction (+:sum)
for (int j = 0; j < M; ++j) {
sum += data[i][j];
}
}

#pragma omp target parallel for
for (int k = 0; k < P; ++k) {
output[k] = process(k);
}
}
"""
  tree, context = common_init(before)
  rule = AddParallelInsteadOfSimdRule(tree, context, [])
  rule.run()
  rule_context = context.get(rule.rule_id)
  print(after == rule_context[0].to_text())



def test_4():
  before = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

  #pragma omp parallel for
    for (int i = 0; i < N; ++i) {
        #pragma omp simd
        for (int j = 0; j < M; ++j) {
            results[i][j] = compute_value(i, j);
        }
    }

    #pragma omp parallel for
    for (int k = 0; k < P; ++k) {
        #pragma omp simd
        for (int l = 0; l < Q; ++l) {
            other_results[k][l] = another_compute(k, l);
        }
    }
}
"""

  after = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

#pragma omp parallel for
for (int i = 0; i < N; ++i) {
#pragma omp target parallel for
for (int j = 0; j < M; ++j) {
results[i][j] = compute_value(i, j);
}
}

#pragma omp parallel for
for (int k = 0; k < P; ++k) {
#pragma omp target parallel for
for (int l = 0; l < Q; ++l) {
other_results[k][l] = another_compute(k, l);
}
}
}
"""
  tree, context = common_init(before)
  rule = AddParallelInsteadOfSimdRule(tree, context, [])
  rule.run()
  rule_context = context.get(rule.rule_id)
  print(after == rule_context[0].to_text())


def test_5():
  before = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

  #pragma omp parallel for
    for (int i = 0; i < N; ++i) {
        #pragma omp simd
        for (int j = 0; j < M; ++j) {
            if (condition(i, j)) {
                data[i][j] = complex_operation(i, j);
            }
        }
    }
}
"""

  after = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

#pragma omp parallel for
for (int i = 0; i < N; ++i) {
#pragma omp simd
for (int j = 0; j < M; ++j) {
if (condition(i, j)) {
data[i][j] = complex_operation(i, j);
}
}
}
}
"""
  tree, context = common_init(before)
  rule = AddParallelInsteadOfSimdRule(tree, context, [])
  rule.run()
  rule_context = context.get(rule.rule_id)
  print(rule_context == None)



def test_6():
  before = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

  #pragma omp parallel for
    for (int i = 0; i < N; ++i) {
        #pragma omp simd aligned(data:64)
        for (int j = 0; j < M; ++j) {
            data[i][j] = process_data(i, j);
        }
    }
}
"""

  after = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

#pragma omp parallel for
for (int i = 0; i < N; ++i) {
#pragma omp simd aligned(data:64)
for (int j = 0; j < M; ++j) {
data[i][j] = process_data(i, j);
}
}
}
"""
  tree, context = common_init(before)
  rule = AddParallelInsteadOfSimdRule(tree, context, [])
  rule.run()
  rule_context = context.get(rule.rule_id)
  print(rule_context == None)


def test_7():
  before = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

  #pragma omp parallel for
    for (int i = 1; i < N; ++i) {
        #pragma omp simd
        for (int j = 0; j < M; ++j) 
        {
            array[i][j] = array[i-1][j] + compute_value(i, j);
        }
    }
}
"""

  after = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

#pragma omp parallel for
for (int i = 1; i < N; ++i) {
#pragma omp simd
for (int j = 0; j < M; ++j) 
{
array[i][j] = array[i-1][j] + compute_value(i, j);
}
}
}
"""
  tree, context = common_init(before)
  rule = AddParallelInsteadOfSimdRule(tree, context, [])
  rule.run()
  rule_context = context.get(rule.rule_id)
  print(rule_context == None)

test_1()
test_2()
test_3()
test_4()
test_5()
test_6()
test_7()