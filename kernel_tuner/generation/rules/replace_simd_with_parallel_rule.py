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
  1) Check that in for only one child -> just long or function call
  2) If reduction -> short is possible
  3) If 
  4) Check long/short functin call doesn't contains params
"""

class AddParallelInsteadOfSimdRule(RuleABC):

  def __init__(self, tree: Tree, context: Context, initila_params: PragmaTuneParams):
    super().__init__(tree, context, initila_params)
    self.rule_id = 'no_simd'

  def run(self, debug_file=None):
    pragmas = filter_pragmas_by_type(self.tree.pragma_tokens, PRAGMA_TOKEN_TYPE.SIMD, False)
    pragmas_with_no_aligned = filter_pragmas_contains_keyword(pragmas, [PRAGMA_KEYWORDS.SIMD], [PRAGMA_KEYWORDS.ALIGNED])
    pragmas_with_for_as_child = filter_pragmas_contains_child(pragmas_with_no_aligned, TOKEN_TYPE.FOR)
    # self.tree.dfs_print()
    print(len(pragmas_with_for_as_child))
    for pragma_with_for_as_child in pragmas_with_for_as_child:
      is_reduction_used = PRAGMA_KEYWORDS.REDUCTION in pragma_with_for_as_child.keywords
      for_token = pragma_with_for_as_child.find_first(TOKEN_TYPE.FOR)
      if not for_token or len(for_token.children) != 2:
        continue
      for_child = list(filter(lambda x: x.type != TOKEN_TYPE.FOR_BODY, for_token.children))[0]
      if not for_child:
        continue
      if for_child.type not in [TOKEN_TYPE.LONG_VARIABLE_REASSIGNMENT, TOKEN_TYPE.FUNCTION_VARIABLE_REASSIGNMENT, TOKEN_TYPE.SHORT_VARIABLE_REASSIGNMENT]:
        continue
      varialbe_reassignment = for_token.find_first(TOKEN_TYPE.LONG_VARIABLE_REASSIGNMENT)
      is_correct = False
      if varialbe_reassignment:
        is_correct = is_reduction_used or self.__is_long_variable_reassignment_is_correct(varialbe_reassignment)
      else:
        varialbe_reassignment = for_token.find_first(TOKEN_TYPE.FUNCTION_VARIABLE_REASSIGNMENT)
        if varialbe_reassignment:
          is_correct = self.__is_function_variable_reassignment_is_correct(varialbe_reassignment)
        else:
          varialbe_reassignment = for_token.find_first(TOKEN_TYPE.SHORT_VARIABLE_REASSIGNMENT)
          if varialbe_reassignment:
            is_correct = is_reduction_used
      if is_correct:
        new_node = build_pragma_token(
          PRAGMA_TOKEN_TYPE.PARALLEL,
          [PRAGMA_KEYWORDS.FOR] + ([PRAGMA_KEYWORDS.REDUCTION] if is_reduction_used else []),
          pragma_with_for_as_child.line.line_number,
          meta = pragma_with_for_as_child.meta,
          is_target_used=True
        )
        self.context.offer_with_new_token([pragma_with_for_as_child], [new_node], self.rule_id)    
    pass

  def generate_param(self) -> str:
    pass

  def __is_function_variable_reassignment_is_correct(self, varialbe_reassignment: PragmaToken) -> bool:
    target = varialbe_reassignment.find_first(TOKEN_TYPE.TARGET)
    parameters = varialbe_reassignment.find_first(TOKEN_TYPE.FUNCTION_PARAMETERS)
    if None in [target, parameters]:
      return False

    target_array = target.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
    if target_array:
      target_name = target_array.meta[TOKEN_TYPE.ARRAY_NAME]
    else:
      target_variable = target.find_first(TOKEN_TYPE.VARIABLE_NAME)
      if not target_variable:
        return False
      target_name = target_variable.line.content

    parameters_name = []
    for param in filter_tokens_by_type(parameters.children, TOKEN_TYPE.FUNCTION_PARAMETER):
      param_array = param.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
      if param_array:
        parameters_name.append(param_array.meta[TOKEN_TYPE.ARRAY_NAME])
      else:
        param_variable = param.find_first(TOKEN_TYPE.VARIABLE_NAME)
        if not param_variable:
          return False
        parameters_name.append(param_variable.line.content)

    return target_name not in parameters_name

  def __is_long_variable_reassignment_is_correct(self, varialbe_reassignment: PragmaToken) -> bool:

    target = varialbe_reassignment.find_first(TOKEN_TYPE.TARGET)
    left_operand = varialbe_reassignment.find_first(TOKEN_TYPE.LEFT_OPERAND)
    right_operand = varialbe_reassignment.find_first(TOKEN_TYPE.RIGHT_OPERAND)
    if None in [target, left_operand, right_operand]:
      return False
    target_array = target.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
    left_array = left_operand.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
    right_array = right_operand.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
    target_name = None
    if target_array:
      if not left_array and not right_array:
        return True
      target_name = target_array.meta[TOKEN_TYPE.ARRAY_NAME]
    else:
      target_variable = target.find_first(TOKEN_TYPE.VARIABLE_NAME)
      target_name = target_variable.line.content
    if left_array:
      if left_array.meta[TOKEN_TYPE.ARRAY_NAME] == target_name:
        return False
      if pattern.is_array_index_contains_another(left_array.meta[TOKEN_TYPE.ARRAY_INDEX], target_name):
        return False
    if right_array:
      if right_array.meta[TOKEN_TYPE.ARRAY_NAME] == target_name:
        return False
      if pattern.is_array_index_contains_another(right_array.meta[TOKEN_TYPE.ARRAY_INDEX], target_name):
        return False
    return True

