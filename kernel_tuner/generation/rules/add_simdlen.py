from kernel_tuner.generation.rules.rule import RuleABC
from kernel_tuner.generation.tree.tree import Tree
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.token.pragma_token import PRAGMA_TOKEN_TYPE, PRAGMA_KEYWORDS, build_pragma_token
from kernel_tuner.generation.code.line import Line
from kernel_tuner.util import write_file
from kernel_tuner.generation.utils.util import *


class AddSimdLenRule(RuleABC):

  def __init__(self, tree: Tree, context: Context, initial_params: PragmaTuneParams):
    super().__init__(tree, context, initial_params)

  def run(self, debug_file=None):
    simd_pragmas = filter_pragmas_contains_keyword(self.tree.pragma_tokens, [PRAGMA_KEYWORDS.SIMD])
    for simd_pragma in simd_pragmas:
      new_keywords = [] if PRAGMA_KEYWORDS.SIMDLEN in simd_pragma.keywords else [PRAGMA_KEYWORDS.SIMDLEN]
      simd_pragma.modify_keywords(new_keywords, {PRAGMA_KEYWORDS.SIMDLEN: '1'})
      self.context.offer_with_new_token([simd_pragma], [simd_pragma], self.rule_id, self.generate_param())


  def generate_param(self) -> PragmaTuneParams:
    pass

"""


#pragma omp target simd -> #pragma omp target simd simdlen(1)



#pragma omp target parallel for num_threads(10) simd

                    |
                    ^

#pragma omp target parallel for num_threads(10) simd simdlen(1)

"""