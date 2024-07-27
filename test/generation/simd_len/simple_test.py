from kernel_tuner.generation.code.code import Code
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.tree.tree import TreeBuilder, Tree
from kernel_tuner.generation.rules.set_simd_length_rule import SimdOptimizationRule

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

  #pragma omp target enter data map(to: a[0:100000000])

  #pragma omp target teams distribute parallel for simd
    for (int i = 0; i < N; ++i) 
    {
        array[i] = compute_value(i);
    }

  #pragma omp target exit data map(from: a[0:100000000])
}
"""

  after = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

#pragma omp target enter data map(to: a[0:100000000])

#pragma omp target  teams distribute parallel for simd simdlen(1)
for (int i = 0; i < N; ++i)
{
array[i] = compute_value(i);
}

#pragma omp target exit data map(from: a[0:100000000])
}
"""
  tree, context = common_init(before)
  rule = SimdOptimizationRule(tree, context, [])
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

  #pragma omp target enter data map(to: a[0:100000000])

  #pragma omp target teams distribute parallel for simd
    for (int i = 0; i < N; ++i) 
    {
        for (int j = 0; j < M; ++j) 
        {
            array[i][j] = compute_value(i, j);
        }
    }

  #pragma omp target exit data map(from: a[0:100000000])
}
"""

  after = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

#pragma omp target enter data map(to: a[0:100000000])

#pragma omp target  teams distribute parallel for simd simdlen(1)
for (int i = 0; i < N; ++i)
{
for (int j = 0; j < M; ++j)
{
array[i][j] = compute_value(i, j);
}
}

#pragma omp target exit data map(from: a[0:100000000])
}
"""
  tree, context = common_init(before)
  rule = SimdOptimizationRule(tree, context, [])
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

  #pragma omp target enter data map(to: a[0:100000000])

  #pragma omp target teams distribute parallel for simd simdlen(4)
    for (int i = 0; i < N; ++i) 
    {
        array[i] = compute_value(i);
    }

  #pragma omp target exit data map(from: a[0:100000000])
}
"""
  tree, context = common_init(before)
  rule = SimdOptimizationRule(tree, context, [])
  rule.run()
  rule_context = context.get(rule.rule_id)
  print(rule_context == None)


def test_4():
  before = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

  #pragma omp target enter data map(to: a[0:100000000])

  #pragma omp target teams distribute parallel for simd
    for (int i = 0; i < N; ++i) 
    {
        for (int j = 0; j < M; ++j) 
        {
            for (int k = 0; k < P; ++k) 
            {
                array[i][j][k] = compute_value(i, j, k);
            }
        }
    }

  #pragma omp target exit data map(from: a[0:100000000])
}
"""

  after = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

#pragma omp target enter data map(to: a[0:100000000])

#pragma omp target  teams distribute parallel for simd simdlen(1)
for (int i = 0; i < N; ++i)
{
for (int j = 0; j < M; ++j)
{
for (int k = 0; k < P; ++k)
{
array[i][j][k] = compute_value(i, j, k);
}
}
}

#pragma omp target exit data map(from: a[0:100000000])
}
"""
  tree, context = common_init(before)
  rule = SimdOptimizationRule(tree, context, [])
  rule.run()
  rule_context = context.get(rule.rule_id)
  print(after == rule_context[0].to_text())

test_1()
test_2()
test_3()
test_4()