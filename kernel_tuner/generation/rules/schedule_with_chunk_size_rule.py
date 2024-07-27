from kernel_tuner.generation.rules.rule import RuleABC
from kernel_tuner.generation.tree.tree import Tree
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.token.pragma_token import PRAGMA_TOKEN_TYPE, PRAGMA_KEYWORDS, build_pragma_token
from kernel_tuner.generation.code.line import Line
from kernel_tuner.util import write_file
from kernel_tuner.generation.utils.util import *

# Only static schedule kind is supported for GPU
class SchedulingOptimizationRule(RuleABC):

  def __init__(self, tree: Tree, context: Context, initial_params: dict):
    super().__init__(tree, context, initial_params)
    self.rule_id = 'add_chunk_schedule'

  def run(self, debug_file=None):
    pragma_for = filter_pragmas_contains_keyword(self.tree.pragma_tokens, [PRAGMA_KEYWORDS.SCHEDULE])
    for pragma_for_child in pragma_for:      
      if PRAGMA_KEYWORDS.SCHEDULE in pragma_for_child.meta:
        schedule = pragma_for_child.meta[PRAGMA_KEYWORDS.SCHEDULE].strip()
        if schedule == 'static':
          new_param_name = self.generate_param()
          pragma_for_child.meta[PRAGMA_KEYWORDS.SCHEDULE] = f"static, {new_param_name}"
          pragma_for_child.modify_keywords([], pragma_for_child.meta)
          self.context.offer_with_new_token([pragma_for_child], [pragma_for_child], self.rule_id)


  def generate_param(self) -> str:
    return self.context.get_tune_param_unique_name(
      rule_id = self.rule_id,
      pragma_keyword = PRAGMA_KEYWORDS.SCHEDULE,
      values = ['16', '32'],
      name_prefix = 'chunk_size'
    )


"""
#pragma omp target parallel for num_threads(nthreads)

#pragma omp target parallel num_threads(16)
#pragma omp for schedule(dynamic)
"""