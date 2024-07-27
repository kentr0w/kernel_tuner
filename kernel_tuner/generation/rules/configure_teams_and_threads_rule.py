from kernel_tuner.generation.rules.rule import RuleABC
from kernel_tuner.generation.tree.tree import Tree
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.token.pragma_token import PRAGMA_TOKEN_TYPE, PRAGMA_KEYWORDS, build_pragma_token
from kernel_tuner.generation.code.line import Line
from kernel_tuner.util import write_file
from kernel_tuner.generation.utils.util import *

class TeamsAandThreadsConfigurationRule(RuleABC):

  def __init__(self, tree: Tree, context: Context, initial_params: dict):
    super().__init__(tree, context, initial_params)
    self.rule_id = 'teams_and_threads_limit'

  def run(self, debug_file=None):
    team_pragmas = filter_pragmas_by_type(self.tree.pragma_tokens, PRAGMA_TOKEN_TYPE.TEAMS)
    team_pragmas = filter_pragmas_contains_keyword(team_pragmas, [PRAGMA_KEYWORDS.TEAMS], [PRAGMA_KEYWORDS.NUM_TEAMS])
    for pragma in team_pragmas:
      new_params = {PRAGMA_KEYWORDS.NUM_TEAMS: self.generate_param(PRAGMA_KEYWORDS.NUM_TEAMS)}
      if PRAGMA_KEYWORDS.THREAD_LIMIT in pragma.keywords:
        pragma.modify_keywords(
          [PRAGMA_KEYWORDS.NUM_TEAMS],
          new_params
        )
      elif PRAGMA_KEYWORDS.NUM_THREADS not in pragma.keywords:
        new_params[PRAGMA_KEYWORDS.THREAD_LIMIT] = self.generate_param(PRAGMA_KEYWORDS.THREAD_LIMIT)
        pragma.modify_keywords(
          [PRAGMA_KEYWORDS.NUM_TEAMS, PRAGMA_KEYWORDS.THREAD_LIMIT],
          new_params
        )
      self.context.offer_with_new_token([pragma], [pragma], self.rule_id)

    
    pragmas = filter_pragmas_contains_keyword(self.tree.pragma_tokens, [PRAGMA_KEYWORDS.PARALLEL], [PRAGMA_KEYWORDS.TEAMS, PRAGMA_KEYWORDS.NUM_THREADS])
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
      is_correct = False
      if for_child.type in [TOKEN_TYPE.LONG_VARIABLE_REASSIGNMENT, TOKEN_TYPE.FUNCTION_VARIABLE_REASSIGNMENT, TOKEN_TYPE.SHORT_VARIABLE_REASSIGNMENT, TOKEN_TYPE.VARIABLE_REASSIGNMENT]:
        is_correct = self.__check_reassignmnet(for_token)
      elif for_child.type == TOKEN_TYPE.FOR:
        is_correct = self.__handle_inner_for(pragma, for_token, is_target_used)
      
      if is_correct:
        new_params = {PRAGMA_KEYWORDS.NUM_TEAMS: self.generate_param(PRAGMA_KEYWORDS.NUM_TEAMS)}
        new_params[PRAGMA_KEYWORDS.THREAD_LIMIT] = self.generate_param(PRAGMA_KEYWORDS.THREAD_LIMIT)
        pragma.modify_keywords([], {}, [], False)
        new_token = build_pragma_token(
          type = PRAGMA_TOKEN_TYPE.TEAMS,
          keywords = [PRAGMA_KEYWORDS.NUM_TEAMS, PRAGMA_KEYWORDS.THREAD_LIMIT],
          line_number = pragma.line.line_number,
          meta = new_params,
          is_target_used = True
        )
        self.tree.append_node(pragma.parent, pragma, new_token)
        new_token.update_content()

        self.context.offer_with_new_token_content(pragma, new_token, self.rule_id)

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
    return tmp_for_child and tmp_for_child.type in [TOKEN_TYPE.LONG_VARIABLE_REASSIGNMENT, TOKEN_TYPE.FUNCTION_VARIABLE_REASSIGNMENT, TOKEN_TYPE.SHORT_VARIABLE_REASSIGNMENT, TOKEN_TYPE.VARIABLE_REASSIGNMENT] and self.__check_reassignmnet(tmp_for_token)

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

  def generate_param(self, pragma_keyword: PRAGMA_KEYWORDS) -> str:
    match pragma_keyword:
      case PRAGMA_KEYWORDS.NUM_TEAMS:
        return self.context.get_tune_param_unique_name(
          rule_id = self.rule_id,
          pragma_keyword = pragma_keyword,
          values =  ['128', '256'],
          name_prefix = 'teams_number'
        )
      case PRAGMA_KEYWORDS.THREAD_LIMIT:
        return self.context.get_tune_param_unique_name(
          rule_id = self.rule_id,
          pragma_keyword = pragma_keyword,
          values =  ['528', '1024'],
          name_prefix = 'nthread_limit'
        )
      case _:
        raise Exception("Unknown  type for this rule!")