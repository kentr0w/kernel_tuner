from kernel_tuner.generation.code.code import Code
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.tree.tree import TreeBuilder, Tree
from kernel_tuner.generation.rules.add_distribute_with_threads_rule import TeamsAndDistributionConfigurationRule


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

  #pragma omp target
  #pragma omp parallel for
  for (int i = 0; i < N; ++i) 
  {
      for (int j = 0; j < M; ++j) 
      {
          data[i][j] = func(i, j);
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

#pragma omp target
#pragma omp  teams distribute num_teams (nteams)
for (int i = 0; i < N; ++i)
{
#pragma omp  parallel for
for (int j = 0; j < M; ++j)
{
data[i][j] = func(i, j);
}
}

#pragma omp target exit data map(from: a[0:100000000])
}
"""
  tree, context = common_init(before)
  rule = TeamsAndDistributionConfigurationRule(tree, context, [])
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

  #pragma omp target
    #pragma omp parallel for schedule(static)
    for (int i = 0; i < N; ++i) 
    {
        for (int j = 0; j < M; ++j) 
        {
            matrix[i][j] += i * j;
        }
    }

    #pragma omp target
    #pragma omp parallel for
    for (int k = 0; k < P; ++k) 
    {
        for (int l = 0; l < Q; ++l) 
        {
            array[k][l] = k + l;
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

#pragma omp target
#pragma omp  teams distribute num_teams (nteams)
for (int i = 0; i < N; ++i)
{
#pragma omp  parallel for
for (int j = 0; j < M; ++j)
{
matrix[i][j] += i * j;
}
}

#pragma omp target
#pragma omp  teams distribute num_teams (nteams_A)
for (int k = 0; k < P; ++k)
{
#pragma omp  parallel for
for (int l = 0; l < Q; ++l)
{
array[k][l] = k + l;
}
}

#pragma omp target exit data map(from: a[0:100000000])
}
"""
  tree, context = common_init(before)
  rule = TeamsAndDistributionConfigurationRule(tree, context, [])
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

  #pragma omp target
    #pragma omp parallel
    {
        #pragma omp for
        for (int i = 0; i < N; ++i) 
        {
            for (int j = 0; j < M; ++j) 
            {
                data[i][j] = func(i, j);
            }
        }

        #pragma omp parallel for
        for (int k = 0; k < P; ++k) 
        {
            for (int l = 0; l < Q; ++l) 
            {
                array[k][l] = compute_value(k, l);
            }
        }
    }

  #pragma omp target exit data map(from: a[0:100000000])
}
"""
  tree, context = common_init(before)
  # tree.dfs_print()
  rule = TeamsAndDistributionConfigurationRule(tree, context, [])
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

  #pragma omp target
  #pragma omp parallel for
  for (int i = 0; i < N; ++i) 
  {
      for (int j = 0; j < M; ++j) 
      {
          a[i] = compute_value(i, j);
      }
  }

  #pragma omp target
  #pragma omp parallel for
  for (int k = 1; k < P; ++k)
  {
      for (int l = 0; l < Q; ++l) 
      {
          array[k][l] = array[k-1][l] + another_compute(k, l);
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

#pragma omp target
#pragma omp  teams distribute num_teams (nteams)
for (int i = 0; i < N; ++i)
{
#pragma omp  parallel for
for (int j = 0; j < M; ++j)
{
a[i] = compute_value(i, j);
}
}

#pragma omp target
#pragma omp parallel for
for (int k = 1; k < P; ++k)
{
for (int l = 0; l < Q; ++l)
{
array[k][l] = array[k-1][l] + another_compute(k, l);
}
}

#pragma omp target exit data map(from: a[0:100000000])
}
"""
  tree, context = common_init(before)
  rule = TeamsAndDistributionConfigurationRule(tree, context, [])
  rule.run()
  rule_context = context.get(rule.rule_id)
  print(after == rule_context[0].to_text())


test_1()
test_2()
test_3()
test_4()