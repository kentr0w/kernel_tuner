from kernel_tuner.generation.code.code import Code
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.tree.tree import TreeBuilder, Tree
from kernel_tuner.generation.rules.configure_teams_and_threads_rule import TeamsAandThreadsConfigurationRule


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

  #pragma omp target
    #pragma omp parallel for
    for (int i = 0; i < N; ++i) 
    {
        results[i] = compute_value(i);
    }
}
"""

  after = """
#include <stdlib.h>
#include <omp.h>
#include <chrono>

#define VECTOR_SIZE 1000

extern "C" void vector_add(float * restrict a, float * restrict b, float * restrict c, int size) {

#pragma omp target
#pragma omp  teams num_teams (teams_number) thread_limit (nthread_limit)
#pragma omp parallel for
for (int i = 0; i < N; ++i)
{
results[i] = compute_value(i);
}
}
"""
  tree, context = common_init(before)
  rule = TeamsAandThreadsConfigurationRule(tree, context, [])
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

  #pragma omp target
    #pragma omp parallel for
    for (int i = 0; i < N; ++i) 
    {
        for (int j = 0; j < M; ++j) 
        {
            results[i][j] = compute_value(i, j);
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

#pragma omp target
#pragma omp  teams num_teams (teams_number) thread_limit (nthread_limit)
#pragma omp parallel for
for (int i = 0; i < N; ++i)
{
for (int j = 0; j < M; ++j)
{
results[i][j] = compute_value(i, j);
}
}
}
"""
  tree, context = common_init(before)
  rule = TeamsAandThreadsConfigurationRule(tree, context, [])
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

  #pragma omp target
    #pragma omp parallel for
    for (int i = 0; i < N; ++i) 
    {
        for (int j = 1; j < M; ++j) 
        {
            results[i][j] = results[i][j-1] + compute_value(i, j);
        }
    }
}
"""
  tree, context = common_init(before)
  rule = TeamsAandThreadsConfigurationRule(tree, context, [])
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

  #pragma omp target
    #pragma omp parallel
    {
        #pragma omp for
        for (int i = 0; i < N; ++i) {
            results[i] = compute_value(i);
        }

        #pragma omp parallel for
        for (int j = 0; j < M; ++j) {
            other_results[j] = another_compute(j);
        }
    }
}
"""
  tree, context = common_init(before)
  rule = TeamsAandThreadsConfigurationRule(tree, context, [])
  rule.run()
  rule_context = context.get(rule.rule_id)
  print(rule_context == None)

test_1()
test_2()
test_3()
test_4()