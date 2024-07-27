from kernel_tuner.generation.code.code import Code
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.tree.tree import TreeBuilder, Tree
from kernel_tuner.generation.rules.rule import RuleABC
from kernel_tuner.generation.rules.add_distribute_with_threads_rule import TeamsAndDistributionConfigurationRule
from kernel_tuner.generation.rules.schedule_with_chunk_size_rule import SchedulingOptimizationRule
from kernel_tuner.generation.rules.apply_static_schedule_rule import ApplyStaticScheduleRule
from kernel_tuner.generation.rules.add_reduction_clause_rule import AddReductionClauseRule
from kernel_tuner.generation.rules.replace_simd_with_parallel_rule import AddParallelInsteadOfSimdRule
from kernel_tuner.generation.rules.configure_teams_and_threads_rule import TeamsAandThreadsConfigurationRule
from kernel_tuner.generation.rules.set_simd_length_rule import SimdOptimizationRule
from kernel_tuner.generation.rules.remove_target_rule import RemoveTargetRule
from kernel_tuner.generation.token.pragma_token import PragmaToken, PRAGMA_KEYWORDS
from kernel_tuner.util import write_file
from kernel_tuner.generation.utils.util import PragmaTuneParams, convertPragmaTuneToDict
from typing import Type

from kernel_tuner.core import DeviceInterface

rule_map = {
  # "add_schedule": ApplyStaticScheduleRule,
  "add_chunk_schedule": SchedulingOptimizationRule,
  "teams_and_threads_limit": TeamsAandThreadsConfigurationRule,
  "teams_and_distribute": TeamsAndDistributionConfigurationRule,
  "reduction": AddReductionClauseRule,
  "no_simd": AddParallelInsteadOfSimdRule,
  "simd_len": SimdOptimizationRule,
  # "no_target": RemoveTargetRule,
}

def generate_kernel_sources(
    initial_code_str: str,
    rules: list[str],
    exclude_rules: list[str],
    initial_tune_params: dict,
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
  tree.dfs(convert_pragma_keyword_to_initiail_tune_params, result_tune_param, initial_tune_params)
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
    result_tune_param: PragmaTuneParams,
    initial_tune_params: dict[str, str],
  ):
  for (pragma_keyword, param_name) in node.meta.items():
    if initial_tune_params and param_name in initial_tune_params:
      result_tune_param.append((pragma_keyword, param_name, initial_tune_params[param_name]))

def post_process(result: list[tuple[Code, PragmaTuneParams]]):
  result = list(filter(lambda x: x is not None and x[0] is not None and x[1] is not None and len(x[1]) > 0, result))
  return list(map(lambda x: (x[0], convertPragmaTuneToDict(x[1])), result))