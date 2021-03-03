from __future__ import annotations

from operator import *
from copy import deepcopy
from math import ceil, floor
from CDLL.CLibrary import *
from Error.Exception import *

"""
CLASSES REPRESENTING ARRAY, MATRIX, AND VECTOR.

Since these three classes are so closely associated, they are implemented in a single source file.
"""


class Arr:
    """
    Array class.

    Represents multidimensional array(tensor).
    Array can be nested to represent higher dimension: eg. array of matrix, array of array of matrix.
    But one should not assign vectors or base types as elements of array.
    Use matrix or vector in those cases.

    All exceptions raised here should be caught by Interp class.
    Then the erroneous position in the raw input string with the string itself should be properly assigned.
    """

    def __init__(self, elem: List, dim: List[int]) -> None:
        # List of elements.
        self._elem: List = elem
        # Dimension.
        self._dim: List[int] = dim
        # Counter for iteration. Used by built-ins __next__ and __iter__.
        self._curr: int = 0

    """
    BUILT-IN OVERRIDING
    """

    def __add__(self, other: Any) -> Arr:
        return self.__apply(other, add)

    def __radd__(self, other: Any) -> Arr:
        return self.__add__(other)

    def __sub__(self, other: Any) -> Arr:
        return self.__apply(other, sub)

    def __rsub__(self, other: Any) -> Arr:
        return self.__apply(other, lambda x, y: y - x)

    def __mul__(self, other: Any) -> Arr:
        return self.__apply(other, mul)

    def __rmul__(self, other: Any) -> Arr:
        return self.__mul__(other)

    def __matmul__(self, other: Any) -> Arr:
        return self.__apply_matmul(other, matmul)

    def __rmatmul__(self, other: Any) -> Arr:
        return self.__apply_matmul(other, lambda x, y: y @ x)

    def __truediv__(self, other: Any) -> Arr:
        return self.__apply(other, truediv)

    def __rtruediv__(self, other: Any) -> Arr:
        return self.__apply(other, lambda x, y: y / x)

    def __floordiv__(self, other: Any) -> Arr:
        return self.__apply(other, floordiv)

    def __rfloordiv__(self, other: Any) -> Arr:
        return self.__apply(other, lambda x, y: y // x)

    def __pow__(self, other: Any) -> Arr:
        return self.__apply(other, pow)

    def __rpow__(self, other: Any) -> Arr:
        return self.__apply(other, lambda x, y: y ** x)

    def __pos__(self) -> Arr:
        return self

    def __neg__(self) -> Arr:
        return Arr([-it for it in self._elem], self._dim.copy())

    def __mod__(self, other: Any) -> Arr:
        return self.__apply(other, mod)

    def __rmod__(self, other: Any) -> Arr:
        return self.__apply(other, lambda x, y: y % x)

    def __lt__(self, other: Any) -> Arr:
        return self.__apply(other, lt)

    def __gt__(self, other: Any) -> Arr:
        return self.__apply(other, gt)

    def __le__(self, other: Any) -> Arr:
        return self.__apply(other, le)

    def __ge__(self, other: Any) -> Arr:
        return self.__apply(other, ge)

    def __eq__(self, other: Any) -> Arr:
        return self.__apply(other, eq)

    def __ne__(self, other: Any) -> Arr:
        return self.__apply(other, ne)

    def __and__(self, other: Any) -> Arr:
        return self.__apply(other, and_)

    def __rand__(self, other: Any) -> Arr:
        return self.__and__(other)

    def __or__(self, other: Any) -> Arr:
        return self.__apply(other, or_)

    def __ror__(self, other: Any) -> Arr:
        return self.__or__(other)

    # Invert operator will act as a boolean negation, which is NOT its original functionality.
    # Since Python does not allow the overriding of keyword 'not', we use __invert__ as a detour.
    def __invert__(self) -> Arr:
        return Arr([~it for it in self._elem], self._dim.copy())

    def __getitem__(self, item: int) -> Any:
        return self._elem[item]

    def __setitem__(self, key: int, value: Any):
        self._elem[key] = value

    def __len__(self) -> int:
        return self._dim[0]

    def __deepcopy__(self, memodict: Dict = {}) -> Arr:
        return Arr(deepcopy(self._elem), self._dim.copy())

    def __next__(self):
        if self._curr >= len(self._elem):
            raise StopIteration

        it = self._elem[self._curr]
        self._curr += 1

        return it

    def __iter__(self):
        self._curr = 0

        return self

    def __str__(self) -> str:
        return 'Arr' + str(self._elem)

    __repr__ = __str__

    """
    INDEXING LOGIC
    
    It supports three types of indexing modes: indexing all, indexing by index list, and indexing by a single index.
        1. Indexing all: a[] means indexing all elements in a.
        2. Indexing by index list: a[[i1, ..., ip]] means indexing elements of a at i1, ..., ip.
        3. Indexing by a single index: a[i] means indexing a single element of a at i.
    Here, a is one of array, matrix, or vector.
    Since the first two indexing modes yield multiple elements, they should be packed up in array (or matrix or vector)
    and thus there is no dimension drop.
    The last one, however, does have a dimension drop since it extracts a single element.
    
    Further, indexing can be chained. That is, a[i1, ..., ip] is allowed and means:
    First, index from a using i1. Then index from each of previously indexed items using i2, and so on.
        
    Summarizing, we define index chain and indexing rule as follows:
        idx_chain = None, idx_chain
                  | [i1, ..., ip], idx_chain
                  | i, idx_chain
                  | Nil
                  
        1. Idx(a, [None]) => a                                                                    [IdxAllBase]
        2. Idx(a, [[i1, ..., ip]]) => [ai1, ..., aip]                                             [IdxListBase]
        3. Idx(a, [i]) => ai                                                                      [IdxSnglBase]
        4. Idx(a, [None, idx_chain]) => [Idx(a1, idx_chain), ..., Idx(ap, idx_chain)]             [IdxAll]
        5. Idx(a, [[i1, ..., ip], idx_chain]) => [Idx(ai1, idx_chain), ..., Idx(aip, idx_chain)]  [IdxList]
        6. Idx(a, [i, idx_chain]) => Idx(ai, idx_chain)                                           [IdxSngl]
    Here, a = [a1, ..., aq].
    """

    def get(self, idx: List) -> Any:
        """
        Indexes using index chain idx.

        Naive implementation of all six rules is trivial but quite laborious.
        As a simple trick, it uses the fact that for array a which has depth(# of dimension) d,
        and index chain idx_chain of length l (<= d), a[idx_chain] = a[idx_chain, None, ... None (d - l of Nones)].
        Utilizing this, we can delegate the implementation of base cases to Vec class.
        Here, other indexing rules are implemented.
        Note that Mat class does not need to override this since it has the same logical structure.

        Promotion may be needed if the length of index chain exceeds the depth of an array.
        One tricky case is the case where base type is indexed.
        However, since base types are not subclasses of Arr, this case should be handled outside of this module.
        Operator module will do this.

        Float can be used as an index, and it will be rounded.
        However, this may cause unexpected behaviors due to rounding.

        :param idx: Index chain.

        :return: Indexed elements.

        :raise ArrErr[EMPTY_IDX]: If index list is empty.
        :raise ArrErr[IDX_BOUND]: If index is out of bound.
        """
        if len(idx) > self.dept:
            return self.promote(len(idx) - self.dept).get(idx)
        elif len(idx) < self.dept:
            idx += [None] * (self.dept - len(idx))

        if idx[0] is None:
            # [IdxAll]
            res = [it.get(idx[1:]) for it in self._elem]

            if type(res[0]) == Vec:
                return Mat(res, [len(res), *res[0].dim])
            elif type(res[0]) == Mat or type(res[0]) == Arr:
                return Arr(res, [len(res), *res[0].dim])
            else:
                return Vec(res)
        elif type(idx[0]) == Vec:
            # [IdxList]
            idx_set: Vec = idx[0]
            res: List = []

            if len(idx_set) == 0:
                raise ArrErr(Errno.EMPTY_IDX)

            for i in idx_set:
                i = round(i)

                if i < 0 or i >= self._dim[0]:
                    raise ArrErr(Errno.IDX_BOUND, idx=i)

                res.append(self._elem[i].get(idx[1:]))

            if type(res[0]) == Vec:
                return Mat(res, [len(res), *res[0].dim])
            elif type(res[0]) == Mat or type(res[0]) == Arr:
                return Arr(res, [len(res), *res[0].dim])
            else:
                return Vec(res)
        else:
            # [IdxSngl]
            i: int = round(idx[0])

            if i < 0 or i >= self._dim[0]:
                raise ArrErr(Errno.IDX_BOUND, idx=i)

            return self._elem[i].get(idx[1:])

    """
    UPDATING LOGIC
    
    It supports updating elements of an array and its subclasses using indexing modes described above.
    This functionality will be used to implement assignment.
    
    Like operators acting b/w arrays (and its subclasses) it supports two types of update: distributive update and
    componentiwe update.
    Updating rules are as follows:
        1. Up(a, [None], b) => [b, ..., b].                                                   [UpIdxAllDistBase]
        2. Up(a, [None, idx_chain], b) => Up(ai, [idx_chain], b) for all i.                   [UpIdxAllDist]
        3. Up(a, [[i1, ..., ip]], b) => a whose elements at i1, ..., ip are replaced with b.  [UpIdxListDistBase]
        4. Up(a, [[i1, ..., ip], idx_chain], b) => Up(aij, [idx_chain], b) for all j.         [UpIdxListDist]
        5. Up(a, [None], c) => [c1, ..., cq].                                                 [UpIdxAllCompBase]
        6. Up(a, [None, idx_chain], c) => Up(ai, [idx_chain], ci) for all i.                  [UpIdxAllComp]
        7. Up(a, [[i1, ..., ip]], c) => a whose elements at ij are replaced with cj.          [UpIdxListCompBase]
        8. Up(a, [[i1, ..., ip], idx_chain], c) => Up(aij, [idx_chain], cj) for all j.        [UpIdxListComp]
        9. Up(a, [i], d) => a whose element at i is replaced with d.                          [UpIdxSnglBase]
        10. Up(a, [i, idx_chain], d) => Up(ai, [idx_chain], d).                               [UpIdxSngl]
    Here, b is a base type object, a = [a1, ... , aq], and c = [c1, ..., cq].
    Rules are applied following the order as above.
    """

    def update(self, idx: List, val: Any) -> Any:
        """
        Updates elements indicated by idx to val.

        Naive implementation of all ten rules is trivial but very laborious.
        As in Arr.get, it delegates the implementation of base cases to Vec class.
        Here, other five rules are implemented.

        Promotion of self may be needed if the length of index chain exceeds the depth of an array.
        Promotion of val may be needed if distributive rules are applied and
        the depth of indexing result exceeds the depth of val.
        Unlike the promotion of self, that of val is tricky since it needs information on the indexing result.
        Fortunately, the depth of indexing result can be inferred by semantic checker 'before' interpretation.
        Since such information is invisible here, promotion of val will be handled outside of this module.
        It just assumes that val is already promoted properly.
        Like Arr.get, updating base type by indexing it is another tricky problem.
        This will be also handled outside of this module. Interp class will do this.

        Float can be used as an index, and it will be rounded.
        However, this may cause unexpected behaviors due to rounding.

        :param idx: Index chain.
        :param val: Value to be assigned.

        :return: Updated array.

        :raise ArrErr[EMPTY_IDX]: If index list is empty.
        :raise ArrErr[IDX_BOUND]: If index is out of bound.
        :raise ArrErr[ASGN_N_MISS]: If # indices of index list does not match with # of items in val in
                                    componentwise case.
        """
        if len(idx) > self.dept:
            return self.promote(len(idx) - self.dept).update(idx, val)
        elif len(idx) < self.dept:
            idx += [None] * (self.dept - len(idx))

        if isinstance(val, Arr):
            if idx[0] is None:
                # [UpIdxAllComp]
                if self._dim[0] != len(val):
                    raise ArrErr(Errno.ASGN_N_MISS, need=self._dim[0], given=len(val))

                return Arr([self._elem[i].update(idx[1:], val[i]) for i in range(self._dim[0])], self._dim.copy())
            elif type(idx[0]) == Vec:
                # [UpIdxListComp]
                idx_set: Vec = idx[0]
                elem: List = deepcopy(self._elem)

                # TODO: Empty index?
                if len(idx_set) != len(val):
                    raise ArrErr(Errno.ASGN_N_MISS, need=len(idx_set), given=len(val))

                for i in range(len(idx_set)):
                    j = round(idx_set[i])

                    if j < 0 or j >= self._dim[0]:
                        raise ArrErr(Errno.IDX_BOUND, idx=j)

                    elem[j] = elem[j].update(idx[1:], val[i])

                return Arr(elem, self._dim.copy())
            else:
                # [UpIdxSngl]
                i: int = round(idx[0])
                elem: List = deepcopy(self._elem)

                if i < 0 or i >= self._dim[0]:
                    raise ArrErr(Errno.IDX_BOUND, idx=i)

                elem[i] = elem[i].update(idx[1:], val)

                return Arr(elem, self._dim.copy())
        else:
            if idx[0] is None:
                # [UpIdxAllDist]
                return Arr([it.update(idx[1:], val) for it in self._elem], self._dim.copy())
            elif type(idx[0]) == Vec:
                # [UpIdxListDist]
                idx_set: Vec = idx[0]
                elem: List = deepcopy(self._elem)

                for i in range(len(idx_set)):
                    j = round(idx_set[i])

                    if j < 0 or j >= self._dim[0]:
                        raise ArrErr(Errno.IDX_BOUND, idx=j)

                    elem[j] = elem[j].update(idx[1:], val)

                return Arr(elem, self._dim.copy())
            else:
                # [UpIdxSngl]
                i: int = round(idx[0])
                elem: List = deepcopy(self._elem)

                if i < 0 or i >= self._dim[0]:
                    raise ArrErr(Errno.IDX_BOUND, idx=i)

                elem[i] = elem[i].update(idx[1:], val)

                return Arr(elem, self._dim.copy())

    """
    PROMOTION & DEGRADATION LOGIC
    
    Promotion is wrapping an object with additional redundant dimensions.
    And degradation is stripping those redundant dimensions.
    
    Numeric(scala) can be considered as a vector of length 1.
    Vector of length n can be considered as a matrix of size 1 by n. (Note that we employ row-major policy.)
    Similarly, m by n matrix can be considered as an array with dimension 1 by m by n.
    This mathematical concept is supported with help of these promotion & degradation logic.
    """

    def promote(self, n: int) -> Arr:
        """
        Promotes an array n times.

        Promoting d1 by ... by dp array n times yields 1 by ... by 1 (n of 1s) by d1 by ... by dp array.

        :param n: # of promotions to be applied.

        :return: Promoted array.
        """
        res: Arr = self

        while n > 0:
            res = Arr([res], [1, *res._dim])
            n -= 1

        return res

    def degrade(self, n: int) -> Any:
        """
        Degrades an array n times.

        Degrading 1 by ... by 1 (m of 1s) by ... array n(<=m) times yields 1 by ... by 1 (m - n of 1s) by ... array.
        Note that when # of dimensions becomes less than 3, it returns a matrix or vector, not array.
        Also, it does NOT check whether the dimension to be stripped is actually redundant or not.

        :param n: # of degradations to be applied.

        :return: Degraded array.
        """
        res: Arr = self

        while n > 0:
            res = self._elem[0]
            n -= 1

            if type(res) == Mat:
                return res.degrade(n)

        return res

    """
    APPLICATION LOGIC
    
    The spirit of array, matrix, and vector operations is supported by these logic.
    As its name implies, it applies the given operation componentwisely or distributively.
    
    Application rules for binary operator op are as follows:
        1. [a1, ..., ap] op [b1, ..., bp] => [a1 op b1, ..., ap op bp].           [BinOpComp]
        2. [a1, ..., ap] op b => [a1 op b, ..., ap op b] if b is of 'unit' of op. [BinOpDist]
    Rules are applied following the order as above.
    Here, 'unit' is the smallest type st. the operation is defined.
    For most binary operators, unit is numeric. However, matrix multiplication has matrix as its unit.
        
    Application rule for unary operator op is as follows:
        1. op [a1, ..., ap] => [op a1, ..., op ap]. [UniOpComp]
        
    Since rule [UniOpComp] is relatively simple, [UniOpComp] is directly implemented in built-in overriding above.
    Rules for binary operators, however, are implemented here separately.
    
    Subclasses also override this application logic.
    Considering the overriding of application logic and built-ins, we can roughly draw following case-by-case scenarios.
        a op a    [*]    Vec op a    [Vec]  Mat op a    [Mat]  Arr op a    [Arr]
        a op Vec  [Vec]  Vec op Vec  [Vec]  Mat op Vec  [Mat]  Arr op Vec  [Arr]
        a op Mat  [Mat]  Vec op Mat  [Mat]  Mat op Mat  [Mat]  Arr op Mat  [Arr]
        a op Arr  [Arr]  Vec op Arr  [Arr]  Mat op Arr  [Arr]  Arr op Arr  [Arr]
    Here, a stands for base type like numeric and the class in bracket indicates the class responsible for
    handling the corresponding case.
    Note that a op a cannot be handled by classes in this module, thus it should be handled somewhere else.
    Operator module will do this.
    
    This logic is for internal use only.
    """

    def __apply(self, other: Any, op: Callable) -> Arr:
        """
        Applies binary operator op.

        Parameter self and other are considered as LHS and RHS, resp.
        Following cases are to be handled.
            1. a op Arr   => Arr rop a
            2. Vec op Arr => Arr rop Vec
            3. Mat op Arr => Arr rop Mat
            4. Arr op a
            5. Arr op Vec
            6. Arr op Mat
            7. Arr op Arr
        For case 1 through 3, self is actually RHS and other is LHS.
        However, this does NOT matter since those cases call this function with rop instead of op.
        (rop is 'reversed' version of op: x rsub y is y - x)
        Thus the first three cases reduce to case 4, 5, and 6, resp.
        For case 4, rule [BinOpDist] will be applied and for case 5 and 6, rule [BinOpComp] will be applied
        with promotion, if needed.

        :param other: RHS.
        :param op: Operator to be applied.

        :return: Result.

        :raise ArrErr[DIM_MISMATCH]: If # of elements does not match during applying rule [BinOpComp].
        """
        if isinstance(other, Arr):
            # [BinOpComp]
            if self.dept > other.dept:
                return op(self, other.promote(self.dept - other.dept))
            elif self.dept < other.dept:
                return op(self.promote(other.dept - self.dept), other)

            if self._dim[0] != other._dim[0]:
                raise ArrErr(Errno.DIM_MISMATCH, op='componentwise binary operation', dim1=str(self._dim),
                             dim2=str(other._dim))

            return Arr([op(self._elem[i], other._elem[i]) for i in range(self._dim[0])], self._dim.copy())
        else:
            # [BinOpDist]
            return Arr([op(it, other) for it in self._elem], self._dim.copy())

    def __apply_matmul(self, other: Any, op: Callable) -> Arr:
        """
        Applies matrix multiplication operator op.

        Since matrix multiplication has matrix as its unit, application logic for it needs a special treat.
        Unlike Arr.__apply, rule [BinOpDist] will be applied to case 4 through 6
        and rule [BinOpComp] will be applied to case 7.
        Other logical structure is the same as Arr.__apply.

        :param other: RHS.
        :param op: Matrix multiplication operator. Must be one of matmul or rmatmul(lambda expr).

        :return: Result.

        :raise ArrErr[DIM_MISMATCH]: If # of elements does not match during applying rule [BinOpComp].
        """

        if type(other) == Arr:
            # [BinOpComp]
            if self.dept > other.dept:
                return op(self, other.promote(self.dept - other.dept))
            elif self.dept < other.dept:
                return op(self.promote(other.dept - self.dept), other)

            if self._dim[0] != other._dim[0]:
                raise ArrErr(Errno.DIM_MISMATCH, op='componentwise binary operation', dim1=str(self._dim),
                             dim2=str(other._dim))

            elem: List = [op(self._elem[i], other._elem[i]) for i in range(self._dim[0])]
            dim: List[int] = [self._dim[0], *elem[0].dim]
        else:
            # [BinOpDist]
            elem: List = [op(it, other) for it in self._elem]
            dim: List[int] = [self._dim[0], *elem[0].dim]

        return Arr(elem, dim)

    """
    FORMATTING LOGIC
    
    Cumbersome logic to print array (and its subclasses) prettily.
    """

    # TODO: Exceeding case?
    @staticmethod
    def __format_hlpr(elem: Arr, pos: List[int], w: int, h: int, it_w: int) -> Tuple[str, int]:
        if h <= 0:
            return '', h

        if type(elem) == Mat:
            d_name: str = ', '.join(map(str, pos)) + ', ,\n'
            buf, h = elem.format(w, h - 1, it_w, True)

            return d_name + buf + '\n\n', h - 1
        else:
            buf: str = ''

            for i in range(len(elem)):
                it_str, h = Arr.__format_hlpr(elem[i], pos + [i], w, h, it_w)
                buf += it_str

            return buf, h

    # TODO: Exceeding case?
    def format(self, w: int, h: int, it_w: int, h_remain: bool = False) -> Union[str, Tuple[str, int]]:
        if self._dim[-1] == 0:
            buf: str = 'Empty array with dimension ' + ' by '.join(map(str, self._dim))

            return (buf, h - 1) if h_remain else buf

        res, h = self.__format_hlpr(self, [], w, h, it_w)

        return (res.rstrip(), h) if h_remain else res.rstrip()

    """
    UTIL
    """

    # TODO: Need update?
    def append(self, v: Any) -> Arr:
        """
        Appends v as an element.

        Two types of appending are supported.
        One is appending a single object, and the other is appending multiple objects.
        In case of appending multiple objects, v should be a list (NOT vector) of objects to be appended.

        Note that this function does NOT check the validity of v.
        Wrongly passed v can corrupt the whole structure of the original array (or its subclasses).
        The user must use this function with extra care.

        :param v: Object or list of objects to be appended.

        :return: Array (or its subclasses) after appending.
        """
        if type(v) == list:
            self._elem += v
            self._dim[0] += len(v)
        else:
            self._elem.append(v)
            self._dim[0] += 1

        return self

    """
    GETTER & SETTER
    """

    @property
    def elem(self) -> List:
        return self._elem

    @property
    def dim(self) -> List[int]:
        return self._dim

    @property
    def dept(self) -> int:
        return len(self._dim)


class Mat(Arr):
    """
    Matrix class.

    Represents matrix.
    Matrix should contain vectors as its elements.
    One should not assign base types as elements or matrix.
    Use vector in that case.

    All exceptions raised here should be caught by Interp class.
    Then the erroneous position in the raw input string with the string itself should be properly assigned.
    """
    # Block size for parallel matrix multiplication.
    # Refer to the comments of CLib.GEMM.
    __BLK_SZ: Final[int] = 500

    def __init__(self, elem: List, dim: List[int]) -> None:
        super().__init__(elem, dim)

    """
    BUILT-IN OVERRIDING
    """

    def __add__(self, other: Any) -> Mat:
        return self.__apply(other, add)

    def __radd__(self, other: Any) -> Mat:
        return self.__add__(other)

    def __sub__(self, other: Any) -> Mat:
        return self.__apply(other, sub)

    def __rsub__(self, other: Any) -> Mat:
        return self.__apply(other, lambda x, y: y - x)

    def __mul__(self, other: Any) -> Mat:
        return self.__apply(other, mul)

    def __rmul__(self, other: Any) -> Mat:
        return self.__mul__(other)

    def __matmul__(self, other: Any) -> Mat:
        """
        Multiplies two matrices.

        There are following cases where this function is being called:
            1. Mat %*% a where a is base type.
            2. Mat %*% Vec.
            3. Mat %*% Mat.
        For case 1 and 2, matrix multiplication is valid iff self has only one column.
        For case 3, matrix multiplication is valid iff # of columns in self and # of rows in other are equal.
        Call of this function with array as other should be rejected.

        :param other: RHS.

        :return: self %*% other.

        :raise ArrErr[DIM_MISMATCH]: If dimensions of two matrices are not compatible for matrix multiplication.
        """
        if type(other) == Arr:
            return NotImplemented

        if type(other) == Vec:
            if self._dim[1] != 1:
                raise ArrErr(Errno.DIM_MISMATCH, op='matrix multiplication', dim1=str(self._dim), dim2=str(other.dim))

            return Mat([self._elem[i] * other[i] for i in range(self._dim[0])], [self._dim[0], len(other)])
        elif type(other) == Mat:
            if self._dim[1] != other._dim[0]:
                raise ArrErr(Errno.DIM_MISMATCH, op='matrix multiplication', dim1=str(self._dim), dim2=str(other._dim))

            return CLib.GEMM(self, other, Mat.__BLK_SZ)
        else:
            if self._dim[1] != 1:
                raise ArrErr(Errno.DIM_MISMATCH, op='matrix multiplication', dim1=str(self._dim), dim2='0(base type)')

            return Mat([it * other for it in self._elem], [self._dim[0], 1])

    def __rmatmul__(self, other: Any) -> Mat:
        """
        Multiplies two matrices.

        There are following cases where this function is being called:
            1. a %*% Mat where a is a base type.
            2. Vec %*% Mat.
        For case 1, matrix multiplication is valid iff self has only one row.
        For case 2, matrix multiplication is valid iff # of rows in self and length of other are equal.
        Call of this function with array as other should be rejected.

        :param other: LHS.

        :return: other %*% self.

        :raise ArrErr[DIM_MISMATCH]: If dimensions of two matrices are not compatible for matrix multiplication.
        """
        if type(other) == Arr:
            return NotImplemented

        # TODO: Optimization
        if type(other) == Vec:
            if self._dim[0] != len(other):
                raise ArrErr(Errno.DIM_MISMATCH, op='matrix multiplication', dim1=str(self._dim),
                             dim2=str([1, len(other)]))

            return CLib.GEMM(other.promote(1), self, Mat.__BLK_SZ)
        else:
            if self._dim[0] != 1:
                raise ArrErr(Errno.DIM_MISMATCH, op='matrix multiplication', dim1=str(self._dim), dim2='0(base type)')

            return Mat([other * self._elem[0]], [1, self._dim[1]])

    def __truediv__(self, other: Any) -> Mat:
        return self.__apply(other, truediv)

    def __rtruediv__(self, other: Any) -> Mat:
        return self.__apply(other, lambda x, y: y / x)

    def __floordiv__(self, other: Any) -> Mat:
        return self.__apply(other, floordiv)

    def __rfloordiv__(self, other: Any) -> Mat:
        return self.__apply(other, lambda x, y: y // x)

    def __pow__(self, other: Any) -> Mat:
        return self.__apply(other, pow)

    def __rpow__(self, other: Any) -> Mat:
        return self.__apply(other, lambda x, y: y ** x)

    def __neg__(self) -> Mat:
        return Mat([-it for it in self._elem], self._dim.copy())

    def __mod__(self, other: Any) -> Mat:
        return self.__apply(other, mod)

    def __rmod__(self, other: Any) -> Mat:
        return self.__apply(other, lambda x, y: y % x)

    def __lt__(self, other: Any) -> Mat:
        return self.__apply(other, lt)

    def __gt__(self, other: Any) -> Mat:
        return self.__apply(other, gt)

    def __le__(self, other: Any) -> Mat:
        return self.__apply(other, le)

    def __ge__(self, other: Any) -> Mat:
        return self.__apply(other, ge)

    def __eq__(self, other: Any) -> Mat:
        return self.__apply(other, eq)

    def __ne__(self, other: Any) -> Mat:
        return self.__apply(other, ne)

    def __and__(self, other: Any) -> Mat:
        return self.__apply(other, and_)

    def __rand__(self, other: Any) -> Mat:
        return self.__and__(other)

    def __or__(self, other: Any) -> Mat:
        return self.__apply(other, or_)

    def __ror__(self, other: Any) -> Mat:
        return self.__or__(other)

    # Refer to the comments of Arr.__invert__.
    def __invert__(self) -> Mat:
        return Mat([~it for it in self._elem], self._dim.copy())

    def __deepcopy__(self, memodict: Dict = {}) -> Mat:
        return Mat(deepcopy(self._elem), self._dim.copy())

    def __str__(self) -> str:
        return 'Mat' + str(self._elem)

    __repr__ = __str__

    """
    UPDATING LOGIC

    Refer to the comments of Arr class.
    """

    def update(self, idx: List, val: Any) -> Any:
        """
        Updates elements indicated by idx to val.

        For details, refer to the comments of Arr.update.
        Note that Mat class cannot just inherit update method from Arr class because the return types are different.

        :param idx: Index chain.
        :param val: Value to be assigned.

        :return: Updated matrix.

        :raise ArrErr[EMPTY_IDX]: If index list is empty.
        :raise ArrErr[IDX_BOUND]: If index is out of bound.
        :raise ArrErr[ASGN_N_MISS]: If # indices of index list does not match with # of items in val in
                                    componentwise case.
        """
        if len(idx) > 2:
            return self.promote(len(idx) - 1).update(idx, val)
        elif len(idx) < 2:
            idx += [None]

        if isinstance(val, Mat):
            if idx[0] is None:
                # [UpIdxAllComp]
                if self._dim[0] != len(val):
                    raise ArrErr(Errno.ASGN_N_MISS, need=self._dim[0], given=len(val))

                return Mat([self._elem[i].update(idx[1:], val[i]) for i in range(self._dim[0])], self._dim.copy())
            elif type(idx[0]) == Vec:
                # [UpIdxListComp]
                idx_set: Vec = idx[0]
                elem: List = deepcopy(self._elem)

                if len(idx_set) != len(val):
                    raise ArrErr(Errno.ASGN_N_MISS, need=len(idx_set), given=len(val))

                for i in range(len(idx_set)):
                    j = round(idx_set[i])

                    if j < 0 or j >= self._dim[0]:
                        raise ArrErr(Errno.IDX_BOUND, idx=j)

                    elem[j] = elem[j].update(idx[1:], val[i])

                return Mat(elem, self._dim.copy())
            else:
                # [UpIdxSngl]
                i: int = round(idx[0])
                elem: List = deepcopy(self._elem)

                if i < 0 or i >= self._dim[0]:
                    raise ArrErr(Errno.IDX_BOUND, idx=i)

                elem[i] = elem[i].update(idx[1:], val)

                return Mat(elem, self._dim.copy())
        else:
            if idx[0] is None:
                # [UpIdxAllDist]
                return Mat([it.update(idx[1:], val) for it in self._elem], self._dim.copy())
            elif type(idx[0]) == Vec:
                # [UpIdxListDist]
                idx_set: Vec = idx[0]
                elem: List = deepcopy(self._elem)

                for i in range(len(idx_set)):
                    j = round(idx_set[i])

                    if j < 0 or j >= self._dim[0]:
                        raise ArrErr(Errno.IDX_BOUND, idx=j)

                    elem[j] = elem[j].update(idx[1:], val)

                return Mat(elem, self._dim.copy())
            else:
                # [UpIdxSngl]
                i: int = round(idx[0])
                elem: List = deepcopy(self._elem)

                if i < 0 or i >= self._dim[0]:
                    raise ArrErr(Errno.IDX_BOUND, idx=i)

                elem[i] = elem[i].update(idx[1:], val)

                return Mat(elem, self._dim.copy())

    """
    PROMOTION & DEGRADATION LOGIC

    Refer to the comments of Arr class.
    """

    def promote(self, n: int) -> Arr:
        return Arr([self], [1, *self._dim]).promote(n - 1) if n >= 1 else self

    def degrade(self, n: int) -> Arr:
        return self._elem[0].degrade(n - 1) if n > 0 else self

    """
    APPLICATION LOGIC

    Refer to the comments of Arr class.
    This logic is for internal use only.
    """

    def __apply(self, other: Any, op: Callable) -> Mat:
        """
        Applies binary operator op.

        For detail, refer to the comments of Arr.__apply.
        Note that call of this function with array as other should be rejected.

        :param other: RHS.
        :param op: Operator to be applied.

        :return: Result.

        :raise ArrErr[DIM_MISMATCH]: If # of elements does not match during applying rule [BinOpComp].
        """
        if type(other) == Arr:
            return NotImplemented

        if type(other) == Vec:
            return op(self, other.promote(1))
        elif type(other) == Mat:
            # [BinOpComp]
            if self._dim[0] != other._dim[0]:
                raise ArrErr(Errno.DIM_MISMATCH, op='componentwise binary operation', dim1=str(self._dim),
                             dim2=str(other._dim))

            return Mat([op(self._elem[i], other._elem[i]) for i in range(self._dim[0])], self._dim.copy())
        else:
            # [BinOpDist]
            return Mat([op(it, other) for it in self._elem], self._dim.copy())

    """
    FORMATTING LOGIC
    """

    def format(self, w: int, h: int, it_w: int, h_remain: bool = False) -> Union[str, Tuple[str, int]]:
        """
        Formats matrix.


        The first line of the formatted string shows column indices.
        Then starting from the second line, elements of a matrix will be formatted row by row,
        with the corresponding row index leading each line.

        Regarding the size of a matrix, there are four possible scenarios:
            1. A matrix is small enough to fit in the given width w and height h.
            2. A matrix has too many columns so that the given w is not enough to format all columns.
            3. A matrix has too may rows so that the given h is not enough to format all rows.
            4. A matrix has too many rows & columns so that it cannot fit in the given w and h.
        The first case has no problem. For the last two cases, elements which cannot be formatted will be omitted.
        For the second case, the original matrix will be blocked into two parts:
        one with columns lying within the given w and one with the exceeding columns.
        Then the formatted string of the first block will be followed by that of the second block.
        If the second block has exceeding columns again,
        the procedure above will be applied continuously until the given h exhausts.

        In any cases, if there are any omitted elements,
        a line presenting # of omitted elements will be attached at the end.
        Empty matrix will be formatted as 'Empty matrix with dimension m by 0'.

        For details, refer to the comments of Vec.format.

        :param w: Width of the output.
        :param h: Height of the output.
        :param it_w: Maximum width of an element.
        :param h_remain: If true, it returns # of used lines. (Default: False)

        :return: Formatted string.
        """
        if self._dim[-1] == 0:
            buf: str = f'Empty matrix with dimension {self._dim[0]} by 0'

            return (buf, h - 1) if h_remain else buf

        # [Step 1]
        buf: str = ''
        # Computes the upper limit for # of columns which will be actually formatted.
        # For details, refer to the comments of Vec.format.
        c_cnt: int = min(ceil(w / 3), self._dim[1])
        # The exact # of rows to be formatted can be determined easily: it is just min(h - 1, p) where p is # of rows.
        m: int = min(h - 1, self._dim[0])

        # For case 2 described above,
        # the # of blocks which will be actually formatted cannot exceed ceil(h/p) where p is # of rows.
        # Therefore, # of columns which will be actually formatted cannot exceed ceil(h/p) * ceil(w/3).
        if h > self._dim[0]:
            c_cnt *= ceil(h / self._dim[0])
            c_cnt = min(c_cnt, self._dim[1])

        pool: List[List[Optional[str]]] = [[None for _ in range(c_cnt)] for _ in range(m)]
        qt: bool = (type(self._elem[0][0]) == str)
        # Refer to the comments of Vec.format.
        it_w, mat_it_w = 0, it_w - 2 * qt

        for i in range(m):
            for j in range(c_cnt):
                it_str: str = str(self._elem[i][j])

                if len(it_str) > mat_it_w:
                    it_str = it_str[:mat_it_w - 3] + '...'

                it_w = max(it_w, len(it_str))
                pool[i][j] = it_str

        # [Step 2]
        # Given m, the row indices preceding each line will be 0, 1, ..., (m - 1).
        # The largest width among them is achieved by the last one
        # and note that there should be enclosing brackets with a comma.
        r_idx_w: int = len(str(m - 1)) + 3
        # In determination of the element width, we should consider column indices.
        # Column index grows from 0 to (c_cnt - 1), and thus the largest width is achieved by c_cnt.
        # Also note that like row indices, there show be enclosing brackets with a comma.
        # Here, we do not consider the case where there are TOO MANY columns (>= 10^7)
        # since those columns cannot be formatted anyhow.
        # (Unless one sets w or h as very large values. Just don't do that...)
        it_w = max(it_w, len(str(c_cnt - 1)) + 3)
        # Refer to the comments of Vec.format.
        n: int = floor(w / (it_w + 2))
        # Given m and n, we can determine the exact # of blocks for case 2.
        # It will be given as ceil(q/n) where q is # of columns but should not exceed ceil((h - 1)/(m + 1)).
        # Here, (m + 1) accounts for one additional line for column indices
        # and (h - 1) is a little trick to prevent the last line being column indices.
        l: int = min(ceil((h - 1) / (m + 1)), ceil(self._dim[1] / n))
        k: int = 0

        # [Step 3]
        while k < l - 1:
            buf += ' ' * r_idx_w

            for j in range(n):
                buf += ('[,' + str(n * k + j) + ']').rjust(it_w + 2 * qt + 2)

            buf += '\n'
            i: int = 0

            while i < m:
                j: int = 0
                buf += ('[' + str(i) + ',]').rjust(r_idx_w)

                while j < n:
                    buf += ('"' * qt + pool[i][j + k * n] + '"' * qt).rjust(it_w + 2 * qt + 2)

                    j += 1

                buf += '\n'
                i += 1

            k += 1

        buf += ' ' * r_idx_w

        for j in range(min(n, self._dim[1] - n * (l - 1))):
            buf += ('[,' + str(n * (l - 1) + j) + ']').rjust(it_w + 2 * qt + 2)

        buf += '\n'
        i: int = 0

        while i < min(m, h - m * l + m - l):
            j: int = 0
            buf += ('[' + str(i) + ',]').rjust(r_idx_w)

            while j < min(n, self._dim[1] - n * (l - 1)):
                buf += ('"' * qt + pool[i][j + (l - 1) * n] + '"' * qt).rjust(it_w + 2 * qt + 2)

                j += 1

            buf += '\n'
            i += 1

        resi: int = self._dim[0] * self._dim[1] - (l - 1) * m * n
        resi -= min(m, h - m * l + m - l) * min(n, self._dim[1] - n * (l - 1))
        h_use: int = m * l + l - m + min(m, h - m * l + m - l)

        # [Step 4]
        if resi > 0:
            buf.rstrip()
            buf += f'\n... and {resi} more elements in this matrix.'
            h_use += 1

        return (buf.rstrip(), h - h_use) if h_remain else buf.rstrip()

    """
    UTIL
    """
    # TODO: Need update?

    def rbind(self, v: Mat) -> Mat:
        if type(v) == Vec:
            self.append(v)
        else:
            self.append(v.elem)

        return self

    def cbind(self, v: Mat) -> Mat:
        if type(v) == Vec:
            for i in range(self._dim[0]):
                self._elem[i].append(v[i])

            self._dim[1] += 1
        else:
            for i in range(self._dim[0]):
                self._elem[i].append(v[i].elem)

            self._dim[1] += v._dim[1]

        return self

    """
    GETTER & SETTER
    """

    @property
    def nrow(self) -> int:
        return self._dim[0]

    @property
    def ncol(self) -> int:
        assert type(self) == Mat

        return self._dim[1]

    @property
    def is_sqr(self) -> bool:
        return self._dim[0] == self._dim[1]


@final
class Vec(Mat):
    """
    Vector class.

    Represents vector.
    Vector should contain base types as its elements.

    All exceptions raised here should be caught by Interp class.
    Then the erroneous position in the raw input string with the string itself should be properly assigned.

    This class is the end of inheritance. No further inheritance is allowed.
    """

    def __init__(self, elem: List) -> None:
        super().__init__(elem, [len(elem)])

    """
    BUILT-IN OVERRIDING
    """

    def __add__(self, other: Any) -> Vec:
        return self.__apply(other, add)

    def __radd__(self, other: Any) -> Vec:
        return self.__add__(other)

    def __sub__(self, other: Any) -> Vec:
        return self.__apply(other, sub)

    def __rsub__(self, other: Any) -> Vec:
        return self.__apply(other, lambda x, y: y - x)

    def __mul__(self, other: Any) -> Vec:
        return self.__apply(other, mul)

    def __rmul__(self, other: Any) -> Vec:
        return self.__mul__(other)

    def __matmul__(self, other: Any) -> Mat:
        """
        Multiplies two matrices.

        There are two cases where this function is being called.
            1. Vec %*% a where a is a base type.
            2. Vec %*% Vec.
        For either case, matrix multiplication is valid iff self is a vector or length 1.
        Call of this function with array or matrix as other should be rejected.

        :param other: RHS.

        :return: self %*% other.

        :raise ArrErr[DIM_MISMATCH]: If dimensions of two matrices are not compatible for matrix multiplication.
        """
        if type(other) == Mat or type(other) == Arr:
            return NotImplemented

        if self._dim[0] != 1:
            raise ArrErr(Errno.DIM_MISMATCH, op='matrix multiplication', dim1=str(self._dim),
                         dim2=str(other._dim) if type(other) == Vec else '0(base type)')

        return Vec([self._elem[0] * other]).promote(1) if type(other) == Vec else Vec([self * other]).promote(1)

    def __rmatmul__(self, other: Any) -> Mat:
        """
        Multiplies two matrices.

        The only case where this function is being called is a %*% Vec where a is a base type.
        In this case, matrix multiplication is always possible. So there is no dimension check.
        Call of this function with array or matrix as other should be rejected.

        :param other: LHS.

        :return: other %*% self.

        :raise ArrErr[DIM_MISMATCH]: If dimensions of two matrices are not compatible for matrix multiplication.
        """
        if type(other) == Mat or type(other) == Arr:
            return NotImplemented

        return Vec([self * other]).promote(1)

    def __truediv__(self, other: Any) -> Vec:
        return self.__apply(other, truediv)

    def __rtruediv__(self, other: Any) -> Vec:
        return self.__apply(other, lambda x, y: y / x)

    def __floordiv__(self, other: Any) -> Vec:
        return self.__apply(other, floordiv)

    def __rfloordiv__(self, other: Any) -> Vec:
        return self.__apply(other, lambda x, y: y // x)

    def __pow__(self, other: Any) -> Vec:
        return self.__apply(other, pow)

    def __rpow__(self, other: Any) -> Vec:
        return self.__apply(other, lambda x, y: y ** x)

    def __neg__(self) -> Vec:
        return Vec([-it for it in self._elem])

    def __mod__(self, other: Any) -> Vec:
        return self.__apply(other, mod)

    def __rmod__(self, other: Any) -> Vec:
        return self.__apply(other, lambda x, y: y % x)

    def __lt__(self, other: Any) -> Vec:
        return self.__apply(other, lt)

    def __gt__(self, other: Any) -> Vec:
        return self.__apply(other, gt)

    def __le__(self, other: Any) -> Vec:
        return self.__apply(other, le)

    def __ge__(self, other: Any) -> Vec:
        return self.__apply(other, ge)

    def __eq__(self, other: Any) -> Vec:
        return self.__apply(other, eq)

    def __ne__(self, other: Any) -> Vec:
        return self.__apply(other, ne)

    def __and__(self, other: Any) -> Vec:
        return self.__apply(other, and_)

    def __rand__(self, other: Any) -> Vec:
        return self.__and__(other)

    def __or__(self, other: Any) -> Vec:
        return self.__apply(other, or_)

    def __ror__(self, other: Any) -> Vec:
        return self.__or__(other)

    # Refer to the comments of Arr.__invert__.
    def __invert__(self) -> Vec:
        return Vec([not it for it in self._elem])

    def __deepcopy__(self, memodict: Dict = {}) -> Vec:
        return Vec(deepcopy(self._elem))

    def __str__(self) -> str:
        return 'Vec' + str(self._elem)

    __repr__ = __str__

    """
    INDEXING LOGIC

    Refer to the comments of Arr class.
    """

    def get(self, idx: List) -> Any:
        """
        Implements indexing rules.

        Here, base cases of indexing rules are implemented.
        For detail, refer to the comments of Arr.get.

        :param idx: Index chain.

        :return: Indexed elements.

        :raise ArrErr[EMPTY_IDX]: If index list is empty.
        :raise ArrErr[IDX_BOUND]: If index is out of bound.
        """
        if len(idx) > 1:
            return self.promote(len(idx) - 1).get(idx)

        if idx[0] is None:
            # [IdxAllBase]
            return Vec(deepcopy(self._elem))
        elif type(idx[0]) == Vec:
            # [IdxListBase]
            idx_set: Vec = idx[0]
            res: List = []

            if idx_set._dim[0] == 0:
                raise ArrErr(Errno.EMPTY_IDX)

            for i in idx_set._elem:
                i = round(i)

                if i < 0 or i >= self._dim[0]:
                    raise ArrErr(Errno.IDX_BOUND, idx=i)

                res.append(self._elem[i])

            return Vec(res)
        else:
            # [IdxSnglBase]
            i: int = round(idx[0])

            if i < 0 or i >= self._dim[0]:
                raise ArrErr(Errno.IDX_BOUND, idx=i)

            return self._elem[i]

    """
    UPDATING LOGIC

    Refer to the comments of Arr class.
    """

    def update(self, idx: List, val: Any) -> Any:
        """
        Updates elements indicated by idx to val.

        Here, base cases of updating rules are implemented.
        For details, refer to the comments of Arr.update.

        :param idx: Index chain.
        :param val: Value to be assigned.

        :return: Updated matrix.

        :raise ArrErr[EMPTY_IDX]: If index list is empty.
        :raise ArrErr[IDX_BOUND]: If index is out of bound.
        :raise ArrErr[ASGN_N_MISS]: If # indices of index list does not match with # of items in val in
                                    componentwise case.
        """
        if len(idx) > 1:
            return self.promote(len(idx) - 1).update(idx, val)

        if type(val) == Vec:
            if idx[0] is None:
                # [UpIdxAllCompBase]
                if self._dim[0] != val._dim[0]:
                    raise ArrErr(Errno.ASGN_N_MISS, need=self._dim[0], given=val._dim[0])

                return Vec(deepcopy(val._elem))
            else:
                # [UpIdxListCompBase]
                idx_set: Vec = idx[0]
                elem: List = deepcopy(self._elem)

                if idx_set._dim[0] != val._dim[0]:
                    raise ArrErr(Errno.ASGN_N_MISS, need=idx_set.dim[0], given=val._dim[0])

                for i in range(len(idx_set)):
                    j = round(idx_set._elem[i])

                    if j < 0 or j >= self._dim[0]:
                        raise ArrErr(Errno.IDX_BOUND, idx=j)

                    elem[j] = deepcopy(val._elem[i])

                return Vec(elem)
        else:
            if idx[0] is None:
                # [UpIdxAllDistBase]
                return Vec([deepcopy(val) for _ in range(self._dim[0])])
            elif type(idx[0]) == Vec:
                # [UpIdxListDistBase]
                idx_set: Vec = idx[0]
                elem: List = deepcopy(self._elem)

                for i in range(idx_set._dim[0]):
                    j = round(idx_set._elem[i])

                    if j < 0 or j >= self._dim[0]:
                        raise ArrErr(Errno.IDX_BOUND, idx=j)

                    elem[j] = deepcopy(val)

                return Vec(elem)
            else:
                # [UpIdxSnglBase]
                i: int = round(idx[0])
                elem: List = deepcopy(self._elem)

                if i < 0 or i >= self._dim[0]:
                    raise ArrErr(Errno.IDX_BOUND, idx=i)

                elem[i] = deepcopy(val)

                return Vec(elem)

    """
    PROMOTION & DEGRADATION LOGIC

    Refer to the comments of Arr class.
    """

    def promote(self, n: int) -> Arr:
        return Mat([self], [1, self._dim[0]]).promote(n - 1) if n >= 1 else self

    def degrade(self, n: int) -> Any:
        if n > 0:
            return self._elem[0] if self._dim[0] != 0 else None
        else:
            return self

    """
    APPLICATION LOGIC

    Refer to the comments of Arr class.
    This logic is for internal use only.
    """

    def __apply(self, other: Any, op: Callable) -> Vec:
        """
        Applies binary operator op.

        For detail, refer to the comments of Arr.__apply.
        Note that call of this function with array or matrix as other should be rejected.

        :param other: RHS.
        :param op: Operator to be applied.

        :return: Result.

        :raise ArrErr[DIM_MISMATCH]: If # of elements does not match during applying rule [BinOpComp].
        """
        if type(other) == Mat or type(other) == Arr:
            return NotImplemented

        if type(other) == Vec:
            # [BinOpComp]
            if self._dim[0] != other._dim[0]:
                raise ArrErr(Errno.DIM_MISMATCH, op='componentwise binary operation', dim1=str(self._dim),
                             dim2=str(other._dim))

            return Vec([op(self._elem[i], other._elem[i]) for i in range(len(self))])
        else:
            # [BinOpDist]
            return Vec([op(it, other) for it in self._elem])

    """
    FORMATTING LOGIC
    """

    def format(self, w: int, h: int, it_w: int, h_remain: bool = False) -> Union[str, Tuple[str, int]]:
        """
        Formats vector.

        It builds up a formatted string of a vector so that it 'roughly' fits in the given width w and height h.
        The point here is that it 'roughly' fits, NOT exactly fits.
        Exact fitting requires more complicated logic including backtracking technique.
        Elements whose string expression exceeds the limit it_w will be abbreviated.
        For abbreviation and basic formatting policies, refer to the comments of Printer.format.

        Each line starts with the index of the first element to be presented in that line.
        Then consecutive elements will follow until the given width is reached.
        If there are too many elements in a vector so that some of them cannot be formatted,
        a line presenting # of omitted elements will be attached at the end.
        Empty vector will be formatted as 'Empty vector'.

        The rough flow of the logic is as follows:
            1. Stringfy 'enough' number of elements in a vector.
            2. Determine the exact # of elements to be formatted.
            3. Format vector elements.
            4. Attach the last line indicating # of omitted elements if needed.

        :param w: Width of the output.
        :param h: Height of the output.
        :param it_w: Maximum width of an element.
        :param h_remain: If true, it returns # of used lines. (Default: False)

        :return: Formatted string.
        """
        if len(self._elem) == 0:
            return ('Empty vector', h - 1) if h_remain else 'Empty vector'

        # [Step 1]
        buf: str = ''
        # Suppose all elements have string expression with length 1.
        # Since there should be (at least) 2 spaces b/w elements, each elements will eat up 3 spaces.
        # Then at most ceil(w/3) elements can be formatted in a single line.
        # Thus # of elements which will be actually formatted cannot exceed ceil(w/3)h.
        it_cnt: int = min(ceil(w / 3) * h, self._dim[0])
        pool: List[Optional[str]] = [None] * it_cnt
        qt: bool = (type(self._elem[0]) == str)
        # In case of string elements, we need double quotes(") enclosing each of them.
        # This can be considered as it_w being reduced by 2.
        it_w, max_it_w = 0, it_w - 2 * qt

        for i in range(it_cnt):
            it_str: str = str(self._elem[i])

            if len(it_str) > max_it_w:
                it_str = it_str[:max_it_w - 3] + '...'

            it_w = max(it_w, len(it_str))
            pool[i] = it_str

        # [Step 2]
        # Now it_w is exactly the largest (after abbreviation) width of the elements which can be formatted.
        # Then each element eats up exactly (it_w + 2) spaces and exactly floor(w/(it_w + 2)) of elements can be
        # formatted in a single line.
        n: int = floor(w / (it_w + 2))
        # Given n, it needs exactly ceil(p/n) lines to format all elements where p is # of elements.
        m: int = min(ceil(self._dim[0] / n), h)
        # Given m, indices preceding each line will be 0, n, ..., n(m - 1).
        # The largest width among them is achieved by the last one and note that there should be enclosing brackets.
        idx_w: int = len(str(n * (m - 1))) + 2
        i: int = 0

        # [Step 3]
        while i < m - 1:
            buf += ('[' + str(i * n) + ']').rjust(idx_w)
            j: int = 0

            while j < n:
                buf += ('"' * qt + pool[i * n + j] + '"' * qt).rjust(it_w + 2 * qt + 2)
                j += 1

            buf += '\n'
            i += 1

        j: int = 0
        buf += ('[' + str((m - 1) * n) + ']').rjust(idx_w)

        while j < min(n, self._dim[0] - (m - 1) * n):
            buf += ('"' * qt + pool[(m - 1) * n + j] + '"' * qt).rjust(it_w + 2 * qt + 2)
            j += 1

        resi: int = self._dim[0] - (m - 1) * n - min(n, self._dim[0] - (m - 1) * n)
        h_use: int = m

        # [Step 4]
        if resi > 0:
            buf.rstrip()
            buf += f'\n... and {resi} more elements in this vector.'
            h_use += 1

        return (buf.rstrip(), h - h_use) if h_remain else buf.rstrip()


"""
COMMENT WRITTEN: 2021.3.2.
"""
