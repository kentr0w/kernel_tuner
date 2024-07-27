import re
from kernel_tuner.generation.token.token import PRAGMA_KEYWORDS_VALUES, TOKEN_TYPE

#==============================Code Token==============================

#==============FOR==============
for_initiailise_pattern_with_type = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^,;]+)')
for_initiailise_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^,;]+)')
for_pattern = re.compile(r'for\s*\(\s*(.*?)\s*;\s*(.*?)\s*;\s*(.*?)\s*\)')
for_condition_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(<|>|<=|>=|==|!=)\s*([a-zA-Z_][a-zA-Z0-9_]*|\d+(\.\d+)?)')
for_operation_pattern = re.compile(r'(\+\+|--)?([a-zA-Z_][a-zA-Z0-9_]*)(\+\+|--)?')


#==============ASSIGNMENT==============
variable_initialisation_pattern = re.compile(r'^\b(?:int|float|double|char|long|short)\s+[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^;]*;')
variable_reassignment_pattern = re.compile(
    r'^(?!\s*(?:int|float|double|char|long|short)\s)'  # Exclude type declarations
    r'(?P<target>[a-zA-Z_][a-zA-Z0-9_\[\]]*\s*(?:\[[^\]]*\])?)\s*'  # Match variable or array element
    r'=\s*'  # Match the assignment operator
    r'(?P<value>[a-zA-Z_][a-zA-Z0-9_\[\]]*|\d+)\s*;'  # Match a single variable or number
)
long_reassignment_pattern = re.compile(
    r'^(?!\s*(?:int|float|double|char|long|short)\s)'  # Ensure it doesn't start with a type declaration
    r'(?P<target>[a-zA-Z_][a-zA-Z0-9_\[\]]*\s*(?:\[[^\]]*\])?)\s*'  # Match the left operand (variable or array element)
    r'(?P<operation>=|\+=|-=|\*=|/=|%=|&=|\|=|\^=)\s*'  # Match the assignment operator or compound assignment operator
    r'(?P<expression>'  # Begin capturing the right operand expression
    r'(?:[a-zA-Z_][a-zA-Z0-9_\[\]]*\s*(?:\[[^\]]*\])?|[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)|\d+)'  # Match variable, array element, function call, or number
    r'(?:\s*[\+\-\*\/%&\|^]\s*'  # Match an operator
    r'(?:[a-zA-Z_][a-zA-Z0-9_\[\]]*\s*(?:\[[^\]]*\])?|[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)|\d+))*'  # Match multiple operands
    r')\s*;'  # Match the semicolon at the end
)
short_reassignment_pattern = re.compile(r'^(?!\s*(?:int|float|double|char|long|short)\s)\b[a-zA-Z_][a-zA-Z0-9_\[\]]*\s*(?:[+\-*/%&|^]=|&&=|\|\|=|=)\s*[^;]*;')
function_reassignment_pattern = re.compile(r'^(?!\s*(?:int|float|double|char|long|short)\s)\b[a-zA-Z_][a-zA-Z0-9_\[\]]*\s*=\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\([^;]*\);')

right_part_long_reassignment_pattern = re.compile(
    r'^(?P<left_operand>'  # Start capturing left operand
    r'(?:[a-zA-Z_][a-zA-Z0-9_\[\]]*\s*(?:\[[^\]]*\])?)|'  # Match variable or array element
    r'(?:\d+)|'  # Match number
    r'(?:[a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\))'  # Match function call
    r'\s*(?P<operation>\+|\-|\*|\/|%|&|\||\^|&&|\|\|)\s*'  # Match operation
    r'(?P<right_operand>'  # Start capturing right operand
    r'(?:[a-zA-Z_][a-zA-Z0-9_\[\]]*\s*(?:\[[^\]]*\])?)|'  # Match variable or array element
    r'(?:\d+)|'  # Match number
    r'(?:[a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\))'  # Match function call
    r'\s*;$'  # Match the semicolon at the end
)
right_part_short_reassignment_pattern = re.compile(r'(?P<target>[a-zA-Z_][a-zA-Z0-9_\[\]]*)\s*(?P<operation>[+\-*&|^]=|&&=|\|\|=)\s*(?P<right_operand>[^;]+);')
right_part_function_reassignment_pattern = re.compile(r'(?P<target>[a-zA-Z_][a-zA-Z0-9_\[\]]*)\s*=\s*(?P<function_name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\((?P<parameters>[^;]*)\);')

#==============FUNCTION==============
function_call_pattern = re.compile(r'^\b[a-zA-Z_][a-zA-Z0-9_]*\s*\([^;{}]*\)\s*;?\s*$', re.DOTALL | re.MULTILINE)
function_start_call_patter = re.compile(r'^\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*$')
function_call_parameters_pattern = re.compile(r'(?P<function_name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\((?P<parameters>[^;]*)\);')



#==============================PRAGMA==============================
directive_with_parentheses_pattern = re.compile(r'({})\(.*\)'.format('|'.join(PRAGMA_KEYWORDS_VALUES)))
directive_exact_pattern = re.compile(r'({})'.format('|'.join(PRAGMA_KEYWORDS_VALUES)))


token_types = {
  'int': TOKEN_TYPE.TYPE_INT
}

operation_types = {
    '+': TOKEN_TYPE.OPERATION_SUM,
    '-': TOKEN_TYPE.OPERATION_MINUS,
    '*': TOKEN_TYPE.OPERATION_MUTLIPLICATION,
    '&': TOKEN_TYPE.OPERATION_AND,
    '|': TOKEN_TYPE.OPERATION_OR,
    '&&': TOKEN_TYPE.OPERATION_AND_AND,
    '||': TOKEN_TYPE.OPERATION_OR_OR,
    '^': TOKEN_TYPE.OPERATION_XOR,
}

def is_array_index_contains_another(array_index: str, array_prefix: str) -> bool:
  if not array_index or not array_prefix:
    return False
  return re.search(fr'\[[^\]]*{array_prefix}[^\]]*\]', array_index) is not None