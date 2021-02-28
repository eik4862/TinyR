from __future__ import annotations

from typing import List, Any, final
from Core.AST import AST
from Error.Exception import ArrErr
from Core.Type import Errno
from copy import deepcopy
from Class.Array import Arr, Mat, Vec


@final
class ArrFact:
    """
    Abstract class for array creation.

    Constructs Arr object from AST.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    """
    OBJECT CREATION LOGIC
    """

    @staticmethod
    def create(ast: AST) -> Arr:
        """
        Creates Arr object from AST.

        :param ast: AST indicating array construction operation.

        :return: Constructed Arr object.

        :raise ArrErr: Constructing array with elements whose dimensions are not compatible raises exception
                       with errno DIM_MISMATCH.
        """
        elem: List = []
        dept: int = ast.t.dept
        dim_old: List[int] = []

        for i in range(len(ast.ch)):
            curr_v: Any = ast.ch[i].tok.v

            if isinstance(curr_v, Arr):
                elem.append(deepcopy(curr_v).promote(dept - curr_v.dept - 1))
                dim_new: List[int] = elem[-1].dim
            elif dept > 1:
                elem.append(Vec([deepcopy(curr_v)]).promote(dept - 2))
                dim_new: List[int] = elem[-1].dim
            else:
                elem.append(deepcopy(curr_v))
                dim_new: List[int] = []

            if len(dim_old) != 0 and dim_old != dim_new:
                dim1: str = '0(base type)' if ast.ch[i - 1].t.base else str(ast.ch[i - 1].tok.v.dim)
                dim2: str = '0(base type)' if ast.ch[i].t.base else str(curr_v.dim)

                raise ArrErr(Errno.DIM_MISMATCH, op='array construction', pos=ast.ch[i].tok.pos, dim1=dim1, dim2=dim2)

            dim_old = dim_new

        if dept == 1:
            return Vec(elem)
        elif dept == 2:
            return Mat(elem, [len(ast.ch), *dim_old])
        else:
            return Arr(elem, [len(ast.ch), *dim_old])
