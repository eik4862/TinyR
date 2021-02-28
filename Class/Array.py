from __future__ import annotations

from typing import List, Optional, Any, Callable, Tuple, Dict, final, Union
from operator import add, sub, mul, mod, floordiv, truediv, pow, eq, ne, le, ge, gt, lt, and_, or_, matmul
from Error.Exception import ArrErr
from math import ceil, floor
from Core.Type import Errno
from copy import deepcopy
from CDLL.CLibrary import CLib


class Arr:
    """
    Array class.

    Represents multidimensional array including vector and matrix.
    All exceptions raised here will be caught be interpreter and the position in the raw input string
    where the exception is raised and the raw input string itself will be properly assigned.
    """

    def __init__(self, elem: List, dim: List[int]) -> None:
        """
        Constructor of Arr class.

        :param elem: Element of the array.
        :param dim: Dimension of the array.
        """
        self._elem: List = elem
        self._dim: List[int] = dim
        self._curr: int = 0

    def __next__(self):
        if self._curr >= len(self._elem):
            raise StopIteration

        it = self._elem[self._curr]
        self._curr += 1

        return it

    def __iter__(self):
        self._curr = 0

        return self

    """
    BUILT-INS
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

    def __str__(self) -> str:
        return 'Arr' + str(self._elem)

    __repr__ = __str__

    def get(self, idx: List) -> Any:
        """
        Helper for indexing.
        It recursively visits elements in the array and returns indexed elements.

        idx_list = Void, idx_list
                 | Arr, idx_list
                 | Num, idx_list
                 | Nil

        hlpr(a, [Nil]) => a
        hlpr([a1, ..., ap], [Void, idx_list]) => [hlpr(a1, [idx_list]), ..., hlpr(ap, [idx_list])]
        hlpr([a1, ..., ap], [[i1, ..., iq], idx_list]) => [hlpr(ai1, [idx_list]), ..., hlpr(aiq, [idx_list])]
        hlpr([a1, ..., ap], [i, idx_list]) => hlpr(ai, [idx_list])

        :param src: List of elements to be visited.
        :param idx: List of indices.

        :return: Indexed elements.
        """
        if len(idx) > self.dept:
            return self.promote(len(idx) - self.dept).get(idx)
        elif len(idx) < self.dept:
            idx += [None] * (self.dept - len(idx))

        if idx[0] is None:
            res = [it.get(idx[1:]) for it in self._elem]

            if type(res[0]) == Vec:
                return Mat(res, [len(res), *res[0].dim])
            elif type(res[0]) == Mat or type(res[0]) == Arr:
                return Arr(res, [len(res), *res[0].dim])
            else:
                return Vec(res)
        elif type(idx[0]) == Vec:
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
            i: int = round(idx[0])

            if i < 0 or i >= self._dim[0]:
                raise ArrErr(Errno.IDX_BOUND, idx=i)

            return self._elem[i].get(idx[1:])

    def update(self, idx: List, val: Any) -> Any:
        if len(idx) > self.dept:
            return self.promote(len(idx) - self.dept).update(idx, val)
        elif len(idx) < self.dept:
            idx += [None] * (self.dept - len(idx))

        if isinstance(val, Arr):
            if idx[0] is None:
                if self._dim[0] != len(val):
                    raise ArrErr(Errno.ASGN_N_MISS, need=self._dim[0], given=len(val))

                return Arr([self._elem[i].update(idx[1:], val[i]) for i in range(self._dim[0])], self._dim.copy())
            elif type(idx[0]) == Vec:
                idx_set: Vec = idx[0]
                elem: List = deepcopy(self._elem)

                if len(idx_set) != len(val):
                    raise ArrErr(Errno.ASGN_N_MISS, need=len(idx_set), given=len(val))

                for i in range(len(idx_set)):
                    j = round(idx_set[i])

                    if j < 0 or j >= self._dim[0]:
                        raise ArrErr(Errno.IDX_BOUND, idx=j)

                    elem[j] = elem[j].update(idx[1:], val[i])

                return Arr(elem, self._dim.copy())
            else:
                i: int = round(idx[0])
                elem: List = deepcopy(self._elem)

                if i < 0 or i >= self._dim[0]:
                    raise ArrErr(Errno.IDX_BOUND, idx=i)

                elem[i] = elem[i].update(idx[1:], val)

                return Arr(elem, self._dim.copy())
        else:
            if idx[0] is None:
                return Arr([it.update(idx[1:], val) for it in self._elem], self._dim.copy())
            elif type(idx[0]) == Vec:
                idx_set: Vec = idx[0]
                elem: List = deepcopy(self._elem)

                for i in range(len(idx_set)):
                    j = round(idx_set[i])

                    if j < 0 or j >= self._dim[0]:
                        raise ArrErr(Errno.IDX_BOUND, idx=j)

                    elem[j] = elem[j].update(idx[1:], val)

                return Arr(elem, self._dim.copy())
            else:
                i: int = round(idx[0])
                elem: List = deepcopy(self._elem)

                if i < 0 or i >= self._dim[0]:
                    raise ArrErr(Errno.IDX_BOUND, idx=i)

                elem[i] = elem[i].update(idx[1:], val)

                return Arr(elem, self._dim.copy())

    """
    PROMOTION LOGIC
    """

    def promote(self, n: int) -> Arr:
        res: Arr = self

        while n > 0:
            res = Arr([res], [1, *res._dim])
            n -= 1

        return res

    def degrade(self, n: int) -> Any:
        res: Arr = self

        while n > 0:
            res = self._elem[0]
            n -= 1

            if type(res) == Mat:
                return res.degrade(n)

        return res

    """
    ITERATION LOGIC
    """

    def __apply(self, other: Any, op: Callable) -> Arr:
        """
        Applies general binary operation to the array properly.
        There are three (basically two) cases.
            1. [a1, ..., ap] op [b1, ..., bp] => [a1 op b1, ..., ap op bp]
            2. [a1, ..., ap] op b => [a1 op b, ..., ap op b] if b is base type.
            3. a op [b1, ..., bp] => [a op b1, ..., a op bp] if a is base type.
        The first case is componentwise case and the others are distributive case.
        Self will be considered as LHS and other will be considered as RHS.
        This should be took into consideration for some operations, like rmul.
        Dimension of one hand side may be automatically promoted for case 1.

        :param other: Right hand side of the operation.
        :param op: Operation to be applied.

        :return: Operation result.

        :raise ArrErr: In componentwise case, two arrays whose dimensions are not compatible raise exception
                       with errno DIM_MISMATCH.
        """
        if isinstance(other, Arr):
            if self.dept > other.dept:
                return op(self, other.promote(self.dept - other.dept))
            elif self.dept < other.dept:
                return op(self.promote(other.dept - self.dept), other)

            if self._dim[0] != other._dim[0]:
                raise ArrErr(Errno.DIM_MISMATCH, op='componentwise binary operation', dim1=str(self._dim),
                             dim2=str(other._dim))

            return Arr([op(self._elem[i], other._elem[i]) for i in range(self._dim[0])], self._dim.copy())
        else:
            return Arr([op(it, other) for it in self._elem], self._dim.copy())

    def __apply_matmul(self, other: Any, op: Callable) -> Arr:
        """
        Applies matrix multiplication to the array properly.
        Matrix operation deserves a special treat, and thus it is written as a separated logic.
        Logical structure is exactly same as __apply.

        :param other: Right hand side of the operation.
        :param op: Operation to be applied.

        :return: Operation result.

        :raise ArrErr: In componentwise case, two arrays whose dimensions are not compatible raise exception
                  with errno DIM_MISMATCH.
        """

        if type(other) == Arr:
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
            elem: List = [op(it, other) for it in self._elem]
            dim: List[int] = [self._dim[0], *elem[0].dim]

        return Arr(elem, dim)

    """
    FORMATTING LOGIC
    """

    @staticmethod
    def __format_hlpr(elem: Arr, pos: List[int], w: int, h: int, it_w: int) -> Tuple[str, int]:
        """
        Formats array(with depth > 2) properly.
        It recursively visits elements until it encounters matrix.
        Then each matrix will be formatted until the given height is exhausted.
        Each matrix element will be separated by newline and
        will be preceded by index indicating the position of the matrix in the original array.
        Empty array will be formatted as 'Empty array with dimension d1 by ... by dp'.

        :param pos: Position of currently visiting element in the original array.
        :param w: Width of the output.
        :param h: Height of the output.
        :param it_w: Maximum width of the element in the array.
        :param dept: Depth of current visiting. Used to determine it is time to format matrix or request further visit.

        :return: Tuple consists of formatted array and # of lines used.
        """
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

    def format(self, w: int, h: int, it_w: int, h_remain: bool = False) -> Union[str, Tuple[str, int]]:
        """
        Formats array(including vector and matrix) like R.
        Element which is too long will be abbreviated using three dots(...).
        String element will be enclosed by double quote(").
        If there are too many elements to be formatted, the last line shows # of the left elements.

        :param w: Width of the output.
        :param h: Height of the output.
        :param it_w: Maximum width of the element in the array.

        :return: Formatted array.
        """
        if self._dim[-1] == 0:
            buf: str = 'Empty array with dimension ' + ' by '.join(map(str, self._dim))

            return (buf, 1) if h_remain else buf

        res, h = self.__format_hlpr(self, [], w, h, it_w)

        return (res.rstrip(), h) if h_remain else res.rstrip()

    def append(self, v: Any) -> Arr:
        if type(v) == list:
            self._elem += v
            self._dim[0] += len(v)
        else:
            self._elem.append(v)
            self._dim[0] += 1

        return self

    """
    GETTERS & SETTERS
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
    def __init__(self, elem: List, dim: List[int]) -> None:
        """
        Constructor of Arr class.

        :param elem: Element of the matrix.
        """
        super().__init__(elem, dim)

    """
    BUILT-INS
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
        if type(other) == Arr:
            return NotImplemented

        if type(other) == Vec:
            if self._dim[1] != 1:
                raise ArrErr(Errno.DIM_MISMATCH, op='matrix multiplication', dim1=str(self._dim), dim2=str(other.dim))

            return Mat([self._elem[i] * other[i] for i in range(self._dim[0])], [self._dim[0], len(other)])
        elif type(other) == Mat:
            if self._dim[1] != other._dim[0]:
                raise ArrErr(Errno.DIM_MISMATCH, op='matrix multiplication', dim1=str(self._dim), dim2=str(other._dim))

            return CLib.GEMM(self, other)
        else:
            if self._dim[1] != 1:
                raise ArrErr(Errno.DIM_MISMATCH, op='matrix multiplication', dim1=str(self._dim), dim2='0(base type)')

            return Mat([it * other for it in self._elem], [self._dim[0], 1])

    def __rmatmul__(self, other: Any) -> Mat:
        if type(other) == Arr:
            return NotImplemented

        # TODO: Optimization
        if type(other) == Vec:
            if self._dim[0] != len(other):
                raise ArrErr(Errno.DIM_MISMATCH, op='matrix multiplication', dim1=str(self._dim),
                             dim2=str([1, len(other)]))

            return CLib.GEMM(other.promote(1), self)
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

    def __invert__(self) -> Mat:
        return Mat([~it for it in self._elem], self._dim.copy())

    def __deepcopy__(self, memodict: Dict = {}) -> Mat:
        return Mat(deepcopy(self._elem), self._dim.copy())

    def __str__(self) -> str:
        return 'Mat' + str(self._elem)

    __repr__ = __str__

    def update(self, idx: List, val: Any) -> Any:
        if len(idx) > 2:
            return self.promote(len(idx) - 1).update(idx, val)
        elif len(idx) < 2:
            idx += [None]

        if isinstance(val, Mat):
            if idx[0] is None:
                if self._dim[0] != len(val):
                    raise ArrErr(Errno.ASGN_N_MISS, need=self._dim[0], given=len(val))

                return Mat([self._elem[i].update(idx[1:], val[i]) for i in range(self._dim[0])], self._dim.copy())
            elif type(idx[0]) == Vec:
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
                i: int = round(idx[0])
                elem: List = deepcopy(self._elem)

                if i < 0 or i >= self._dim[0]:
                    raise ArrErr(Errno.IDX_BOUND, idx=i)

                elem[i] = elem[i].update(idx[1:], val)

                return Mat(elem, self._dim.copy())
        else:
            if idx[0] is None:
                return Mat([it.update(idx[1:], val) for it in self._elem], self._dim.copy())
            elif type(idx[0]) == Vec:
                idx_set: Vec = idx[0]
                elem: List = deepcopy(self._elem)

                for i in range(len(idx_set)):
                    j = round(idx_set[i])

                    if j < 0 or j >= self._dim[0]:
                        raise ArrErr(Errno.IDX_BOUND, idx=j)

                    elem[j] = elem[j].update(idx[1:], val)

                return Mat(elem, self._dim.copy())
            else:
                i: int = round(idx[0])
                elem: List = deepcopy(self._elem)

                if i < 0 or i >= self._dim[0]:
                    raise ArrErr(Errno.IDX_BOUND, idx=i)

                elem[i] = elem[i].update(idx[1:], val)

                return Mat(elem, self._dim.copy())

    """
    PROMOTION LOGIC
    """

    def promote(self, n: int) -> Arr:
        return Arr([self], [1, *self._dim]).promote(n - 1) if n >= 1 else self

    def degrade(self, n: int) -> Arr:
        return self._elem[0].degrade(n - 1) if n > 0 else self

    """
    ITERATION LOGIC
    """

    def __apply(self, other: Any, op: Callable) -> Mat:
        if type(other) == Arr:
            return NotImplemented

        if type(other) == Vec:
            return op(self, other.promote(1))
        elif type(other) == Mat:
            if self._dim[0] != other._dim[0]:
                raise ArrErr(Errno.DIM_MISMATCH, op='componentwise binary operation', dim1=str(self._dim),
                             dim2=str(other._dim))

            return Mat([op(self._elem[i], other._elem[i]) for i in range(self._dim[0])], self._dim.copy())
        else:
            return Mat([op(it, other) for it in self._elem], self._dim.copy())

    """
    FORMATTING LOGIC
    """

    def format(self, w: int, h: int, it_w: int, h_remain: bool = False) -> Union[str, Tuple[str, int]]:
        """
        Formats matrix properly.
        If the given height and width are enough, all elements will be formatted.
        If the given height is enough but the given width is not,
        the exceeding column will be formatted using the remaining height.
        If the given width is enough but the given height si not, the exceeding rows will not be formatted.
        If the given height and width are not enough, exceeding columns and rows will not be formatted.
        The first line consists of column indices and the following lines starts with the corresponding row index.
        Empty matrix will be formatted as 'Empty matrix with dimension m by n'.

        :param w: Width of the output.
        :param h: Height of the output.
        :param it_w: Maximum width of the element in the matrix.
        :param h_remain: If true, it returns # of used lines. (Default: False)

        :return: Tuple consists of formatted matrix and # of lines used.
        """
        if self._dim[-1] == 0:
            buf: str = f'Empty matrix with dimension {self._dim[0]} by {self._dim[1]}'

            return (buf, 1) if h_remain else buf

        buf: str = ''
        c_cnt: int = min(ceil(w / 3), self._dim[1])
        m: int = min(h - 1, self._dim[0])

        if h > self._dim[0]:
            c_cnt *= ceil(h / self._dim[0])
            c_cnt = min(c_cnt, self._dim[1])

        pool: List[List[Optional[str]]] = [[None for _ in range(c_cnt)] for _ in range(m)]
        qt: bool = (type(self._elem[0][0]) == str)
        it_w, mat_it_w = 0, it_w - 2 * qt

        # Stringfy 'enough' elements.
        for i in range(m):
            for j in range(c_cnt):
                it_str: str = str(self._elem[i][j])

                if len(it_str) > mat_it_w:
                    it_str = it_str[:mat_it_w - 3] + '...'

                it_w = max(it_w, len(it_str))
                pool[i][j] = it_str

        # Determine exact # of elements which can be formatted.
        r_idx_w: int = len(str(m)) + 3
        it_w = max(it_w, len(str(c_cnt)) + 3)
        n: int = floor(w / (it_w + 2))
        l: int = min(ceil((h - 1) / (m + 1)), ceil(self._dim[1] / n))
        k: int = 0

        # Format each element.
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

        # Attach the last line indicating # of the omitted elements if needed.
        if resi > 0:
            buf += f'... and {resi} more elements.'
            h_use += 1

        return (buf.rstrip(), h - h_use) if h_remain else buf.rstrip()

    def rbind(self, v: Mat) -> Mat:
        if type(v) == Vec:
            assert len(v) == self._dim[1]

            self.append(v)
        else:
            assert self._dim[1] == v._dim[1]

            self.append(v.elem)

        return self

    def cbind(self, v: Mat) -> Mat:
        if type(v) == Vec:
            assert len(v) == self._dim[0]

            for i in range(self._dim[0]):
                self._elem[i].append(v[i])

            self._dim[1] += 1
        else:
            assert self._dim[0] == v._dim[0]

            for i in range(self._dim[0]):
                self._elem[i].append(v[i].elem)

            self._dim[1] += v._dim[1]

        return self

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
    def __init__(self, elem: List) -> None:
        """
        Constructor of Arr class.

        :param elem: Element of the vector.
        """
        super().__init__(elem, [len(elem)])

    """
    BUILT-INS
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
        if type(other) == Mat or type(other) == Arr:
            return NotImplemented

        if self._dim[0] != 1:
            raise ArrErr(Errno.DIM_MISMATCH, op='matrix multiplication', dim1=str(self._dim),
                         dim2=str(other._dim) if type(other) == Vec else '0(base type)')

        return Vec([self._elem[0] * other]).promote(1) if type(other) == Vec else Vec([self * other]).promote(1)

    def __rmatmul__(self, other: Any) -> Mat:
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

    def __invert__(self) -> Vec:
        return Vec([not it for it in self._elem])

    def __deepcopy__(self, memodict: Dict = {}) -> Vec:
        return Vec(deepcopy(self._elem))

    def __str__(self) -> str:
        return 'Vec' + str(self._elem)

    __repr__ = __str__

    def get(self, idx: List) -> Any:
        if len(idx) > 1:
            return self.promote(len(idx) - 1).get(idx)

        if idx[0] is None:
            return Vec(deepcopy(self._elem))
        elif type(idx[0]) == Vec:
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
            i: int = round(idx[0])

            if i < 0 or i >= self._dim[0]:
                raise ArrErr(Errno.IDX_BOUND, idx=i)

            return self._elem[i]

    def update(self, idx: List, val: Any) -> Any:
        if len(idx) > 1:
            return self.promote(len(idx) - 1).update(idx, val)

        if type(val) == Vec:
            if idx[0] is None:
                if self._dim[0] != val._dim[0]:
                    raise ArrErr(Errno.ASGN_N_MISS, need=self._dim[0], given=val._dim[0])

                return Vec(deepcopy(val._elem))
            else:
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
                return Vec([deepcopy(val) for _ in range(self._dim[0])])
            elif type(idx[0]) == Vec:
                idx_set: Vec = idx[0]
                elem: List = deepcopy(self._elem)

                for i in range(idx_set._dim[0]):
                    j = round(idx_set._elem[i])

                    if j < 0 or j >= self._dim[0]:
                        raise ArrErr(Errno.IDX_BOUND, idx=j)

                    elem[j] = deepcopy(val)

                return Vec(elem)
            else:
                i: int = round(idx[0])
                elem: List = deepcopy(self._elem)

                if i < 0 or i >= self._dim[0]:
                    raise ArrErr(Errno.IDX_BOUND, idx=i)

                elem[i] = deepcopy(val)

                return Vec(elem)

    """
    PROMOTION LOGIC
    """

    def promote(self, n: int) -> Arr:
        return Mat([self], [1, self._dim[0]]).promote(n - 1) if n >= 1 else self

    def degrade(self, n: int) -> Any:
        if n > 0:
            return self._elem[0] if self._dim[0] != 0 else None
        else:
            return self

    """
    ITERATION LOGIC
    """

    def __apply(self, other: Any, op: Callable) -> Vec:
        if type(other) == Mat or type(other) == Arr:
            return NotImplemented

        if type(other) == Vec:
            if self._dim[0] != other._dim[0]:
                raise ArrErr(Errno.DIM_MISMATCH, op='componentwise binary operation', dim1=str(self._dim),
                             dim2=str(other._dim))

            return Vec([op(self._elem[i], other._elem[i]) for i in range(len(self))])
        else:
            return Vec([op(it, other) for it in self._elem])

    """
    FORMATTING LOGIC
    """

    def format(self, w: int, h: int, it_w: int, h_remain: bool = False) -> Union[str, Tuple[str, int]]:
        """
        Formats vector properly.
        Each line starts with the index of the first element in that line.
        Empty vector will be formatted as 'Empty vector'.

        :param w: Width of the output.
        :param h: Height of the output.
        :param it_w: Maximum width of the element in the vector.
        :param h_remain: If true, it returns # of used lines. (Default: False)

        :return: Formatted vector.
        """
        if len(self._elem) == 0:
            return ('Empty vector', 1) if h_remain else 'Empty vector'

        buf: str = ''
        it_cnt: int = min(ceil(w / 3) * h, len(self._elem))
        pool: List[Optional[str]] = [None] * it_cnt
        qt: bool = (type(self._elem[0]) == str)
        it_w, max_it_w = 0, it_w - 2 * qt

        # Stringfy 'enough' elements.
        for i in range(it_cnt):
            it_str: str = str(self._elem[i])

            if len(it_str) > max_it_w:
                it_str = it_str[:max_it_w - 3] + '...'

            it_w = max(it_w, len(it_str))
            pool[i] = it_str

        # Determine exact # of elements which can be formatted.
        n: int = floor(w / (it_w + 2))
        m: int = min(ceil(it_cnt / n), h)
        idx_w: int = len(str(1 + n * (m - 1))) + 2
        i: int = 0

        # Format each element.
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

        # Attach the last line indicating # of the omitted elements if needed.
        if resi > 0:
            buf += f'\n... and {resi} more elements.'
            h_use += 1

        return (buf, h - h_use) if h_remain else buf
