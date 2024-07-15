from kernel_tuner.generation.rules.rule import RuleABC
from kernel_tuner.generation.tree.tree import Tree
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.token.pragma_token import PRAGMA_TOKEN_TYPE, PRAGMA_KEYWORDS, build_pragma_token
from kernel_tuner.generation.code.line import Line
from kernel_tuner.util import write_file
from kernel_tuner.generation.utils.util import *

class AddNumTeamsAndThreadLimitRule(RuleABC):

  def __init__(self, tree: Tree, context: Context, initial_params: dict):
    super().__init__(tree, context, initial_params)

  def run(self, debug_file=None):
    team_pragmas = filter_pragmas_by_type(self.tree.pragma_tokens, PRAGMA_TOKEN_TYPE.TEAMS)
    team_pragmas = filter_pragmas_contains_keyword(team_pragmas, [PRAGMA_KEYWORDS.TEAMS], [PRAGMA_KEYWORDS.NUM_TEAMS, PRAGMA_KEYWORDS.NUM_THREADS])
    # team_pragmas = list(filter(lambda x: PRAGMA_KEYWORDS.NUM_TEAMS not in x.keywords, team_pragmas))
    new_params = self.generate_param()
    for pragma in team_pragmas:
      pragma_tune_params = {x[0]:x[1] for x in new_params}
      if PRAGMA_KEYWORDS.THREAD_LIMIT in pragma.keywords:
        pragma.modify_keywords(
          [PRAGMA_KEYWORDS.NUM_TEAMS],
          pragma_tune_params
        )
      else:
        new_params += self.get_thread_param()
        pragma_tune_params.update({x[0]:x[1] for x in new_params})
        pragma.modify_keywords(
          [PRAGMA_KEYWORDS.NUM_TEAMS, PRAGMA_KEYWORDS.THREAD_LIMIT],
          pragma_tune_params
        )
      self.context.offer_with_new_token([pragma], [pragma], self.rule_id, new_params)
      

  def generate_param(self) -> PragmaTuneParams:
    team_numbers = self.context.get_tune_param_unique_name('teams_number')
    return self.initial_params + [
      (PRAGMA_KEYWORDS.NUM_TEAMS, team_numbers, ['128', '256']),
      
    ]
  
  def get_thread_param(self) -> PragmaTuneParams:
    thread_limit = self.context.get_tune_param_unique_name('nthread_limit')
    return [(PRAGMA_KEYWORDS.THREAD_LIMIT, thread_limit, ['528', '1024'])]