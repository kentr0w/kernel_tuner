from __future__ import annotations
from kernel_tuner.generation.token.token import *
from kernel_tuner.generation.code.code import Code, CodeBlock
import kernel_tuner.generation.utils.patterns as pattern

class CodeToken(Token):

  def __init__(self, line: Line, content: CodeBlock, type: TOKEN_TYPE) -> None:
    super().__init__(line, content, type)
    self.__detect_children()
    self.meta = self.__detect_meta()

  @staticmethod
  def build_code_token(line: Line, initial_code_block: CodeBlock) -> CodeToken | None:
    if line.startswith('{'):
      return build_block_code_token(line, initial_code_block)
    elif line.startswith('for'):
      return build_for_code_token(line, initial_code_block)
    elif line.startswith('if'):
      return build_if_code_token(line, initial_code_block)
    else:
      return build_function_code_token(line, initial_code_block)
  
  # create additional tokens for 'FOR' specifi (py)
  def __detect_meta(self) -> dict[TOKEN_TYPE, str]:
    meta = {}
    if self.type == TOKEN_TYPE.FOR_INITIALISATION:      
      match = pattern.for_initiailise_pattern_with_type.search(self.line.content)
      if match:
          meta[TOKEN_TYPE.TYPE] = match.group(1).strip().strip()
          meta[TOKEN_TYPE.VARIABLE_NAME] = match.group(2).strip()
      else:
        match = pattern.for_initiailise_pattern.search(self.line.content)
        if match:
            meta[TOKEN_TYPE.VARIABLE_NAME] = match.group(1).strip()
    # elif self.type == TOKEN_TYPE.FOR_CONDITION:
    #   match = for_condition_pattern.search(self.line.content)
    #   if match:
    #       meta[TOKEN_TYPE.LEFT_OPERAND] = match.group(1).strip()
    #       meta[TOKEN_TYPE.OPERATION] = match.group(2).strip()
    #       meta[TOKEN_TYPE.RIGHT_OPERAND] = match.group(3).strip()
    elif self.type == TOKEN_TYPE.FOR_OPERATION:
      match = pattern.for_operation_pattern.search(self.line.content)
      if match:
          meta[TOKEN_TYPE.VARIABLE_NAME] = match.group(2).strip()
          if match.group(1):
            if match.group(1).strip() == '++':
              meta[TOKEN_TYPE.PRE_INCREMENT] = match.group(1).strip()
            elif match.group(1).strip() == '--':
              meta[TOKEN_TYPE.PRE_DECREMENT] = match.group(1).strip()
          if match.group(3):
            if match.group(3).strip() == '++':
              meta[TOKEN_TYPE.POST_INCREMENT] = match.group(3).strip()
            elif match.group(3).strip() == '--':
              meta[TOKEN_TYPE.POST_DECREMENT] = match.group(3).strip()
    elif self.type == TOKEN_TYPE.ARRAY_ELEMENT:
      array_content = self.line.content.split('[')
      meta[TOKEN_TYPE.ARRAY_NAME] = array_content[0].strip()
      index = array_content[1].split(']')[0].strip()
      meta[TOKEN_TYPE.ARRAY_INDEX] = index
    return meta

  def __detect_children(self):
    idx = 1
    rest_possible_types = [
      build_function_code_token,
      build_variable_initialisation,
      build_variable_reassignment
    ]

    # Detect 0 line itself
    if self.type == TOKEN_TYPE.FOR:
      code_token = build_for_body(self.line, self.content)
      if code_token:
        self.append_child(code_token)
    elif self.type == TOKEN_TYPE.FOR_BODY:
      code_tokens = build_for_body_content(self.line, self.content)
      for code_token in code_tokens:
        self.append_child(code_token)
    elif self.type == TOKEN_TYPE.LONG_VARIABLE_REASSIGNMENT:
      code_tokens = build_long_varialbe_reassignment_content(self.line, self.content)
      for code_token in code_tokens:
        self.append_child(code_token)
    elif self.type == TOKEN_TYPE.SHORT_VARIABLE_REASSIGNMENT:
      code_tokens = build_short_varialbe_reassignment_content(self.line, self.content)
      for code_token in code_tokens:
        self.append_child(code_token)
    elif self.type in [TOKEN_TYPE.TARGET, TOKEN_TYPE.LEFT_OPERAND, TOKEN_TYPE.RIGHT_OPERAND]:
      if '[' and ']' in self.line.content:
        self.append_child(CodeToken(self.line, self.content, TOKEN_TYPE.ARRAY_ELEMENT))
      else:
        self.append_child(CodeToken(self.line, self.content, TOKEN_TYPE.VARIABLE_NAME))
    

    # Detect start from 1 line
    while idx < self.content.size():

      code_token = None
      next_line = self.content.get(idx)
      if not next_line:
        return

      if next_line.startswith('{'):

        if self.type == TOKEN_TYPE.FOR or self.type == TOKEN_TYPE.IF:
          idx+=1
          continue

        code_token = build_block_code_token(next_line, CodeBlock(self.content.lines[idx:]))

      elif next_line.startswith('for'):
        code_token = build_for_code_token(next_line, CodeBlock(self.content.lines[idx:]))

      elif next_line.startswith('}'):
        idx+=1
        continue

      elif next_line.startswith('if'):
        code_token = build_if_code_token(next_line, CodeBlock(self.content.lines[idx:]))

      else:
        for f in rest_possible_types:
          code_token = f(next_line, CodeBlock(self.content.lines[idx:]))
          if code_token:
            break

      if code_token:
        self.append_child(code_token)
        idx+=len(code_token.content.lines)
      else:
        return
  
  def print(self, debug=False) -> str:
    result = f"id: {self.id}\n"
    result += f"type: {self.type}\n"
    result += f"line_start: {self.line.content}\n"
    result += f"meta: {self.meta}\n"
    result += f"children: {list(map(lambda x: x.id, self.children))}\n"

    if debug:
      result += f"content: \n {self.print_content()}\n"
    return result

def build_block_code_token(statrt_line: Line, initial_code: CodeBlock) -> CodeToken|None:
  node_content = []
  open_braces_count = 0
  idx = 0
  line = statrt_line
  while(True):          
    node_content.append(line)
    if line.is_open_brace():
      open_braces_count+=1
    elif line.is_close_brace():
      open_braces_count-=1
    idx+=1          
    if open_braces_count == 0:
      break
    line = initial_code.get(idx)
    if not line:
      return None
  return CodeToken(statrt_line, CodeBlock(node_content), TOKEN_TYPE.BLOCK)



def build_for_code_token(start_line: Line, initial_code: CodeBlock) -> CodeToken|None:
  node_content = []
  open_braces_count = 0
  idx = 0
  line = start_line
  while True:
    node_content.append(line)
    if line.is_open_brace():
      open_braces_count+=1
    if len(node_content) == 1 and not line.is_open_brace():
      idx+=1
      next_line = initial_code.get(idx)
      if not next_line:
        return None
      if next_line.is_open_brace():
        open_braces_count+=1
        node_content.append(next_line)
      else:
        return build_one_line_for_code_token(start_line, next_line)
    elif line.is_close_brace():
      open_braces_count-=1
    idx+=1
    if open_braces_count == 0:
      break
    line = initial_code.get(idx)
    if not line:
      print("TODO NOT LINE")
      break
  return CodeToken(start_line, CodeBlock(node_content), TOKEN_TYPE.FOR)


def build_one_line_for_code_token(current_line: Line, next_line: Line) -> CodeToken|None:
  open_parenthesis_count = 1
  start_index = current_line.find('(')
  last_paranthesis_idx = start_index    
  if not start_index:
    return None
  for idx, char in enumerate(current_line.content[start_index+1:]):
    if open_parenthesis_count == 0:
      break
    if char == '(':
      open_parenthesis_count+=1
    elif char == ')':
      open_parenthesis_count-=1
      last_paranthesis_idx=idx

  if (last_paranthesis_idx + start_index + 1) == current_line.len() - 1:
    return CodeToken(current_line, CodeBlock([current_line, next_line]), TOKEN_TYPE.FOR)
  return CodeToken(current_line, CodeBlock([current_line]), TOKEN_TYPE.FOR)



def build_function_code_token(start_line: Line, initial_code: CodeBlock):
  idx = 0
  line = start_line
  node_content = []
  # function_call_pattern = r'^\b[a-zA-Z_][a-zA-Z0-9_]*\s*\([^;{}]*\)\s*;?\s*$'
  # function_start_call_patter = r'^\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*$'
  while True:
    node_content.append(line)
    content_as_string = '\n'.join(list(map(lambda x: x.content, node_content)))
    match = pattern.function_call_pattern.search(content_as_string)
    if not match:
      if len(node_content) == 1:
        match = pattern.function_start_call_patter.search(line.content)
        if not match:
          return None
      idx+=1
      line = initial_code.get(idx)
      if not line:
        print("TODO: NOT LINE!")
        return None
      continue
    # check only one function is called!
    # if idx_line != line.len()-1:
    #   return None
    break
  return CodeToken(start_line, CodeBlock(node_content), TOKEN_TYPE.FUNCTION_CALL)


def build_if_code_token(start_line: Line, initial_code: CodeBlock) -> CodeToken|None:
  node_content = []
  open_braces_count = 0
  idx = 0
  line = start_line
  while(True):
    node_content.append(line)
    if line.is_open_brace():
      open_braces_count+=1
    if line.is_close_brace():
      open_braces_count-=1
    if len(node_content) == 1 and not line.is_open_brace():
      idx+=1
      next_next_line = initial_code.get(idx)
      if not next_next_line:
        return None # for now we don't support if(a) foo()s
      if next_next_line.is_open_brace():
        open_braces_count+=1
        node_content.append(next_next_line)
      else:
        return build_one_line_if_code_block(start_line, initial_code)
    if open_braces_count == 0:
      idx+=1
      next_next_line = initial_code.get(idx)
      if not next_next_line or not next_next_line.content.startswith('else'):
        break
      node_content.append(next_next_line)
    idx+=1
    line = initial_code.get(idx)
    if not line:
      print("TODO NOT LINE")
      break
  return CodeToken(start_line, CodeBlock(node_content), TOKEN_TYPE.IF)


def build_one_line_if_code_block(start_line: Line, initial_code: CodeBlock) -> CodeToken|None:
  """
    if(a) foo()
    For now - we can avoid this. Think about it in a future!
  """
  node_content = []
  line = start_line
  node_content.append(line)
  idx = 1
  next_line = initial_code.get(idx)
  if not next_line:
    print("IF NONE ONE LINE TODO")
    return None
  node_content.append(next_line)
  idx+=1
  else_line = initial_code.get(idx)
  if else_line and else_line.startswith('else'):
    node_content.append(else_line)
    idx+=1
    else_next_line = initial_code.get(idx)
    if not else_next_line:
      print("ELSE ONT LINE NONE TODO!")
      return None
    node_content.append(else_next_line)
  currentToken = CodeToken(start_line, CodeBlock(node_content), TOKEN_TYPE.IF)
  return currentToken

# We don't need it -> use only pragma childrend
# 
# def build_variable_declaration(start_line: Line, initial_code: CodeBlock) -> CodeToken|None:
#   pattern = r'^\b(?:int|float|double|char|long|short)\s+[a-zA-Z_][a-zA-Z0-9_]*\s*;'
#   match = re.search(pattern, start_line.content)
#   if match:
#     return CodeToken(start_line, CodeBlock([start_line]), TOKEN_TYPE.VARIABLE_DECLARATION)
#   return None


def build_variable_initialisation(start_line: Line, initial_code: CodeBlock) -> CodeToken|None:
  match = pattern.variable_initialisation_pattern.search(start_line.content)
  if match:
    return CodeToken(start_line, CodeBlock([start_line]), TOKEN_TYPE.VARIABLE_ASSIGNMENT)
  return None


def build_variable_reassignment(start_line: Line, initial_code: CodeBlock) -> CodeToken|None:
  match = pattern.long_reassignment_pattern.search(start_line.content)
  if match:
    type = TOKEN_TYPE.LONG_VARIABLE_REASSIGNMENT
  else:
    match = pattern.short_reassignment_pattern.search(start_line.content)
    if match:
      type = TOKEN_TYPE.SHORT_VARIABLE_REASSIGNMENT
  if type:
    return CodeToken(start_line, CodeBlock([start_line]), type)
  return None


def build_for_body(start_line: Line, initial_code: CodeBlock) -> CodeToken|None:
  return CodeToken(start_line, CodeBlock([start_line]), TOKEN_TYPE.FOR_BODY)


def build_for_body_content(start_line: Line, initial_code: CodeBlock) -> list[CodeToken]:
  for_parts = pattern.for_pattern.search(start_line.content)
  if not for_parts:
    return []
  for_parts = for_parts.groups()
  if len(for_parts) != 3:
    return []
  for_body_sub_tokens = []
  for_body_types = [TOKEN_TYPE.FOR_INITIALISATION, TOKEN_TYPE.FOR_CONDITION, TOKEN_TYPE.FOR_OPERATION]
  for idx, part in enumerate(for_parts):
    if part != '':
      for_body_sub_tokens.append(
        CodeToken(
          Line(part, start_line.line_number),
          CodeBlock([start_line]),
          for_body_types[idx]
        )
      )
  return for_body_sub_tokens


def build_long_varialbe_reassignment_content(start_line: Line, initial_code: CodeBlock) -> list[CodeToken]:
  split_line = start_line.content.split('=')
  if len(split_line) != 2:
    return []
  result = []
  target = split_line[0].strip()
  #if '[' and ']' in target:
  result.append(CodeToken(Line(target, start_line.line_number), CodeBlock([start_line]), TOKEN_TYPE.TARGET))
  # else:
  #   result.append(CodeToken(Line(target, start_line.line_number), CodeBlock([start_line]), TOKEN_TYPE.TARGET_VARIABLE))
  # analyse right part of =
  right_part = split_line[1].strip()
  match = pattern.right_part_long_reassignment_pattern.fullmatch(right_part)
  if match:
      left_operand = match.group('left_operand')
      if left_operand:
        result.append(CodeToken(Line(left_operand, start_line.line_number), CodeBlock([start_line]), TOKEN_TYPE.LEFT_OPERAND))
      operation = match.group('operation')
      if operation:
        if operation in pattern.operation_types:
          result.append(CodeToken(Line(operation, start_line.line_number), CodeBlock([start_line]), pattern.operation_types[operation]))
      right_operand = match.group('right_operand')
      if right_operand:
        result.append(CodeToken(Line(right_operand, start_line.line_number), CodeBlock([start_line]), TOKEN_TYPE.RIGHT_OPERAND))
  return result


def build_short_varialbe_reassignment_content(start_line: Line, initial_code: CodeBlock) -> list[CodeToken]:
  result = []
  match = pattern.right_part_short_reassignment_pattern.fullmatch(start_line.content)
  if match:
    target = match.group('target')
    # if '[' and ']' in target:
    result.append(CodeToken(Line(target, start_line.line_number), CodeBlock([start_line]), TOKEN_TYPE.TARGET))
    # else:
    #   result.append(CodeToken(Line(target, start_line.line_number), CodeBlock([start_line]), TOKEN_TYPE.TARGET_VARIABLE))
    operation = match.group('operation')
    if operation:
      operation = operation.replace('=', '')
      if operation in pattern.operation_types:
        result.append(CodeToken(Line(operation, start_line.line_number), CodeBlock([start_line]), pattern.operation_types[operation]))
    right_operand = match.group('right_operand')
    if right_operand:
      result.append(CodeToken(Line(right_operand, start_line.line_number), CodeBlock([start_line]), TOKEN_TYPE.RIGHT_OPERAND))
  return result