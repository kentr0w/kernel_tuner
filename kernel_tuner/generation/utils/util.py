from kernel_tuner.generation.token.pragma_token import *
from kernel_tuner.generation.token.code_token import CodeToken
from kernel_tuner.generation.token.token import TOKEN_TYPE
from typing import TypeAlias
from kernel_tuner.generation.utils.patterns import operation_types

PragmaTuneParams: TypeAlias = list[tuple[PRAGMA_KEYWORDS, str, list[str]]]

def convertPragmaTuneToDict(pragmaTuneParams: PragmaTuneParams) -> dict[str, list[str]]:
  return dict(map(lambda x: (x[1], x[2]), pragmaTuneParams))

def filter_pragmas_by_type(pragmas: list[PragmaToken], type: PRAGMA_TOKEN_TYPE, is_target_used: bool = True) -> list[PragmaToken]:
  return list(filter(lambda x: x.pragma_type == type and x.is_target_used == is_target_used, pragmas))

def filter_tokens_by_type(tokens: list[CodeToken], type: TOKEN_TYPE) -> list[CodeToken]:
  return list(filter(lambda x: x.type == type, tokens))

def filter_pragmas_contains_child(pragmas: list[PragmaToken], type: TOKEN_TYPE) -> list[PragmaToken]:
  return list(filter(lambda el: type in list(map(lambda x: x.type, el.children)), pragmas))

def filter_pragmas_contains_keyword(
    pragmas: list[PragmaToken], 
    contains_keywords: list[PRAGMA_KEYWORDS],
    exclude_keywords: list[PRAGMA_KEYWORDS] = []
) -> list[PragmaToken]:
  resulst = []
  for pragma in pragmas:
    if (any(x in contains_keywords for x in pragma.keywords) and all(x not in exclude_keywords for x in pragma.keywords)):
        resulst.append(pragma)
  return resulst


def get_for_child(token: Token) -> Token:
  for_token = token.find_first(TOKEN_TYPE.FOR) if token.type is not TOKEN_TYPE.FOR else token
  if not for_token or len(for_token.children) != 2:
    return None
  return list(filter(lambda x: x.type != TOKEN_TYPE.FOR_BODY, for_token.children))[0]

def find_varialbe_operations(varialbe_reassignment: Token) -> list[Token]:
  possible_operations = list(map(lambda x: varialbe_reassignment.find_first(x), operation_types.values()))
  return list(filter(lambda x: x, possible_operations))


def is_variable_reassignment_is_correct(varialbe_reassignment: Token) -> bool:
  target = varialbe_reassignment.find_first(TOKEN_TYPE.TARGET)
  left_operand = varialbe_reassignment.find_first(TOKEN_TYPE.LEFT_OPERAND)
  if None in [target, left_operand]:
    return False
  target_name = None
  target_array = target.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
  if target_array:
    target_name = target_array.meta[TOKEN_TYPE.ARRAY_NAME]
  else:
    target_variable = target.find_first(TOKEN_TYPE.VARIABLE_NAME)
    target_name = target_variable.line.content

  # do for left: is array -> name, is function -> params else var name
  left_names = []
  left_indexes = []
  left_array = left_operand.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
  left_function = left_operand.find_first(TOKEN_TYPE.FUNCTION_CALL)
  if left_array:
    left_names = [left_array.meta[TOKEN_TYPE.ARRAY_NAME]]
    left_indexes = [left_array.meta[TOKEN_TYPE.ARRAY_INDEX]]
  elif left_function:
    left_params = left_function.find_first(TOKEN_TYPE.FUNCTION_PARAMETERS)
    if left_params:
      for left_param in left_params.children:
        left_param_array = left_param.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
        if left_param_array:
          left_names.append(left_param_array.meta[TOKEN_TYPE.ARRAY_NAME])
          left_indexes.append(left_param_array.meta[TOKEN_TYPE.ARRAY_INDEX])
        else:
          left_param_var = left_param.find_first(TOKEN_TYPE.VARIABLE_NAME)
          if left_param_var:
            left_names.append(left_param_var.line.content)
  else:
    left_var = left_operand.find_first(TOKEN_TYPE.VARIABLE_NAME)
    left_names.append(left_var.line.content)

  if target_name in left_names:
      return False
  for li in left_indexes:
    if pattern.is_array_index_contains_another(li, target_name):
      return False
  return True
  

def is_function_variable_reassignment_is_correct(varialbe_reassignment: Token) -> bool:
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

def is_long_variable_reassignment_is_correct(varialbe_reassignment: Token) -> bool:

    target = varialbe_reassignment.find_first(TOKEN_TYPE.TARGET)
    left_operand = varialbe_reassignment.find_first(TOKEN_TYPE.LEFT_OPERAND)
    right_operand = varialbe_reassignment.find_first(TOKEN_TYPE.RIGHT_OPERAND)

    if None in [target, left_operand, right_operand]:
      return False
    
    target_name = None
    target_array = target.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
    if target_array:
      target_name = target_array.meta[TOKEN_TYPE.ARRAY_NAME]
    else:
      target_variable = target.find_first(TOKEN_TYPE.VARIABLE_NAME)
      target_name = target_variable.line.content

    # do for left: is array -> name, is function -> params else var name
    left_names = []
    left_indexes = []
    left_array = left_operand.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
    left_function = left_operand.find_first(TOKEN_TYPE.FUNCTION_CALL)
    if left_array:
      left_names = [left_array.meta[TOKEN_TYPE.ARRAY_NAME]]
      left_indexes = [left_array.meta[TOKEN_TYPE.ARRAY_INDEX]]
    elif left_function:
      left_params = left_function.find_first(TOKEN_TYPE.FUNCTION_PARAMETERS)
      if left_params:
        for left_param in left_params.children:
          left_param_array = left_param.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
          if left_param_array:
            left_names.append(left_param_array.meta[TOKEN_TYPE.ARRAY_NAME])
            left_indexes.append(left_param_array.meta[TOKEN_TYPE.ARRAY_INDEX])
          else:
            left_param_var = left_param.find_first(TOKEN_TYPE.VARIABLE_NAME)
            if left_param_var:
              left_names.append(left_param_var.line.content)
    else:
      left_var = left_operand.find_first(TOKEN_TYPE.VARIABLE_NAME)
      left_names.append(left_var.line.content)


    right_names = []
    right_indexes = []
    right_array = right_operand.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
    right_function = right_operand.find_first(TOKEN_TYPE.FUNCTION_CALL)
    if right_array:
      right_names = [right_array.meta[TOKEN_TYPE.ARRAY_NAME]]
      right_indexes = [right_array.meta[TOKEN_TYPE.ARRAY_INDEX]]
    elif right_function:
      right_params = right_function.find_first(TOKEN_TYPE.FUNCTION_PARAMETERS)
      if right_params:
        for right_param in right_params.children:
          right_param_array = right_param.find_first(TOKEN_TYPE.ARRAY_ELEMENT)
          if right_param_array:
            right_names.append(right_param_array.meta[TOKEN_TYPE.ARRAY_NAME])
            right_indexes.append(right_param_array.meta[TOKEN_TYPE.ARRAY_INDEX])
          else:
            right_param_var = right_param.find_first(TOKEN_TYPE.VARIABLE_NAME)
            if right_param_var:
              right_names.append(right_param_var.line.content)
    else:
      right_var = right_operand.find_first(TOKEN_TYPE.VARIABLE_NAME)
      right_names.append(right_var.line.content)
      
    if target_name in left_names or target_name in right_names:
      return False
    for ri in right_indexes:
      if pattern.is_array_index_contains_another(ri, target_name):
        return False
    for li in left_indexes:
      if pattern.is_array_index_contains_another(li, target_name):
        return False
    return True