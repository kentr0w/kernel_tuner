from kernel_tuner.generation.rules.rule import RuleABC
from kernel_tuner.generation.tree.tree import Tree
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.token.pragma_token import PRAGMA_TOKEN_TYPE, PRAGMA_KEYWORDS, build_pragma_token
from kernel_tuner.generation.code.line import Line
from kernel_tuner.util import write_file
from kernel_tuner.generation.utils.util import *


"""
+) Check no teams and distribute is used before
+) Add target if no target before (upper)
+) If there is inner loop -> add parallel after the firest one
+) No Sequential Dependencies: go inside in for loop
"""
class TeamsAndDistributionConfigurationRule(RuleABC):

  def __init__(self, tree: Tree, context: Context, initial_params: PragmaTuneParams):
    super().__init__(tree, context, initial_params)
    self.rule_id = 'teams_and_distribute'

  def run(self, debug_file=None):
    pragmas = filter_pragmas_contains_keyword(self.tree.pragma_tokens, [PRAGMA_KEYWORDS.PARALLEL], [PRAGMA_KEYWORDS.TEAMS, PRAGMA_KEYWORDS.DISTRIBUTE])    
    pragmas = filter_pragmas_contains_child(pragmas, TOKEN_TYPE.FOR)
    pragmas = list(filter(lambda x: len(x.children) == 1, pragmas))
    
    for pragma in pragmas:
      parents = pragma.parents()
      is_target_used = len(filter_pragmas_by_type(parents, PRAGMA_TOKEN_TYPE.TARGET)) > 0
      if len(filter_pragmas_by_type(parents, PRAGMA_TOKEN_TYPE.TEAMS)) > 0:
        continue
      if len(filter_pragmas_by_type(parents, PRAGMA_TOKEN_TYPE.PARALLEL, False)) > 0:
        continue
      if len(filter_pragmas_by_type(parents, PRAGMA_TOKEN_TYPE.PARALLEL)) > 0:
        continue
      if len(filter_pragmas_by_type(parents, PRAGMA_TOKEN_TYPE.DISTRIBUTE)) > 0:
        continue
      for_token = pragma.find_first(TOKEN_TYPE.FOR)
      if not for_token:
        continue
      for_child = get_for_child(for_token)
      if for_child.type in [TOKEN_TYPE.LONG_VARIABLE_REASSIGNMENT, TOKEN_TYPE.FUNCTION_VARIABLE_REASSIGNMENT, TOKEN_TYPE.SHORT_VARIABLE_REASSIGNMENT, TOKEN_TYPE.VARIABLE_REASSIGNMENT]:        
        self.__handle_one_for(pragma, for_token, is_target_used)
      elif for_child.type == TOKEN_TYPE.FOR:
        self.__handle_inner_for(pragma, for_token, is_target_used)
      
    
  def generate_param(self) -> str:
    return self.context.get_tune_param_unique_name(
      rule_id = self.rule_id,
      pragma_keyword = PRAGMA_KEYWORDS.NUM_TEAMS,
      values = ['1', '2'],
      name_prefix = 'nteams'
    )

  def __handle_one_for(self, pragma: PragmaToken, for_token: Token, is_target_used: bool):
    if self.__check_reassignmnet(for_token):
      new_meta = {PRAGMA_KEYWORDS.NUM_TEAMS: self.generate_param()}
      new_meta.update(pragma.meta)
      new_node = build_pragma_token(
        type = PRAGMA_TOKEN_TYPE.TEAMS,
        keywords = [PRAGMA_KEYWORDS.DISTRIBUTE, PRAGMA_KEYWORDS.NUM_TEAMS] + pragma.keywords,
        line_number = pragma.line.line_number,
        meta = new_meta,
        is_target_used = not is_target_used
      )
      self.context.offer_with_new_token([pragma], [new_node], self.rule_id)

  def __handle_inner_for(self, pragma: PragmaToken, outer_for: Token, is_target_used: bool):
    tmp_for_token = outer_for
    while(True):
      sub_for_child = get_for_child(tmp_for_token)
      if sub_for_child and sub_for_child.type == TOKEN_TYPE.FOR:
        tmp_for_token = sub_for_child
      else:
        break
    
    tmp_for_child = get_for_child(tmp_for_token)
    if tmp_for_child and tmp_for_child.type in [TOKEN_TYPE.LONG_VARIABLE_REASSIGNMENT, TOKEN_TYPE.FUNCTION_VARIABLE_REASSIGNMENT, TOKEN_TYPE.SHORT_VARIABLE_REASSIGNMENT, TOKEN_TYPE.VARIABLE_REASSIGNMENT]:
      if self.__check_reassignmnet(tmp_for_token):
        one_level_for = get_for_child(outer_for)

        new_parallel_node = build_pragma_token(
          type = PRAGMA_TOKEN_TYPE.PARALLEL,
          keywords = [PRAGMA_KEYWORDS.FOR],
          line_number = one_level_for.line.line_number,
          meta = {},
          is_target_used = False
        )
        self.tree.append_node(outer_for, one_level_for, new_parallel_node)
        
        # TODO make better!
        outer_for.content = CodeBlock([outer_for.line, Line('{\n', 999)] + new_parallel_node.content.lines + [Line('}\n', 999)])

        new_meta = {PRAGMA_KEYWORDS.NUM_TEAMS: self.generate_param()}
        new_node = build_pragma_token(
          type = PRAGMA_TOKEN_TYPE.TEAMS,
          keywords = [PRAGMA_KEYWORDS.DISTRIBUTE, PRAGMA_KEYWORDS.NUM_TEAMS],
          line_number = pragma.line.line_number,
          meta = new_meta,
          is_target_used = not is_target_used
        )

        new_node.append_child(outer_for)
        self.tree.replace_node(pragma, new_node)

        self.context.offer_with_new_token_content(pragma, new_node, self.rule_id)


  def __check_reassignmnet(self, assignment_token: Token):
    is_correct = False
    varialbe_reassignment = assignment_token.find_first(TOKEN_TYPE.VARIABLE_REASSIGNMENT)
    if varialbe_reassignment:
      is_correct = is_variable_reassignment_is_correct(varialbe_reassignment)
    else:
      varialbe_reassignment = assignment_token.find_first(TOKEN_TYPE.LONG_VARIABLE_REASSIGNMENT)
      if varialbe_reassignment:
        is_correct = is_long_variable_reassignment_is_correct(varialbe_reassignment)
      else:
        varialbe_reassignment = assignment_token.find_first(TOKEN_TYPE.FUNCTION_VARIABLE_REASSIGNMENT)
        if varialbe_reassignment:        
          is_correct = is_function_variable_reassignment_is_correct(varialbe_reassignment)
    return is_correct

