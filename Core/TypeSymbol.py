from __future__ import annotations

from .Type import *

"""
CLASSES REPRESENTING TYPES.

There are two categories for types: base type and composite type.
Numeric, boolean, string, and void are base types.
Other types, array, struct, and function, are all composite types.
Composite types are defined by using base types and some additional information.

Module Type defines one more type, which is NA.
However, NA type must be used temporarily, like placeholder.
Most operations and functions on types implicitly assume that there is no NA type.
"""


class TSym:
    """
    Root class for type symbols.

    In most cases, this class should not be instantiated.
    Instead, use this class as a wild card meaning 'any type symbol'.
    Nevertheless, there are some special occasions where instance of this class is quite useful.
    In such occasions, extra care must be taken since the instance has NA type, unless specified.
    """

    def __init__(self, t: T = T.NA) -> None:
        # Symbol type. Subclasses fill in this field automatically with proper value.
        self.__t: T = t
        # Flag indicating whether the type is base type or not.
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

        Rules determining the equality of two types are as follows:
            1. a == b if a and b are the same base type.                                               [EqBase]
            2. Arr[a, m] == Arr[b, n] if a == b and m = n.                                             [EqArr]
            3. ((a1, ..., ap) => b) == ((c1, ..., cq) => d) if ai == ci for all i, b == d, and p = q.  [EqFun]
            4. Two struct types a and b are equal iff they have the same ids
               and for any id, type of a[id] and that of b[id] are equal.                              [EqStrt]

        NA type should not be compared.

        :param other: Type to be tested.

        :return: True if self == other. False otherwise.
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
        Determines whether type self is a subtype of type other or not.

        Rules determining subtype relation are as follows:
            1. a <: b if a == b.                                                                      [SubEq]
            2. Void <: a for any type a.                                                              [SubVoid]
            3. Bool <: Num.                                                                           [SubBoolNum]
            4. a <: Arr[b, n] if a <: b and a is base type.                                           [SubBaseArr]
            5. Arr[a, n] <: Arr[b, m] if a <: b and n <= m.                                           [SubArr]
            6. ((a1, ..., ap) => b) <: ((c1, ... cq) => d) if ai <: ci for all i, b <: d, and p = q.  [SubFun]
            7. For struct type a and b, a <: b iff both have the same ids
               and for any id, type of a[id] is a subtype of that of b[id].                           [SubStrt]

        NA type should not be compared.

        :param other: Type to be tested.

        :return: True if self <: other. False otherwise.
        """
        if self.__t == T.VOID:
            # [SubVoid]
            return True
        elif self.__t == T.BOOL and other.__t == T.NUM:
            # [SubBoolNum]
            return True
        elif self.__base and other.__base and self == other:
            # [SubEq]
            return True

        if other.__t == T.ARR:
            if self.__base:
                # [SubBaseArr]
                return self <= other.elem
            elif self.__t == T.ARR:
                # [SubArr]
                return self.elem <= other.elem and self.dept <= other.dept

        if self.__t == other.__t == T.FUN:
            # [SubFun]
            if len(self.args) != len(other.args):
                return False

            return all([self.args[i] <= other.args[i] for i in range(len(self.args))]) and self.ret <= other.ret

        if self.__t == other.__t == T.STRT:
            # [SubStrt]
            if len(self.elem) != len(other.elem):
                return False

            for k, t1 in self.elem.items():
                t2: Optional[TSym] = other.elem.get(k, None)

                if t2 is None or not (t1 <= t2):
                    return False

            return True

        return False

    @staticmethod
    def sup(*set_: TSym) -> Optional[TSym]:
        """
        Computes supremum of the given type set.

        Supremum of type set {a1, ..., ap} is defined as type b st.
            1. For any type ai, ai <: b.
            2. For any type c st. satisfies the first condition, b <: c.
        Since subtype system is not a preorder, supremum of some sets may not exist.
        Also, supremum of an empty set does not exist.

        Rules determining supremum are as follows:
            1. Sup({a1, ..., ap, a(p+1)}) => Sup({Sup({a1, ..., ap}), a(p+1)}).                      [SupRec]
            2. Sup({a}) => a.                                                                        [SupSngl]
            3. Sup({a, b}) => a if b <: a.                                                           [SupSub]
            4. Sup({a, Arr[b, n]}) => Arr[Sup(a, b), n] if a is base type.                           [SupBaseArr]
            6. Sup({Arr[a, m], Arr[b, n]}) => Arr[Sup(a, b), max(m, n)].                             [SupArr]
            7. Sup({(a1, ..., ap) => b, (c1, ..., cq) => d}) =>
                                        ((Sup({a1, c1}), ..., Sup({ap, cq})) => sup(b, d)) if p = q. [SupFun]
            8. Supremum of set consists of two struct types a and b is a struct type c st.
                8.1. Ids of c are the same with those of a(and b).
                8.2. For any id, type of c[id] is supremum of {type of a[id], type of b[id]}.
               if a and b have the same ids.                                                         [SupStrt]

        :param set_: Set of types whose supremum is to be computed.

        :return: Supremum of set_. None if it does not exists.
        """
        if len(set_) == 0:
            return None
        elif len(set_) == 1:
            # [SupSngl]
            return set_[0]
        elif len(set_) > 2:
            # [SupRec]
            t: Optional[TSym] = TSym.sup(*set_[:-1])
            return None if t is None else TSym.sup(t, set_[-1])

        if set_[0].__base:
            if set_[1].__base:
                # [SupSub]
                if set_[0] <= set_[1]:
                    return set_[1]
                elif set_[1] <= set_[0]:
                    return set_[0]
                else:
                    return None
            elif set_[1].__t == T.ARR:
                # [SupBaseArr]
                elem: Optional[TSym] = TSym.sup(set_[0], set_[1].elem)

                return None if elem is None else ArrTSym(elem, set_[1].dept)
            else:
                return None
        elif set_[0].__t == T.ARR:
            if set_[1].__base:
                # [SupBaseArr]
                elem: Optional[TSym] = TSym.sup(set_[0].elem, set_[1])

                return None if elem is None else ArrTSym(elem, set_[0].dept)
            elif set_[1].__t == T.ARR:
                # [SupArr]
                elem: Optional[TSym] = TSym.sup(set_[0].elem, set_[1].elem)

                return None if elem is None else ArrTSym(elem, max(set_[0].dept, set_[1].dept))
            else:
                return None

        if set_[0].__t != set_[1].__t:
            return None

        if set_[0].__t == T.FUN:
            # [SupFun]
            if len(set_[0].args) != len(set_[1].args):
                return None

            args: List[TSym] = []

            for i in range(len(set_[0].args)):
                elem: Optional[TSym] = TSym.sup(set_[0].args[i], set_[1].args[i])

                if elem is None:
                    return None

                args.append(elem)

            ret: Optional[TSym] = TSym.sup(set_[0].ret, set_[01].ret)

            return None if elem is None else FunTSym(args, ret)
        elif set_[0].__t == T.STRT:
            # [SupStrt]
            if len(set_[0].elem) != len(set_[1].elem):
                return None

            elem: Dict[str, TSym] = {}

            for k, t1 in set_[0].elem.items():
                t2: Optional[TSym] = set_[1].elem.get(k, None)

                if t2 is None:
                    return None

                t: Optional[TSym] = TSym.sup(t1, t2)

                if t is None:
                    return None

                elem[k] = t

            return StrtTSym(elem)

        return None

    """
    GETTER & SETTER
    """

    @property
    def t(self) -> T:
        return self.__t

    @property
    def base(self) -> bool:
        return self.__base


"""
BASE TYPE: NUMERIC, STRING, BOOLEAN, AND VOID.
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
BASE TYPE: ARRAY, FUNCTION, AND STRUCT

Array type is defined by the type of elements and depth(# of dimensions).
Note that all elements of an array must be identical.

Function type is defined by the list composed of the types of arguments and the return type.
Function type with no input arguments is valid, but missing or multiple return types are not.

Struct type is defined by the dictionary which contains ids of members and their types.
Struct type with no members at all is valid.
"""


@final
class ArrTSym(TSym):
    def __init__(self, elem: TSym, dept: int) -> None:
        super().__init__(T.ARR)
        # Type of elements.
        self.__elem: TSym = elem
        # Depth(# of dimensions)
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
        # Argument types. Can be an empty list which represents function with no input arguments.
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
    def __init__(self, elem: Dict[str, TSym]) -> None:
        super().__init__(T.STRT)
        # Types of members with their ids. Can be an empty dictionary which represents an empty struct.
        self.__elem: Dict[str, TSym] = elem

    def __str__(self) -> str:
        return str(self.__elem)

    __repr__ = __str__

    @property
    def elem(self) -> Dict[str, TSym]:
        return self.__elem
