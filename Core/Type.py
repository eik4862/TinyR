from enum import IntEnum, auto
from typing import final


@final
class TokT(IntEnum):
    VAR = auto()
    NUM = auto()
    STR = auto()
    BOOL = auto()
    OP = auto()
    ARR = auto()
    VOID = auto()
    FUN = auto()
    KWARG = auto()
    STRT = auto()
    MEM = auto()
    EOF = auto()

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


@final
class OpT(IntEnum):
    EXP = auto()
    ADD = auto()
    SUB = auto()
    SEQ = auto()
    MATMUL = auto()
    MOD = auto()
    QUOT = auto()
    MUL = auto()
    DIV = auto()
    LSS = auto()
    LEQ = auto()
    GRT = auto()
    GEQ = auto()
    EQ = auto()
    NEQ = auto()
    NEG = auto()
    AND = auto()
    OR = auto()
    IDX = auto()
    LPAR = auto()
    RPAR = auto()
    LBRA = auto()
    RBRA = auto()
    LCUR = auto()
    RCUR = auto()
    COM = auto()
    ASGN = auto()

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


@final
class Errno(IntEnum):
    INVALID_TOK = auto()
    NCLOSED_PARN = auto()
    INCOMP_EXPR = auto()
    NOT_DEFINE = auto()
    FUN_CALL_MISS = auto()
    KWARG_MISS = auto()
    MEMID_MISS = auto()
    INVALID_LVAL = auto()
    ID_DUP = auto()
    ASGN_T_MISS = auto()
    ASGN_N_MISS = auto()
    INHOMO_ELEM = auto()
    SGNTR_NFOUND = auto()
    KERNEL_ERR = auto()
    DIM_MISMATCH = auto()
    EMPTY_IDX = auto()
    IDX_BOUND = auto()
    FUN_ERR = auto()
    NOT_IMPLE = auto()


@final
class T(IntEnum):
    NUM = auto()
    BOOL = auto()
    STR = auto()
    VOID = auto()
    ARR = auto()
    FUN = auto()
    STRT = auto()
    NA = auto()
