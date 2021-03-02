from __future__ import annotations

from .Type import *

"""
CLASSES REPRESENTING TYPES.

There are two category of types: base type and composite type.
Only numeric, boolean, string, and void are base types.
Other types, array, struct, and function, are all composite types.
Composite types are represented by using base types and some additional information.

Actually, module Type defines one more type, NA.
However, NA type must be used temporarily, like placeholder.
Most operations and functions on types implicitly assume that there is no NA type.
"""


class TSym:
    """
    Root class for type symbols.

    For most cases, this class should not be instantiated.
    Instead, use this class as a wild card meaning 'any type symbol'.
    Nevertheless, there are some special occasions where instance of this class is quite useful.
    In such occasions, extra care must be taken since the instance has NA type, unless specified.
    """

    def __init__(self, t: T = T.NA) -> None:
        # Symbol type. Subclasses which are used in most cases automatically fills in this field properly.
        self.__t: T = t
        # Flag indicating whether the symbol is base type or not.
        self.__base: bool = t in [T.NUM, T.BOOL, T.STR, T.VOID]

    """
    BUILT-IN OVERRIDING
    """

    def __str__(self) -> str:
        return 'NA'

    __repr__ = __str__

    """
    OPERATIONS
    """

    def __eq__(self, other: TSym) -> bool:
        """
        Determines whether two types are equal or not.

        Rules determining an equality of two types are as follows:
            1. a == b if a and b are the same base type.                                               [EqBase]
            2. Arr[a, m] == Arr[b, n] if a == b and m = n.                                             [EqArr]
            3. ((a1, ..., ap) => b) == ((c1, ..., cq) => d) if ai == ci for all i, b == d, and p = q.  [EqFun]
            4. Two struct types a and b are equal iff they have the same ids
               and for any id, type of a[id] and that of b[id] are equal.                              [EqStrt]

        NA type should not be compared.
        """
        if self.__t != other.__t:
            return False

        if self.__base and other.__base and self.__t == other.__t:
            # [EqBase]
            return True
        elif self.__t == T.ARR:
            # [EqArr]
            return self.elem.__t == other.elem.__t and self.dept == other.dept
        elif self.__t == T.FUN:
            # [EqFun]
            return self.args == other.args and self.ret == other.ret
        elif self.__t == T.STRT:
            # [EqStrt]
            return self.elem == other.elem

        return False

    def __le__(self, other: TSym) -> bool:
        """
        Determines whether type a is a subtype of type b or not.

        Rules determining subtype relation are as follows:
            1. a <: b if a == b.  [SubEq]
            2. Void <: a for any type a.  [SubVoid]
            3. Bool <: Num.  [SubBool]
            4. a <: Arr[b, n] if a <: b and a is base type.  [SubArr1]
            5. Arr[a, n] <: Arr[b, m] if a <: b and n <= m.  [SubArr2]
            6.

        NA type should not be compared.
        """
        if self.__t == T.VOID:
            return True
        elif self.__t == T.BOOL and other.__t == T.NUM:
            return True
        elif self.__base and other.__base and self == other:
            return True

        if other.__t == T.ARR:
            if self.__base:
                return self <= other.elem
            elif self.__t == T.ARR:
                return self.elem <= other.elem and self.dept <= other.dept

        if self.__t == other.__t == T.FUN:
            if len(self.args) != len(other.args):
                return False

            return all([self.args[i] <= other.args[i] for i in range(len(self.args))]) and self.ret <= other.ret

        if self.__t == other.__t == T.STRT:
            if len(self.elem) != len(other.elem):
                return False

            for k, t1 in self.elem:
                t2: Optional[TSym] = other.elem.get(k, None)

                if t2 is None or not (t1 <= t2):
                    return False

            return True

        return False

    @staticmethod
    def sup(*set_: TSym) -> Optional[TSym]:
        """
        This method computes supremum of the given types set.
        Supremum of type set A = {a1, ..., ap} is defined as type b such that satisfies the followings:
            1. For any i <= p, ai <: b.
            2. For any type c such that satisfies condition 1, b <: c.
        Note that since subtype system is not preorder, supremum of some sets does not exist.
        Also, supremum of an empty set does not exist.

        sup({a1, ..., ap, ap+1}) = sup({sup({a1, ..., ap}), ap+1})
        sup({a}) = a
        sup({a, b}) = a if b <: a
        sup({a, Arr[b, n]}) = Arr[b, n] if a <: b and a is base type.
        sup({a, Arr[a, n]}) = Arr[a, n] if b <: a and a is base type.
        sup({Arr[a, m], Arr[b, n]}) = Arr[b, max(m, n)] if a <: b

        :param set_: Set of types whose supremum is to be computed.

        :return: Supremum of the given set. If the supremum does not exists, it returns None.
        """
        if len(set_) == 0:
            return None

        sup_t: TSym = VoidTSym()

        for t in set_:
            if sup_t.__base:
                if t.__base:
                    if sup_t <= t:
                        sup_t = t
                    elif not (t <= sup_t):
                        return None
                elif t.__t == T.ARR:
                    if sup_t <= t.elem:
                        sup_t = t
                    elif t.elem <= sup_t:
                        sup_t = ArrTSym(sup_t, t.dept)
                    else:
                        return None
                else:
                    return None
            elif sup_t.__t == T.ARR:
                if t.__base:
                    if sup_t.elem <= t:
                        sup_t = ArrTSym(t, sup_t.dept)
                    elif not (t <= sup_t.elem):
                        return None
                elif t.__t == T.ARR:
                    if sup_t.elem <= t.elem:
                        sup_t = ArrTSym(t.elem, max(sup_t.dept, t.dept))
                    elif t.elem <= sup_t.elem:
                        sup_t = ArrTSym(sup_t.elem, max(sup_t.dept, t.dept))
                    else:
                        return None
                else:
                    return None
            else:
                return None

        return sup_t

    """
    GETTERS & SETTERS
    """

    @property
    def t(self) -> T:
        return self.__t

    @property
    def base(self) -> bool:
        return self.__base


"""
BASE TYPES
"""


@final
class NumTSym(TSym):
    def __init__(self) -> None:
        super().__init__(T.NUM)

    def __str__(self) -> str:
        return 'Num'

    __repr__ = __str__


@final
class StrTSym(TSym):
    def __init__(self) -> None:
        super().__init__(T.STR)

    def __str__(self) -> str:
        return 'Str'

    __repr__ = __str__


@final
class BoolTSym(TSym):
    def __init__(self) -> None:
        super().__init__(T.BOOL)

    def __str__(self) -> str:
        return 'Bool'

    __repr__ = __str__


@final
class VoidTSym(TSym):
    def __init__(self) -> None:
        super().__init__(T.VOID)

    def __str__(self) -> str:
        return 'Void'

    __repr__ = __str__


"""
COMPOSITE TYPES
"""


@final
class ArrTSym(TSym):
    def __init__(self, elem: TSym, dept: int) -> None:
        """
        Array type is defined by two components, type of element and depth(# of nesting).
        For example, [2, 3] is Arr[Num, 1] and [[T, T], [F, F]] is Arr[Bool, 2].
        There is no array with depth 0.

        :param elem: Type of element.
        :param dept: Depth of the array.
        """
        super().__init__(T.ARR)
        self.__elem: TSym = elem
        self.__dept: int = dept

    def __str__(self) -> str:
        return f'Arr[{self.__elem}, {self.__dept}]'

    __repr__ = __str__

    @property
    def elem(self) -> TSym:
        return self.__elem

    @property
    def dept(self) -> int:
        return self.__dept


@final
class FunTSym(TSym):
    def __init__(self, args: List[TSym], ret: TSym) -> None:
        super().__init__(T.FUN)
        self.__args: List[TSym] = args
        self.__ret: TSym = ret

    def __str__(self) -> str:
        args: str = ', '.join(map(str, self.__args))

        return f'({args}) => {self.__ret}'

    __repr__ = __str__

    @property
    def args(self) -> List[TSym]:
        return self.__args

    @property
    def ret(self) -> TSym:
        return self.__ret


@final
class StrtTSym(TSym):
    def __init__(self, elem: Dict[str, TSym] = None) -> None:
        if elem is None:
            elem = {}

        super().__init__(T.STRT)
        self.__elem: Dict[str, TSym] = elem

    def __str__(self) -> str:
        return str(self.__elem)

    __repr__ = __str__

    @property
    def elem(self) -> Dict[str, TSym]:
        return self.__elem
