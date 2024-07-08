import re
from kernel_tuner.generation.token.token import PRAGMA_KEYWORDS_VALUES

#==============================Code Token==============================
for_initiailise_pattern_with_type = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^,;]+)')
for_initiailise_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^,;]+)')
for_pattern = re.compile(r'for\s*\(\s*(.*?)\s*;\s*(.*?)\s*;\s*(.*?)\s*\)')
for_condition_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(<|>|<=|>=|==|!=)\s*([a-zA-Z_][a-zA-Z0-9_]*|\d+(\.\d+)?)')
for_operation_pattern = re.compile(r'(\+\+|--)?([a-zA-Z_][a-zA-Z0-9_]*)(\+\+|--)?')

#==============================PRAGMA==============================
pattern_with_parentheses = re.compile(r'({})\(.*\)'.format('|'.join(PRAGMA_KEYWORDS_VALUES)))
pattern_exact = re.compile(r'({})'.format('|'.join(PRAGMA_KEYWORDS_VALUES)))