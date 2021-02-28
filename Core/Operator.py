from __future__ import annotations

from typing import Optional, Tuple, Callable, Any, List, final
from Core.Type import OpT, T
from Core.TypeSymbol import TSym, NumTSym, StrTSym, BoolTSym, ArrTSym, VoidTSym
from Class.Array import Arr, Vec, Mat
from operator import add, sub, mul, mod, floordiv, truediv, pow, pos, neg, eq, ne, le, ge, gt, lt, and_, or_

"""
TYPE CHECKING & ROUTING LOGIC
"""


@final
class Arith:
    """
    Abstract class for arithmetic operations.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    """
    BASIC OPERATIONS
    """

    @staticmethod
    def __matmul(v1: Any, v2: Any) -> Arr:
        return v1 @ v2 if isinstance(v1, Arr) or isinstance(v2, Arr) else Mat([Vec([v1 * v2])], [1, 1])

    @staticmethod
    def __seq(v1: Any, v2: Any) -> Arr:
        v1, v2 = round(v1), round(v2)
        elem: List = [v1 + i for i in range(v2 - v1 + 1)] if v1 <= v2 else [v1 - i for i in range(v1 - v2 + 1)]

        return Vec(elem)

    """
    TYPE CHECKING LOGIC
    """

    @staticmethod
    def __t_chk_hlpr_bin(t1: TSym, t2: TSym) -> Optional[TSym]:
        """
        Type checking for general binary arithmetic.

        t1 op t2 => Num if sup(t1, t2) <: Num
        t1 op t2 => Arr[Num, n] if sup(t1, t2) = Arr[a, n] and a <: Num
        """
        sup_t: Optional[TSym] = TSym.sup(t1, t2)

        if sup_t is None:
            return None

        if sup_t.base and sup_t <= NumTSym():
            return NumTSym()
        elif sup_t.t == T.ARR and sup_t.elem <= NumTSym():
            return ArrTSym(NumTSym(), sup_t.dept)

        return None

    @staticmethod
    def __t_chk_hlpr_uni(t: TSym) -> Optional[TSym]:
        """
        Type checking for general unary arithmetic.

        op t => Num if t <: Num
        op t => Arr[Num, n] if t = Arr[a, n] and a <: Num
        """
        if t.base:
            return NumTSym() if t <= NumTSym() else None
        elif t.t == T.ARR:
            return ArrTSym(NumTSym(), t.dept) if t.elem <= NumTSym() else None

        return None

    @staticmethod
    def __t_chk_hlpr_add(t1: TSym, t2: TSym) -> Optional[TSym]:
        """
        Type checking for addition.

        t1 + t2 => Num if sup(t1, t2) <: Num
        t1 + t2 => Str if sup(t1, t2) = Str
        t1 + t2 => Arr[Num, n] if sup(t1, t2) = Arr[a, n] and a <: Num
        t1 + t2 => Arr[Str, n] if sup(t1, t2) = Arr[a, n] and a = Str
        """
        sup_t: Optional[TSym] = TSym.sup(t1, t2)

        if sup_t is None:
            return None

        if sup_t.base:
            if sup_t <= NumTSym():
                return NumTSym()
            elif sup_t == StrTSym():
                return StrTSym()
            else:
                return None
        elif sup_t.t == T.ARR:
            if sup_t.elem <= NumTSym():
                return ArrTSym(NumTSym(), sup_t.dept)
            elif sup_t.elem == StrTSym():
                return ArrTSym(StrTSym(), sup_t.dept)
            else:
                return None

        return None

    @staticmethod
    def __t_chk_hlpr_mul(t1: TSym, t2: TSym) -> Optional[TSym]:
        """
        Type checking for multiplication.

        t1 * t2 => Num if sup(t1, t2) <: Num
        t1 * t2 => Str if (t1 <: Num and t2 = Str) or (t1 = Str and t2 <: Num)
        t1 * t2 => Arr[Num, n] if sup(t1, t2) = Arr[a, n] and a <: Num
        Arr[Num, m] * Arr[Str, n] => Arr[Str, max(m, n)]
        Arr[Str, m] * Arr[Num, n] => Arr[Str, max(m, n)]
        """
        if t1.base:
            if t2.base and ((t1 <= NumTSym() and t2 == StrTSym()) or (t2 <= NumTSym() and t1 == StrTSym())):
                return StrTSym()
            elif t2.t == T.ARR and \
                    ((t1 <= NumTSym() and t2.elem == StrTSym()) or (t2.elem <= NumTSym() and t1 == StrTSym())):
                return ArrTSym(StrTSym(), t2.dept)
        elif t1.t == T.ARR:
            if t2.base and ((t1.elem <= NumTSym() and t2 == StrTSym()) or (t2 <= NumTSym() and t1.elem == StrTSym())):
                return ArrTSym(StrTSym(), t1.dept)
            elif t2.t == T.ARR and \
                    ((t1.elem <= NumTSym() and t2.elem == StrTSym()) or
                     (t2.elem <= NumTSym() and t1.elem == StrTSym())):
                return ArrTSym(StrTSym(), max(t1.dept, t2.dept))

        return Arith.__t_chk_hlpr_bin(t1, t2)

    @staticmethod
    def __t_chk_hlpr_matmul(t1: TSym, t2: TSym) -> Optional[TSym]:
        """
        Type checking for matrix multiplication.
        
        t1 %*% t2 => Arr[Num, 2] if sup(t1, t2) <: Num
        t1 %*% t2 => Arr[Num, max(n, 2)] if sup(t1, t2) = Arr[a, n] and a <: Num
        """
        t = Arith.__t_chk_hlpr_bin(t1, t2)

        if t is None:
            return None

        return ArrTSym(t, 2) if t.base else ArrTSym(t.elem, max(2, t.dept))

    @staticmethod
    def __t_chk_hlpr_seq(t1: TSym, t2: TSym) -> Optional[TSym]:
        """
        Type checking for sequence construction operation.

        t1:t2 => Arr[Num, 1] if t1, t2 <: Num
        """
        return ArrTSym(NumTSym(), 1) if t1 <= NumTSym() and t2 <= NumTSym() else None

    @staticmethod
    def t_chk(op: OpT, arg: List[TSym]) -> Tuple[Optional[TSym], Optional[Callable]]:
        """
        Checks type for arithmetic operation and infers the result type.
        If the type check is successful, it also returns function pointer corresponding to the operation.
        This returned function pointer will be used by interpreter.

        :param op: Arithmetic operation to be type checked.
        :param arg: Operands.

        :return: Tuple consists of inferred result type and function pointer which conducts corresponding operation.
                 If type check fails, it returns None, None.
        """
        if op == OpT.ADD:
            if len(arg) == 1:
                return Arith.__t_chk_hlpr_uni(*arg), pos
            elif len(arg) == 2:
                return Arith.__t_chk_hlpr_add(*arg), add
            else:
                return None, None
        elif op == OpT.SUB:
            if len(arg) == 1:
                return Arith.__t_chk_hlpr_uni(*arg), neg
            elif len(arg) == 2:
                return Arith.__t_chk_hlpr_bin(*arg), sub
            else:
                return None, None
        elif op == OpT.MUL:
            if len(arg) == 2:
                return Arith.__t_chk_hlpr_mul(*arg), mul
            else:
                return None, None
        elif op == OpT.MATMUL:
            if len(arg) == 2:
                return Arith.__t_chk_hlpr_matmul(*arg), Arith.__matmul
            else:
                return None, None
        elif len(arg) == 2:
            if op == OpT.DIV:
                return Arith.__t_chk_hlpr_bin(*arg), truediv
            elif op == OpT.MOD:
                return Arith.__t_chk_hlpr_bin(*arg), mod
            elif op == OpT.QUOT:
                return Arith.__t_chk_hlpr_bin(*arg), floordiv
            elif op == OpT.SEQ:
                return Arith.__t_chk_hlpr_seq(*arg), Arith.__seq
            else:
                return Arith.__t_chk_hlpr_bin(*arg), pow
        else:
            return None, None


@final
class Comp:
    """
    Abstract class for comparision operations.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    """
    INTERNAL TYPE CHECKING LOGIC
    """

    @staticmethod
    def __t_chk_hlpr(t1: TSym, t2: TSym) -> Optional[TSym]:
        """
        Type checking for general comparison.

        t1 op t2 => Bool if sup(t1, t2) <: Num or sup(t1, t2) = Str
        t1 op t2 => Arr[Bool, n] if sup(t1, t2) = Arr[a, n] and (a <: Num or a = Str)
        """
        sup_t: Optional[TSym] = TSym.sup(t1, t2)

        if sup_t is None:
            return None

        if sup_t.base and (sup_t <= NumTSym() or sup_t == StrTSym()):
            return BoolTSym()
        elif sup_t.t == T.ARR and (sup_t.elem <= NumTSym() or sup_t.elem == StrTSym()):
            return ArrTSym(BoolTSym(), sup_t.dept)

        return None

    """
    TYPE CHECKING METHODS
    """

    @staticmethod
    def t_chk(op: OpT, arg: List[TSym]) -> Tuple[Optional[TSym], Optional[Callable]]:
        """
        Checks type for comparison operation and infers the result type.
        If the type check is successful, it also returns function pointer corresponding to the operation.
        This returned function pointer will be used by interpreter.

        :param op: Comparison operation to be type checked.
        :param arg: Operands.

        :return: Tuple consists of inferred result type and function pointer which conducts corresponding operation.
                 If type check fails, it returns None, None.
        """
        if len(arg) == 2:
            if op == OpT.LSS:
                return Comp.__t_chk_hlpr(*arg), lt
            elif op == OpT.LEQ:
                return Comp.__t_chk_hlpr(*arg), le
            elif op == OpT.GRT:
                return Comp.__t_chk_hlpr(*arg), gt
            elif op == OpT.GEQ:
                return Comp.__t_chk_hlpr(*arg), ge
            elif op == OpT.EQ:
                return Comp.__t_chk_hlpr(*arg), eq
            else:
                return Comp.__t_chk_hlpr(*arg), ne
        else:
            return None, None


@final
class Logi:
    """
    Abstract class for logical operations.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    """
    TYPE CHECKING LOGIC
    """

    @staticmethod
    def __t_chk_hlpr_bin(t1: TSym, t2: TSym) -> Optional[TSym]:
        """
        Type checking for general binary logical operation.

        t1 op t2 => Bool if sup(t1, t2) <: Num
        t1 op t2 => Arr[Bool, n] if sup(t1, t2) = Arr[a, n] and a <: Num
        """
        sup_t: Optional[TSym] = TSym.sup(t1, t2)

        if sup_t is None:
            return None

        if sup_t.base and sup_t <= NumTSym():
            return BoolTSym()
        elif sup_t.t == T.ARR and sup_t.elem <= NumTSym():
            return ArrTSym(BoolTSym(), sup_t.dept)

        return None

    @staticmethod
    def __t_chk_hlpr_uni(t: TSym) -> Optional[TSym]:
        """
        Type checking for general unary logical operation.

        op t => Bool if t <: Num
        op t => Arr[Bool, n] if t = Arr[a, n] and a <: Num
        """
        if t.base:
            return BoolTSym() if t <= NumTSym() else None
        elif t.t == T.ARR:
            return ArrTSym(BoolTSym(), t.dept) if t.elem <= NumTSym() else None

        return None

    @staticmethod
    def t_chk(op: OpT, arg: List[TSym]) -> Tuple[Optional[TSym], Optional[Callable]]:
        """
        Checks type for logical operation and infers the result type.
        If the type check is successful, it also returns function pointer corresponding to the operation.
        This returned function pointer will be used by interpreter.

        :param op: Logical operation to be type checked.
        :param arg: Operands.

        :return: Tuple consists of inferred result type and function pointer which conducts corresponding operation.
                 If type check fails, it returns None, None.
        """
        if op == OpT.NEG:
            if len(arg) == 1:
                return Logi.__t_chk_hlpr_uni(*arg), lambda x: not x if not isinstance(x, Arr) else ~x
            else:
                return None, None
        elif len(arg) == 2:
            if op == OpT.AND:
                return Logi.__t_chk_hlpr_bin(*arg), and_
            else:
                return Logi.__t_chk_hlpr_bin(*arg), or_
        else:
            return None, None


@final
class Sp:
    """
    Abstract class for special operations.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    """
    BASIC OPERATIONS
    """

    @staticmethod
    def __idx(*args: Any) -> Any:
        src: Any = args[0]
        idx: List = list(args[1:])

        if isinstance(src, Arr):
            return src.get(idx)
        else:
            # A little trick here.
            # Note that when base type receives indexing, that means it needs AT LEAST one promotion.
            return Vec([src]).get(idx)

    @staticmethod
    def __addr(*args: Any) -> Tuple:
        """
        Computes address for assignment.

        id[idx] => (id, idx)
        (id, idx1)[idx2] => (id, idx1 + idx2)
        """
        return (args[0], list(args[1:])) if type(args[0]) == str else (args[0][0], args[0][1] + list(args[1:]))

    """
    TYPE CHECKING LOGIC
    """

    @staticmethod
    def __t_chk_hlpr_idx(t1: TSym, t2: List[TSym]) -> Optional[TSym]:
        """
        Type checking for indexing operation.

        Let a be a base type, bi <: Num, and (ci <: Arr[Num, 1] or ci = Void).
        a[b1, ..., bp] => a if a is base type.
        a[b1, ..., bp, c1, ..., cq] => Arr[a, q] if a is base type.
        Arr[a, n][b1, ..., bp, c1, ..., cq] = Arr[a, max(p + q, n) - p] if max(p + q, n) > p
        Arr[a, n][b1, ..., bp, c1, ..., cq] => a if max(p + q, n) = p
        """
        if not (t1.base or t1.t == T.ARR):
            return None

        dept: int = max(t1.dept, len(t2)) if t1.t == T.ARR else len(t2)

        for t in t2:
            if t == VoidTSym():
                continue
            elif t <= NumTSym():
                dept -= 1
            elif t <= ArrTSym(NumTSym(), 1):
                continue
            else:
                return None

        if t1.base:
            return ArrTSym(t1, dept) if dept > 0 else t1
        else:
            return ArrTSym(t1.elem, dept) if dept > 0 else t1.elem

    @staticmethod
    def __t_chk_hlpr_asgn(t1: TSym, t2: TSym) -> Optional[TSym]:
        """
        Type checking for assignment operation.

        a = b => b if b <: a
        """
        return t2 if t2 <= t1 else None

    @staticmethod
    def t_chk(op: OpT, arg: List[TSym], lval: bool = False) -> Tuple[Optional[TSym], Optional[Callable]]:
        """
        Checks type for special operation and infers the result type.
        If the type check is successful, it also returns function pointer corresponding to the operation.
        This returned function pointer will be used by interpreter.
        The flag lval is used to determine whether the given indexing is 'real' indexing or address computation.

        :param op: Special operation to be type checked.
        :param arg: Operands.
        :param lval: Flag for l-value. (Default: False)

        :return: Tuple consists of inferred result type and function pointer which conducts corresponding operation.
                 If type check fails, it returns None, None.
        """
        if op == OpT.IDX:
            if len(arg) < 2:
                return None, None
            else:
                return Sp.__t_chk_hlpr_idx(arg[0], arg[1:len(arg)]), (Sp.__addr if lval else Sp.__idx)
        else:
            if len(arg) != 2:
                return None, None
            else:
                return Sp.__t_chk_hlpr_asgn(*arg), None

    # Just for testing
    @staticmethod
    def foo():
        print('HELLO WORLD')
