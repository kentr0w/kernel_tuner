from kernel_tuner.generation.code.code import Code
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.tree.tree import TreeBuilder, Tree
from kernel_tuner.generation.rules.rule import RuleABC
from kernel_tuner.generation.rules.add_num_threads_and_distribute_rule import AddNumThreadsAndDistributeRule
from kernel_tuner.generation.rules.add_chunk_size_to_schedule_rule import AddChunkSizeToScheduleRule
from kernel_tuner.generation.rules.add_schedule_rule import AddStaticScheduleRule
from kernel_tuner.generation.rules.add_reduction_rule import AddReductionRule
from kernel_tuner.generation.rules.add_parallel_no_simd import AddParallelInsteadOfSimd
from kernel_tuner.generation.rules.add_num_teams_and_thread_limit import AddNumTeamsAndThreadLimitRule
from kernel_tuner.generation.rules.add_simdlen import AddSimdLenRule
from kernel_tuner.generation.rules.remove_target import RemoveTargetRule
from kernel_tuner.generation.token.pragma_token import PragmaToken, PRAGMA_KEYWORDS
from kernel_tuner.util import write_file
from kernel_tuner.generation.utils.util import PragmaTuneParams, convertPragmaTuneToDict
from typing import Type

from kernel_tuner.core import DeviceInterface

rule_map = {
"add_schedule": AddStaticScheduleRule,
  "add_chunk_schedule": AddChunkSizeToScheduleRule,
  "add_teams_and_thread_limit": AddNumTeamsAndThreadLimitRule,
  "add_teams_and_distribute": AddNumThreadsAndDistributeRule,
  "add_reduction": AddReductionRule,
  "no_simd": AddParallelInsteadOfSimd,
  "simd_len": AddSimdLenRule,
  "no_target": RemoveTargetRule,
}

def generate_kernel_sources(
    initial_code_str: str,
    initial_tune_params: dict,
    rules: list[str],
    exclude_rules: list[str],
    debug_file=None
):
  code = Code(initial_code_str.split('\n'))
  if debug_file:
    write_file(debug_file, '='*10 + 'CODE' + '='*10 + '\n' + code.to_text() + '\n\n', "a")
  tree_builder = TreeBuilder(code)
  tree = tree_builder.build_tree()
  # tree.dfs_print()
  if debug_file:
    write_file(debug_file, '='*10 + 'TREE' + '='*10 + '\n\n', "a")
    tree.dfs_print(debug_file_name=debug_file)
  
  result_tune_param = []
  tree.dfs(convert_pragma_keyword_to_initiail_tune_params, initial_tune_params, result_tune_param)
  context = Context(code, result_tune_param)
  write_file(debug_file, '='*10 + 'RULES' + '='*10 + '\n\n', "a")

  result = [(code, result_tune_param)]
  for rule in get_rules(rules, exclude_rules):
    s_rule = rule(tree, context, result_tune_param)
    s_rule.run(debug_file)
    rule_context = context.get(s_rule.rule_id)
    if rule_context:
      write_file(debug_file, f"\nRULE {s_rule.rule_id} was applied!\n", "a")
      write_file(debug_file, f"\nPARAMS:\n{rule_context[1]}\n", "a")
      write_file(debug_file, '='*10 + 'CODE' + '='*10 + f"\n{rule_context[0].to_text()}\n\n", "a")
      result.append(rule_context)
  return post_process(result)

def get_rules(rules: list[str], exclude_rules: list[str]) -> list[Type[RuleABC]]:
  return [rule_map[rule_name] for rule_name in rules if rule_name not in exclude_rules and rule_name in rule_map]


def convert_pragma_keyword_to_initiail_tune_params(
    node: PragmaToken,    
    initial_tune_params: dict[str, str],
    result_tune_param: PragmaTuneParams
  ):
  for (pragma_keyword, param_name) in node.meta.items():
    if param_name in initial_tune_params:
      result_tune_param.append((pragma_keyword, param_name, initial_tune_params[param_name]))

def post_process(result: list[tuple[Code, PragmaTuneParams]]):
  result = list(filter(lambda x: x is not None, result))
  return list(map(lambda x: (x[0], convertPragmaTuneToDict(x[1])), result))