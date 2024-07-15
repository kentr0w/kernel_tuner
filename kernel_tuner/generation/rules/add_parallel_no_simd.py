from kernel_tuner.generation.rules.rule import RuleABC
from kernel_tuner.generation.tree.tree import Tree
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.token.pragma_token import PRAGMA_TOKEN_TYPE, PRAGMA_KEYWORDS, build_pragma_token
from kernel_tuner.generation.code.line import Line
from kernel_tuner.util import write_file
from kernel_tuner.generation.utils.util import *
from kernel_tuner.generation.utils.patterns import operation_types
import re

"""
TODO
  Check if there's no parent with teams + distribute -> add it as well, otherwise just parallel for
"""

class AddParallelInsteadOfSimd(RuleABC):

  def __init__(self, tree: Tree, context: Context, initila_params: PragmaTuneParams):
    super().__init__(tree, context, initila_params)

  def run(self, debug_file=None):
    pragmas = filter_pragmas_by_type(self.tree.pragma_tokens, PRAGMA_TOKEN_TYPE.SIMD)
    pragmas_with_for_as_child = filter_pragmas_contains_child(pragmas, TOKEN_TYPE.FOR)
    for pragma_with_for_as_child in pragmas_with_for_as_child:
      for_token = pragma_with_for_as_child.find_first(TOKEN_TYPE.FOR) # TODO?
      if not for_token or len(for_token.children) != 2: # because for contains two children
        continue
      varialbe_reassignment = for_token.find_first(TOKEN_TYPE.LONG_VARIABLE_REASSIGNMENT)
      if not varialbe_reassignment:
        continue
      target = varialbe_reassignment.find_first(TOKEN_TYPE.TARGET)
      left_operand = varialbe_reassignment.find_first(TOKEN_TYPE.LEFT_OPERAND)
      right_operand = varialbe_reassignment.find_first(TOKEN_TYPE.RIGHT_OPERAND)

      if None in [target, left_operand, right_operand]:
        continue  
      if self.__is_target_used_in_operand(target, left_operand, right_operand):
        continue

      new_node = build_pragma_token(
        PRAGMA_TOKEN_TYPE.PARALLEL,
        [PRAGMA_KEYWORDS.FOR],
        pragma_with_for_as_child.line.line_number,
        meta = pragma_with_for_as_child.meta,
        is_target_used=True
      )

      self.context.offer_with_new_token([pragma_with_for_as_child], [new_node], self.rule_id, self.generate_param())    
    pass

  def generate_param(self) -> PragmaTuneParams:
    return self.initial_params

  def __is_target_used_in_operand(self, target: Token, left_operand: Token, right_operand: Token) -> bool:

    target_array = target.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
    left_array = left_operand.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
    right_array = right_operand.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
    target_name = None
    
    if target_array:      
      if not left_array and not right_array:
        return False
      target_name = target_array.meta[TOKEN_TYPE.ARRAY_NAME]
    else:
      target_variable = target.find_first(TOKEN_TYPE.VARIABLE_NAME)
      target_name = target_variable.line.content
      
    if left_array:
      if left_array.meta[TOKEN_TYPE.ARRAY_NAME] == target_name:
        return True
      if pattern.is_array_index_contains_another(left_array.meta[TOKEN_TYPE.ARRAY_INDEX], target_name):
        return True

    if right_array:
      if right_array.meta[TOKEN_TYPE.ARRAY_NAME] == target_name:
        return True
      if pattern.is_array_index_contains_another(right_array.meta[TOKEN_TYPE.ARRAY_INDEX], target_name):
        return True

    return False

