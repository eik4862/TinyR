from enum import *
from typing import *

"""
ENUMS FOR VARIOUS TYPES.

Here, 'type' does not stand for classes in TypeSymbol module.
They have no direct relation with type inference. They are just 'type' in usual sense.

Enums should inherit IntEnum class in enum module 
and their values should be assigned using auto function lying in the same module.
Function auto assigns integer values starting from 1 (NOT 0).
Avoid using these integer values directly, if possible. (In most cases, it is indeed possible.)

All enums are the end of inheritance. No further inheritance is allowed.
"""


@final
class TokT(IntEnum):
    """
    Token types.
    """
    VAR = auto()    # Variable token
    NUM = auto()    # Numeric token
    STR = auto()    # String token
    BOOL = auto()   # Boolean token
    OP = auto()     # Operator token
    ARR = auto()    # Array token
    VOID = auto()   # Void token
    FUN = auto()    # Function token
    KWARG = auto()  # Keyword argument token
    STRT = auto()   # Struct token
    MEM = auto()    # Struct member token
    EOF = auto()    # EOF(End Of File) token

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


@final
class OpT(IntEnum):
    """
    Operator types.
    """
    # Arithmetic operators
    EXP = auto()     # ^ and **
    ADD = auto()     # +
    SUB = auto()     # -
    SEQ = auto()     # :
    MATMUL = auto()  # %*%
    MOD = auto()     # %%
    QUOT = auto()    # %/%
    MUL = auto()     # *
    DIV = auto()     # /

    # Comparison operators
    LSS = auto()     # <
    LEQ = auto()     # <=
    GRT = auto()     # >
    GEQ = auto()     # >=
    EQ = auto()      # ==
    NEQ = auto()     # !=

    # Boolean operators
    NEG = auto()     # !
    AND = auto()     # & and &&
    OR = auto()      # | and ||

    # Special operators
    IDX = auto()     # [
    LPAR = auto()    # (
    RPAR = auto()    # )
    LBRA = auto()    # [
    RBRA = auto()    # ]
    LCUR = auto()    # {
    RCUR = auto()    # }
    COM = auto()     # ,
    ASGN = auto()    # =

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


@final
class Errno(IntEnum):
    """
    Error types.
    """
    INVALID_TOK = auto()    # Invalid token encountered.
    NCLOSED_PARN = auto()   # Parenthesis or quote is not closed.
    INCOMP_EXPR = auto()    # Input expression is incomplete.
    NOT_DEFINE = auto()     # Variable is used before assignment.
    FUN_CALL_MISS = auto()  # Function call expression is not complete.
    ARG_MISPOS = auto()     # Non-keyword argument for function call is followed by keyword arguments.
    MEMID_MISS = auto()     # Member id in a struct is missing.
    INVALID_LVAL = auto()   # LHS of an assignment cannot be interpreted as a l-value.
    ID_DUP = auto()         # Member ids in a strut are duplicated.
    ASGN_T_MISS = auto()    # Types of both hand sides do not match in case of assignment with indexing.
    ASGN_N_MISS = auto()    # Assignment error.
    INHOMO_ELEM = auto()    # Types of elements in an array are not identical.
    SGNTR_NFOUND = auto()   # Operator or function call signature is wrong.
    KERNEL_ERR = auto()     # Python kernel raised exception during computation.
    DIM_MISMATCH = auto()   # Dimension is not compatible for some computation.
    EMPTY_IDX = auto()      # Index list for indexing is empty.
    IDX_BOUND = auto()      # Index is out of bound.
    FUN_ERR = auto()        # Function raised exception during computation.
    NOT_IMPLE = auto()      # The functionality is not implemented.

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


@final
class T(IntEnum):
    """
    Type symbol types.
    """
    NUM = auto()   # Numeric type
    BOOL = auto()  # Boolean type
    STR = auto()   # String type
    VOID = auto()  # Void type
    ARR = auto()   # Array type
    STRT = auto()  # Struct type
    FUN = auto()   # Function type
    NA = auto()    # NA type

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


"""
COMMENT WRITTEN: 2021.3.2.
"""