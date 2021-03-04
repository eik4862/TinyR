from __future__ import annotations

from .TypeSymbol import *
from Class.Array import *

"""
TYPE CHECKING & ROUTING LOGIC

Operators are grouped into four categories:
    1. Arithmetic: EXP, ADD, SUB, SEQ, MATMUL, MOD, QUOT, MUL, DIV
    2. Comparison: LSS, LEQ, GRT, GEQ, EQ, NEQ
    3. Logical   : NEG, AND, OR
    4. Special   : IDX, ASGN

The action of some operators differ depending on # of operands(ADD, SUB) and state of lval(IDX).
Following classes checks these and routes to them properly.

All classes below are implemented as abstract classes. They can not be (and should not be) instantiated.
All classes below are the end of inheritance. No further inheritance is allowed.
"""


@final
class Arith:
    """
    Arithmetic operators.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    """
    WRAPPER
    
    Thin wrappers handling operators which are not Python built-ins.
    Note that matrix multiplication b/w two base types are handled here. (Refer to the comments of Array module.)
    
    The logic below is for internal use only.
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
    TYPE CHECKING & ROUTING LOGIC
    
    Type inference rules are as follows:
        1. [TBinArithBase]
           If   env |- e1 => env', a
                env' |- e2 => env'', b
                Sup(a, b) <: Num
           Then env |- e1 op e2 => env'', Num
        2. [TBinArithArr]
           If   env |- e1 => env', a
                env' |- e2 => env'', b
                Sup(a, b) = Arr[c, n] <: Arr[Num, n]
           Then env |- e1 op e2 => env'', Arr[Num, n]
        3. [TUniArithBase]
           If   env |- e => env', a
                a <: Num
           Then env |- op e => env', Num
        4. [TUniArithArr]
           If   env |- e => env', Arr[a, n]
                a <: Num
           Then env |- op e => env', Arr[Num, n]
        5. [TAddNum]
           If   env |- e1 => env', a
                env' |- e2 => env'', b
                Sup(a, b) <: Num
           Then env |- e1 + e2 => env'', Num
        6. [TAddStr]
           If   env |- e1 => env', a
                env' |- e2 => env'', b
                Sup(a, b) = Str
           Then env |- e1 + e2 => env'', Str
        7. [TAddNumArr]
           If   env |- e1 => env', a
                env' |- e2 => env'', b
                Sup(a, b) = Arr[c, n] <: Arr[Num, n]
           Then env |- e1 + e2 => env'', Arr[Num, n]
        8. [TAddStrArr]
           If   env |- e1 => env', a
                env' |- e2 => env'', b
                Sup(a, b) = Arr[Str, n]
           Then env |- e1 + e2 => env'', Arr[Str, n]
        9. [TMulNum]
           If   env |- e1 => env', a
                env' |- e2 => env'', b
                Sup(a, b) <: Num
           Then env |- e1 * e2 => env'', Num
        10. [TMulStr]
            If   env |- e1 => env', a
                 env' |- e2 => env'', b
                 (a <: Num & b = Str) | (a = Str, b <: Num)
            Then env |- e1 * e2 => env'', Str
        11. [TMulNumArr]
            If   env |- e1 => env', a
                 env' |- e2 => env'', b
                 Sup(a, b) = Arr[c, n] <: Arr[Num, n]
            Then env |- e1 * e2 => env'', Arr[Num, n]
        12. [TMulStrNumArr]
            If   env |- e1 => env', a
                 env' |- e2 => env'', b
                 (a = Str & b = Arr[c, n] <: Arr[Num, n]) | (a = Arr[c, n] <: Arr[Num, n] & b = Str)
            Then env |- e1 * e2 => env'', Arr[Str, n]
        13. [TMulNumStrArr]
            If   env |- e1 => env', a
                 env' |- e2 => env'', b
                 (a <: Num & b = Arr[Str, n]) | (a = Arr[Str, n], b <: Num)
            Then env |- e1 * e2 => env'', Arr[Str, n]
        14. [TMulNumArrStrArr]
            If   env |- e1 => env', a
                 env' |- e2 => env'', b
                 (a = Arr[Str, m]& b = Arr[c, n] <: Arr[Num, n]) | (a = Arr[c, n] <: Arr[Num, n] & b = Arr[Str, m])
            Then env |- e1 * e2 => env'', Arr[Str, max(m, n)]
        15. [TMatmulBase]
            If   env |- e1 => env', a
                 env' |- e2 => env'', b
                 Sup(a, b) <: Num
            Then env |- e1 %*% e2 => env'', Arr[Num, 2]
        16. [TMatmulArr]
            If   env |- e1 => env', a
                 env' |- e2 => env'', b
                 Sup(a, b) = Arr[c, n] <: Arr[Num, n]
            Then env |- e1 %*% e2 => env'', Arr[Num, max(n, 2)]
        17. [TSeq]
            If   env |- e1 => env', Num
                 env' |- e2 => env'', Num
            Then env |- e1 : e2 => env'', Arr[Num, 1]
    
    Routing table for arithmetic operators are as follows:
        Operator  # of operands  Handle
        ADD       2              operator.add
                  1              operator.pos
        SUB       2              operator.sub
                  1              operator.neg
        SEQ       2              Arith.__seq
        MATMUL                   Arith.__matmul
        MOD                      operator.mod
        QUOT                     floordiv
        MUL                      operator.mul
        DIV                      truediv
        EXP                      operator.pow
        
    Most of the logic below is for internal use only.
    """

    @staticmethod
    def __t_chk_hlpr_bin(t1: TSym, t2: TSym) -> Optional[TSym]:
        sup_t: Optional[TSym] = TSym.sup(t1, t2)

        if sup_t is None:
            return None

        if sup_t <= NumTSym():
            # [TBinArithBase]
            return NumTSym()
        elif sup_t.t == T.ARR and sup_t.elem <= NumTSym():
            # [TBinArithArr]
            return ArrTSym(NumTSym(), sup_t.dept)

        return None

    @staticmethod
    def __t_chk_hlpr_uni(t: TSym) -> Optional[TSym]:
        if t.t == T.ARR:
            # [TUniArithArr]
            return ArrTSym(NumTSym(), t.dept) if t.elem <= NumTSym() else None
        else:
            # [TUniArithBase]
            return NumTSym() if t <= NumTSym() else None

    @staticmethod
    def __t_chk_hlpr_add(t1: TSym, t2: TSym) -> Optional[TSym]:
        sup_t: Optional[TSym] = TSym.sup(t1, t2)

        if sup_t is None:
            return None

        if sup_t.t == T.ARR:
            if sup_t.elem <= NumTSym():
                # [TAddNumArr]
                return ArrTSym(NumTSym(), sup_t.dept)
            elif sup_t.elem == StrTSym():
                # [TAddStrArr]
                return ArrTSym(StrTSym(), sup_t.dept)
            else:
                return None
        else:
            if sup_t <= NumTSym():
                # [TAddNum]
                return NumTSym()
            elif sup_t == StrTSym():
                # [TAddStr]
                return StrTSym()
            else:
                return None

    # TODO: Refactor this
    @staticmethod
    def __t_chk_hlpr_mul(t1: TSym, t2: TSym) -> Optional[TSym]:
        if t1.base:
            if t2.base and ((t1 <= NumTSym() and t2 == StrTSym()) or (t2 <= NumTSym() and t1 == StrTSym())):
                # [TMulStr]
                return StrTSym()
            elif t2.t == T.ARR and \
                    ((t1 <= NumTSym() and t2.elem == StrTSym()) or (t2.elem <= NumTSym() and t1 == StrTSym())):
                # [TMulStrNumArr], [TMulNumStrArr]
                return ArrTSym(StrTSym(), t2.dept)
        elif t1.t == T.ARR:
            if t2.base and ((t1.elem <= NumTSym() and t2 == StrTSym()) or (t2 <= NumTSym() and t1.elem == StrTSym())):
                # [TMulStrNumArr], [TMulNumStrArr]
                return ArrTSym(StrTSym(), t1.dept)
            elif t2.t == T.ARR and \
                    ((t1.elem <= NumTSym() and t2.elem == StrTSym()) or
                     (t2.elem <= NumTSym() and t1.elem == StrTSym())):
                # [TMulNumArrStrArr]
                return ArrTSym(StrTSym(), max(t1.dept, t2.dept))

        # [TMulNum], [TMulNumArr]
        return Arith.__t_chk_hlpr_bin(t1, t2)

    @staticmethod
    def __t_chk_hlpr_matmul(t1: TSym, t2: TSym) -> Optional[TSym]:
        t = Arith.__t_chk_hlpr_bin(t1, t2)

        if t is None:
            return None

        # [TMatmulBase], [TMatmulArr]
        return ArrTSym(t, 2) if t.base else ArrTSym(t.elem, max(2, t.dept))

    @staticmethod
    def __t_chk_hlpr_seq(t1: TSym, t2: TSym) -> Optional[TSym]:
        # [TSeq]
        return ArrTSym(NumTSym(), 1) if t1 <= NumTSym() and t2 <= NumTSym() else None

    @staticmethod
    def t_chk(op: OpT, arg: List[TSym]) -> Tuple[Optional[TSym], Optional[Callable]]:
        """
        Checks type and routes to the proper function pointer.

        For type check, it just routes to type checking logic according to the operator op.
        If type check fails, it fails silently rather than raising exceptions.

        :param op: Operator.
        :param arg: Operands.

        :return: Tuple consists of the inferred type and the function pointer. (None, None) if type check fails.
        """
        if len(arg) == 1:
            if op == OpT.ADD:
                return Arith.__t_chk_hlpr_uni(*arg), pos
            elif op == OpT.SUB:
                return Arith.__t_chk_hlpr_uni(*arg), neg
            else:
                return None, None
        elif len(arg) == 2:
            if op == OpT.ADD:
                return Arith.__t_chk_hlpr_add(*arg), add
            elif op == OpT.SUB:
                return Arith.__t_chk_hlpr_bin(*arg), sub
            elif op == OpT.MUL:
                return Arith.__t_chk_hlpr_mul(*arg), mul
            elif op == OpT.MATMUL:
                return Arith.__t_chk_hlpr_matmul(*arg), Arith.__matmul
            elif op == OpT.DIV:
                return Arith.__t_chk_hlpr_bin(*arg), truediv
            elif op == OpT.MOD:
                return Arith.__t_chk_hlpr_bin(*arg), mod
            elif op == OpT.QUOT:
                return Arith.__t_chk_hlpr_bin(*arg), floordiv
            elif op == OpT.SEQ:
                return Arith.__t_chk_hlpr_seq(*arg), Arith.__seq
            elif op == OpT.EXP:
                return Arith.__t_chk_hlpr_bin(*arg), pow
            else:
                return None, None
        else:
            return None, None


@final
class Comp:
    """
    Comparison operators.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    """
    TYPE CHECKING & ROUTING LOGIC
    
    Type inference rules are as follows:
        1. [TCompBase]
           If   env |- e1 => env', a
                env' |- e2 => env'', b
                Sup(a, b) <: Num | Sup(a, b) = Str
           Then env |- e1 op e2 => env'', Bool
        2. [TCompArr]
           If   env |- e1 => env', a
                env' |- e2 => env'', b
                Sup(a, b) = Arr[c, n]
                c <: Num | c = Str
           Then env |- e1 op e2 => env'', Arr[Bool, n]
    
    Routing table for comparison operators are as follows:
        Operator  Handle
        LSS       operator.lt
        LEQ       operator.le
        GRT       operator.gt
        GEQ       operator.ge
        EQ        operator.eq
        NEQ       operator.ne
    
    Most of the logic below is for internal use only.
    """

    @staticmethod
    def __t_chk_hlpr(t1: TSym, t2: TSym) -> Optional[TSym]:
        sup_t: Optional[TSym] = TSym.sup(t1, t2)

        if sup_t is None:
            return None

        if sup_t.t == T.ARR and (sup_t.elem <= NumTSym() or sup_t.elem == StrTSym()):
            # [TCompArr]
            return ArrTSym(BoolTSym(), sup_t.dept)
        elif sup_t <= NumTSym() or sup_t == StrTSym():
            # [TCompBase]
            return BoolTSym()

        return None

    """
    TYPE CHECKING METHODS
    """

    @staticmethod
    def t_chk(op: OpT, arg: List[TSym]) -> Tuple[Optional[TSym], Optional[Callable]]:
        """
        Refer to the comments of Arith.t_chk.
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
    Logical operators.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    """
    WRAPPER

    Thin wrappers handling operators which are not Python built-ins.
    The logic below is for internal use only.
    """

    @staticmethod
    def __not(v: Any) -> bool:
        return not v if not isinstance(v, Arr) else ~v

    """
    TYPE CHECKING & ROUTING LOGIC
    
    Type inference rules are as follows:
        1. [TBinLogiBase]
           If   env |- e1 => env', a
                env' |- e2 => env'', b
                Sup(a, b) <: Num
           Then env |- e1 op e2 => env'', Bool
        2. [TBinLogiArr]
           If   env |- e1 => env', a
                env' |- e2 => env'', b
                Sup(a, b) = Arr[c, n] <: Arr[Num, n]
           Then env |- e1 op e2 => env'', Arr[Bool, n]
        3. [TUniLogiBase]
           If   env |- e => env', a
                a <: Num
           Then env |- op a => env', Bool
        4. [TUniLogiArr]
           If   env |- e => env', a
                a = Arr[b, n] <: Arr[Num, n]
           Then env |- op a => env', Arr[Bool, n]
    
    Routing table for comparison operators are as follows:
        Operator  Handle
        NEG       Logi.__not
        AND       operator.and_
        OR        operator.or_
    
    Most of the logic below is for internal use only.
    """

    @staticmethod
    def __t_chk_hlpr_bin(t1: TSym, t2: TSym) -> Optional[TSym]:
        sup_t: Optional[TSym] = TSym.sup(t1, t2)

        if sup_t is None:
            return None

        if sup_t.t == T.ARR and sup_t.elem <= NumTSym():
            # [TBinLogiArr]
            return ArrTSym(BoolTSym(), sup_t.dept)
        elif sup_t <= NumTSym():
            # [TBinLogiBase]
            return BoolTSym()

        return None

    @staticmethod
    def __t_chk_hlpr_uni(t: TSym) -> Optional[TSym]:
        if t.t == T.ARR:
            # [TUniLogiArr]
            return ArrTSym(BoolTSym(), t.dept) if t.elem <= NumTSym() else None
        elif t.base:
            # [TUniLogiBase]
            return BoolTSym() if t <= NumTSym() else None

        return None

    @staticmethod
    def t_chk(op: OpT, arg: List[TSym]) -> Tuple[Optional[TSym], Optional[Callable]]:
        """
        Refer to the comments of Arith.t_chk.
        """
        if len(arg) == 1:
            if op == OpT.NEG:
                return Logi.__t_chk_hlpr_uni(*arg), Logi.__not
            else:
                return None, None
        elif len(arg) == 2:
            if op == OpT.AND:
                return Logi.__t_chk_hlpr_bin(*arg), and_
            elif op == OpT.OR:
                return Logi.__t_chk_hlpr_bin(*arg), or_
            else:
                return None, None
        else:
            return None, None


@final
class Sp:
    """
    Special operators.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    """
    WRAPPER

    Thin wrappers handling operators which are not Python built-ins.
    The logic below is for internal use only.
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
    TYPE CHECKING & ROUTING LOGIC
    
    Type inference rules are as follows:
        1. [TIdxBaseBase]
           If   env |- e => env0, a
                env(i - 1) |- ei => envi, bi for all i
                a is not array type
                bi <: Num for all i
           Then env |- e[e1, ..., ep] => envp, a
        2. [TIdxBaseArr]
           If   env |- e => env0, a
                env(i - 1) |- ei => envi, bi for all i
                env(i + j - 1) |- e'j => env(i + j), cj for all j
                a is not array type
                bi <: Num for all i
                cj <: Arr[Num, 1] or cj = Void for all j
           Then env |- e[e1, ..., ep, e'1, ..., e'q] => env(p + q), Arr[a, q]
        3. [TIdxArrBase]
           If   env |- e => env0, Arr[a, n]
                env(i - 1) |- ei => envi, bi for all i
                env(i + j - 1) |- e'j => env(i + j), cj for all j
                bi <: Num for all i
                cj <: Arr[Num, 1] or cj = Void for all j
                max(p + q, n) = p
           Then env |- e[e1, ..., ep, e'1, ..., e'q] => env(p + q), a
        4. [TIdxArrArr]
           If   env |- e => env0, Arr[a, n]
                env(i - 1) |- ei => envi, bi for all i
                env(i + j - 1) |- e'j => env(i + j), cj for all j
                bi <: Num for all i
                cj <: Arr[Num, 1] or cj = Void for all j
                max(p + q, n) > p
           Then env |- e[e1, ..., ep, e'1, ..., e'q] => env(p + q), Arr[a, max(p + q, n) - p]
    
    Routing table for comparison operators are as follows:
        Operator  l-value  Handle
        IDX       TRUE     Sp.__addr
                  FALSE    Sp.__idx
    
    Most of the logic below is for internal use only.
    """

    @staticmethod
    def __t_chk_hlpr_idx(t1: TSym, t2: List[TSym]) -> Optional[TSym]:
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

        if t1.t == T.ARR:
            # [TIdxBaseBase], [TIdxBaseArr]
            return ArrTSym(t1.elem, dept) if dept > 0 else t1.elem
        else:
            # [TIdxArrBase], [TIdxArrArr]
            return ArrTSym(t1, dept) if dept > 0 else t1

    @staticmethod
    def t_chk(op: OpT, arg: List[TSym], lval: bool = False) -> Tuple[Optional[TSym], Optional[Callable]]:
        """
        Refer to the comments of Arith.t_chk.
        """
        if len(arg) >= 2:
            if op == OpT.IDX:
                return Sp.__t_chk_hlpr_idx(arg[0], arg[1:]), (Sp.__addr if lval else Sp.__idx)
            else:
                return None, None
        else:
            return None, None
