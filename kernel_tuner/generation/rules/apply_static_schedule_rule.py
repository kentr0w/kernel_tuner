from kernel_tuner.generation.rules.rule import RuleABC
from kernel_tuner.generation.tree.tree import Tree
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.token.pragma_token import PRAGMA_TOKEN_TYPE, PRAGMA_KEYWORDS, build_pragma_token
from kernel_tuner.generation.code.line import Line
from kernel_tuner.util import write_file
from kernel_tuner.generation.utils.util import *

# Only static schedule kind is supported for GPU
class ApplyStaticScheduleRule(RuleABC):

  def __init__(self, tree: Tree, context: Context, initial_params: dict):
    super().__init__(tree, context, initial_params)
    self.rule_id = 'add_schedule'

  def run(self, debug_file=None):
    pragma_for = filter_pragmas_contains_keyword(self.tree.pragma_tokens, [PRAGMA_KEYWORDS.FOR], [PRAGMA_KEYWORDS.SCHEDULE])
    for pragma_for_child in pragma_for:
      # uppper node -> pragma without for
      pragma_for_child.modify_keywords([], replace_keywords=[PRAGMA_KEYWORDS.FOR])

      new_node = build_pragma_token(
        PRAGMA_TOKEN_TYPE.FOR,
        [PRAGMA_KEYWORDS.SCHEDULE],
        pragma_for_child.initial_line.line_number,
        {PRAGMA_KEYWORDS.SCHEDULE: self.generate_param()},
        is_target_used=False
      )

      for ch in pragma_for_child.children:
        new_node.append_child(ch)
        pragma_for_child.remove_child(ch)
      pragma_for_child.append_child(new_node)

      self.context.offer_with_new_token([pragma_for_child], [new_node], self.rule_id)

      self.context.offer_with_add_pragma_above(new_node, pragma_for_child, self.rule_id)


  def generate_param(self) -> str:
    return self.context.get_tune_param_unique_name(
      rule_id = self.rule_id,
      pragma_keyword = PRAGMA_KEYWORDS.SCHEDULE,
      values = ['static'],
      name_prefix = 'scedule_type'
      )

"""

#pragma omp target parallel for num_threads(nthreads)

#pragma omp target parallel num_threads(16)
#pragma omp for schedule(dynamic)
"""