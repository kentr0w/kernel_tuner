from kernel_tuner.generation.rules.rule import RuleABC
from kernel_tuner.generation.tree.tree import Tree
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.token.pragma_token import PRAGMA_TOKEN_TYPE, PRAGMA_KEYWORDS, build_pragma_token
from kernel_tuner.generation.code.line import Line
from kernel_tuner.util import write_file
from kernel_tuner.generation.utils.util import *


class RemoveTargetRule(RuleABC):

  def __init__(self, tree: Tree, context: Context, initial_params: PragmaTuneParams):
    super().__init__(tree, context, initial_params)


  def run(self, debug_file=None):
    target_pragmas = list(filter(lambda x: x.is_target_used and not x.pragma_type.is_data(), self.tree.pragma_tokens))
    for target_pragma in target_pragmas:
      new_pragma_type = target_pragma.pragma_type
      new_keywords = list(filter(lambda x: x not in [PRAGMA_KEYWORDS.TEAMS, PRAGMA_KEYWORDS.NUM_TEAMS], target_pragma.keywords))
      if len(new_keywords) == 0:
        continue
      if target_pragma.pragma_type == PRAGMA_TOKEN_TYPE.TEAMS:
        new_pragma_type = None
        for nk in new_keywords:
          if nk.name in PRAGMA_TOKEN_TYPE:
            new_pragma_type = PRAGMA_TOKEN_TYPE[nk.name]
            new_keywords.remove(nk.name)
            break
      if not new_pragma_type:
        continue
      target_pragma.meta.pop(PRAGMA_KEYWORDS.TEAMS, None)
      target_pragma.meta.pop(PRAGMA_KEYWORDS.NUM_TEAMS, None)
      new_pragma = build_pragma_token(
        new_pragma_type,
        new_keywords,
        target_pragma.line.line_number,
        target_pragma.meta,
        False,
        target_pragma.level
      )
      self.context.offer_with_new_token([target_pragma], [new_pragma], self.rule_id)

  def generate_param(self) -> PragmaTuneParams:
    pass

"""


#pragma omp target simd -> #pragma omp simd

#pragma omp target parallel ... -> #pragma omp parallel ...   <- should be slower, but why not?


"""