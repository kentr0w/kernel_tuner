from kernel_tuner.generation.rules.rule import RuleABC
from kernel_tuner.generation.tree.tree import Tree
from kernel_tuner.generation.code.context import Context
from kernel_tuner.generation.token.pragma_token import PRAGMA_TOKEN_TYPE, PRAGMA_KEYWORDS, build_pragma_token
from kernel_tuner.generation.token.token import TOKEN_TYPE
from kernel_tuner.generation.code.line import Line
from kernel_tuner.util import write_file
import kernel_tuner.generation.utils.util as util
from kernel_tuner.generation.utils.patterns import operation_types


class AddReductionClauseRule(RuleABC):

  def __init__(self, tree: Tree, context: Context, initial_params: util.PragmaTuneParams):
    super().__init__(tree, context, initial_params)
    self.rule_id = 'reduction'

  def run(self, debug_file=None):
    print("hey!")
    pragmas = util.filter_pragmas_contains_keyword(self.tree.pragma_tokens, [PRAGMA_KEYWORDS.PARALLEL, PRAGMA_KEYWORDS.FOR], [PRAGMA_KEYWORDS.REDUCTION])
    pragmas_with_for_as_child = util.filter_pragmas_contains_child(pragmas, TOKEN_TYPE.FOR)
    for pragma_with_for_as_child in pragmas_with_for_as_child:
      for_token = pragma_with_for_as_child.find_first(TOKEN_TYPE.FOR) # TODO?
      if not for_token or len(for_token.children) != 2: # because for contains two children
        continue
      varialbe_reassignment = for_token.find_first(TOKEN_TYPE.SHORT_VARIABLE_REASSIGNMENT)
      if not varialbe_reassignment:
        varialbe_reassignment = for_token.find_first(TOKEN_TYPE.LONG_VARIABLE_REASSIGNMENT)
        if not varialbe_reassignment:
          continue
      operation = util.find_varialbe_operations(varialbe_reassignment)
      if len(operation) != 1:
        continue
      operation = operation[0]
      target = varialbe_reassignment.find_first(TOKEN_TYPE.TARGET)
      if not target:
        continue
      if varialbe_reassignment.type == TOKEN_TYPE.LONG_VARIABLE_REASSIGNMENT:
        left_operand = varialbe_reassignment.find_first(TOKEN_TYPE.LEFT_OPERAND)
        if not left_operand or left_operand.line.content != target.line.content:
          continue
      pragma_with_for_as_child.modify_keywords(
        [PRAGMA_KEYWORDS.REDUCTION],
        {PRAGMA_KEYWORDS.REDUCTION: f"{operation.line.content}:{target.line.content}"}
      )

      self.context.offer_with_new_token([pragma_with_for_as_child], [pragma_with_for_as_child], self.rule_id)

  def generate_param(self) -> str:
    pass

"""

===============before============
int a[3] = {1,2,3};
int sum = 0;
#pragma omp for
for (int i = 0; i < 10; i++)
{
  sum += a[i];
}


===============after============
int a[3] = {1,2,3};
int sum = 0;
#pragma omp for reduction(+:sum)
for (int i = 0; i < 10; i++)
{
  sum += a[i];
}


Conditions:

1) Check that in for is just ne assignemmt:


  1.1) check target is not array element
  1.2) get operation -> build keyword based on it

  1.1) Check that on left -> no \[ and \].
  1.2) Check what kind of operation is used.  += or +

  sum += a[i];
  sum = sum + a[i];

  product *= a[i];
  product = product * a[i];

  any_true = any_true || condition[i]; -> ||:any_true
  all_true = all_true && condition[i]; -> &&:all_true


2) Check that inside only if statement

array elements compared with variable and then assignmen to it:

if (array[i] < minimum) {
  minimum = array[i];
}

OR

if (array[i] > maximum) {
  maximum = array[i];
}

then replace with min:minimum or max:maximum

"""