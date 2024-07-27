from __future__ import annotations
from enum import Enum
from abc import ABC, abstractmethod
from kernel_tuner.generation.code.line import Line
from kernel_tuner.generation.code.code import Code, CodeBlock
import random
import copy

class PRAGMA_TOKEN_TYPE(Enum):
  ROOT = 1  
  DATA_ENTER = 2
  DATA_EXIT = 3
  TEAMS = 4
  PARALLEL = 5
  DISTRIBUTE = 6
  SECTIONS = 7
  SINGLE = 8
  SIMD = 9
  DECLARE = 10
  TASK = 11
  TASKLOOP = 12
  TASKYIELD = 13
  UPDATE = 14
  MASTER = 15
  CRITICAL = 16
  BARRIER = 17 
  TASKWAIT = 18
  TASKGROUP = 19
  ATOMIC = 20
  FLUSH = 21
  ORDERED = 22
  CANCEL = 23
  THREADPRIVATE = 24
  FOR = 25
  TARGET = 26  
  UNKNOWN = 27


  def is_data(self):
    return True if self is PRAGMA_TOKEN_TYPE.DATA_ENTER or self is PRAGMA_TOKEN_TYPE.DATA_EXIT else False

  
class PRAGMA_KEYWORDS(Enum):
  PARALLEL = 'parallel'
  FOR = 'for'
  SIMD = 'simd'
  TASK = 'task'
  TEAMS = 'teams'
  DISTRIBUTE = 'distribute'
  UNKNOWN = 'unknown'
  NUM_THREADS = 'num_threads'
  NUM_TEAMS = 'num_teams'
  DEFAULT = 'default'
  PRIVATE = 'private'
  FIRST_PRIVATE = 'firstprivate'
  LATS_PRIVATE = 'lastprivate'
  COPY_PRIVATE = 'copyprivate'
  LINEAR = 'linear'
  SCHEDULE = 'schedule'
  ORDERED = 'ordered'
  NOWAIT = 'nowait'
  SHARED = 'shared'
  COPY_IN = 'copyin'
  REDUCTION = 'reduction'
  PROC_BIND = 'proc_bind'
  SAFELEN = 'safelen'
  SIMDLEN = 'simdlen'
  ALIGNED = 'aligned'
  UNIFORM = 'uniform'
  IN_BRANCH = 'inbranch'
  NOT_IN_BRANCH = 'notinbranch'
  FINAL = 'final'
  UNTIED = 'untied'
  MERGEABLE = 'mergeable'
  PRIORITY = 'priority'
  GRAIN_SIZE = 'grainsize'
  NUM_TASKS = 'num_tasks'
  NO_GROUP = 'nogroup'
  TARGET = 'target'
  DATA = 'data'
  DEVICE = 'device'
  MAP = 'map'
  DEPEND = 'depend'
  IS_DEVICE_PTR = 'is_device_ptr'
  DEFAULT_MAP = 'defaultmap'
  DIST_SCHEDULE = 'dist_schedule'
  THREAD_LIMIT = 'thread_limit'
  


PRAGMA_KEYWORDS_VALUES = list(map(lambda x: x.value, PRAGMA_KEYWORDS))

class TOKEN_TYPE(Enum):
  BLOCK = 1
  FOR = 2
  IF = 3
  IF_ELSE = 4
  FUNCTION_CALL = 5
  PRAGMA = 6
  VARIABLE_ASSIGNMENT = 7
  VARIABLE_DECLARATION = 8
  LONG_VARIABLE_REASSIGNMENT = 9
  FOR_INITIALISATION = 10
  FOR_CONDITION = 11
  FOR_OPERATION = 12
  TYPE = 13
  LS = 14
  LSQ = 15
  GR = 16
  GRQ = 17
  
  PRE_INCREMENT = 18
  POST_INCREMENT = 19
  PRE_DECREMENT = 20
  POST_DECREMENT = 21
  FOR_BODY = 22
  COMPLEX_STRUCTURE = 23
  TYPE_INT = 24
  VARIABLE_NAME = 25

  OPERATION = 28

  VARIABLE_TARGET = 29
  BINARY_OPEARION = 30
  SHORT_VARIABLE_REASSIGNMENT = 31 

  TARGET = 32
  ARRAY_ELEMENT = 33
  ARRAY_NAME = 34

  LEFT_OPERAND = 35
  RIGHT_OPERAND = 36

  OPERATION_SUM=37
  OPERATION_MINUS=38
  OPERATION_MUTLIPLICATION=39
  OPERATION_AND=40
  OPERATION_AND_AND=41
  OPERATION_OR=42
  OPERATION_OR_OR=43
  OPERATION_XOR=44

  ARRAY_INDEX = 45
  FUNCTION_VARIABLE_REASSIGNMENT = 46
  FUNCTION_PARAMETERS = 47
  FUNCTION_PARAMETER = 48
  FUNCTION_NAME = 49
  VARIABLE_REASSIGNMENT = 50


class Token(ABC):

  def __init__(self, line: Line, content: CodeBlock, type: TOKEN_TYPE):
    self.line = copy.deepcopy(line)
    self.content = content
    self.type = type
    self.children: list[Token] = []
    self.parent: Token | None = None
    self.id = random.randint(1, 1000)
    pass

  def append_child(self, child):
    self.children.append(child)
    child.parent = self

  def remove_child(self, child):
    self.children.remove(child)
    child.parent = None

  def print_content(self) -> str:
    return '\n'.join(list(map(lambda x: x.content, self.content.lines)))
  
  def find_first(self, type: TOKEN_TYPE) -> Token|None:
    queue:list[Token] = [self]
    results = []
    self.__bfs(type, queue, results)
    return results.pop(0) if len(results) > 0 else None
  
  def find_all(self, type: TOKEN_TYPE) -> list[Token]:
    queue:list[Token] = [self]
    results = []
    self.__bfs(type, queue, results)
    return results

  def __bfs(self, type: TOKEN_TYPE, queue: list[Token], results: list[Token]):
    if len(queue) == 0:
      return None
    cur_tkn = queue.pop(0)
    for ch in cur_tkn.children:
      if ch.type == type:
          results.append(ch)
      queue.append(ch)
    self.__bfs(type, queue, results)
  
  @abstractmethod
  def print(self, debug=False) -> str:
    pass