from __future__ import annotations

from typing import final, List, NoReturn, Any, Tuple
from Error.Exception import FunErr
from Core.Type import Errno
from Class.Array import Mat, Vec
from copy import deepcopy
from Core.SymbolTable import SymTab
from Class.Function import Fun
from Core.TypeSymbol import FunTSym, NumTSym, ArrTSym, BoolTSym
from CDLL.CLibrary import CLib

"""
MATRIX FUNCTIONS
"""


@final
class MatFun:
    def __init__(self) -> None:
        raise NotImplementedError

    @staticmethod
    def init() -> NoReturn:
        SymTab.inst().update_kw(
            'oMat',
            Fun(MatFun.o_mat,
                FunTSym([NumTSym()], ArrTSym(NumTSym(), 2))
                )
        )
        SymTab.inst().update_kw(
            'zMat',
            Fun(MatFun.z_mat,
                FunTSym([NumTSym()], ArrTSym(NumTSym(), 2))
                )
        )
        SymTab.inst().update_kw(
            'idMat',
            Fun(MatFun.id_mat,
                FunTSym([NumTSym()], ArrTSym(NumTSym(), 2))
                )
        )
        SymTab.inst().update_kw(
            'diagComp',
            Fun(MatFun.diag_comp,
                FunTSym([ArrTSym(NumTSym(), 2), BoolTSym()], ArrTSym(NumTSym(), 1)),
                [('anti', 'F')])
        )
        SymTab.inst().update_kw(
            'diagMat',
            Fun(MatFun.diag_mat,
                FunTSym([ArrTSym(NumTSym(), 1), BoolTSym()], ArrTSym(NumTSym(), 2)),
                [('anti', 'F')])
        )
        SymTab.inst().update_kw(
            'triComp',
            Fun(MatFun.tri_comp,
                FunTSym([ArrTSym(NumTSym(), 2), BoolTSym(), BoolTSym()], ArrTSym(NumTSym(), 2)),
                [('strict', 'T'), ('lower', 'T')]
                )
        )
        SymTab.inst().update_kw(
            'triMat',
            Fun(MatFun.tri_mat,
                FunTSym([ArrTSym(NumTSym(), 1), BoolTSym(), BoolTSym()], ArrTSym(NumTSym(), 2)),
                [('strict', 'T'), ('lower', 'T')]
                )
        )
        SymTab.inst().update_kw(
            'rbind',
            Fun(MatFun.rbind,
                FunTSym([ArrTSym(NumTSym(), 2), ArrTSym(NumTSym(), 2)], ArrTSym(NumTSym(), 2))
                )
        )
        SymTab.inst().update_kw(
            'cbind',
            Fun(MatFun.cbind,
                FunTSym([ArrTSym(NumTSym(), 2), ArrTSym(NumTSym(), 2)], ArrTSym(NumTSym(), 2))
                )
        )
        SymTab.inst().update_kw(
            't',
            Fun(MatFun.t,
                FunTSym([ArrTSym(NumTSym(), 2)], ArrTSym(NumTSym(), 2))
                )
        )
        SymTab.inst().update_kw(
            'lu',
            Fun(MatFun.lu,
                FunTSym([ArrTSym(NumTSym(), 2), BoolTSym()], ArrTSym(NumTSym(), 2))
                )
        )
        SymTab.inst().update_kw(
            'chol',
            Fun(MatFun.chol,
                FunTSym([ArrTSym(NumTSym(), 2)], ArrTSym(NumTSym(), 2))
                )
        )
        SymTab.inst().update_kw(
            'qr',
            Fun(MatFun.qr,
                FunTSym([ArrTSym(NumTSym(), 2)], ArrTSym(NumTSym(), 2))
                )
        )

    @staticmethod
    def o_mat(n: int) -> Mat:
        n = round(n)

        if n <= 0:
            raise FunErr(Errno.FUN_ERR, detail='nonpositive matrix dimension')

        return Mat([Vec([1] * n) for _ in range(n)], [n, n])

    @staticmethod
    def z_mat(n: int) -> Mat:
        n = round(n)

        if n <= 0:
            raise FunErr(Errno.FUN_ERR, detail='nonpositive matrix dimension')

        return Mat([Vec([0] * n) for _ in range(n)], [n, n])

    @staticmethod
    def id_mat(n: int) -> Mat:
        n = round(n)

        if n <= 0:
            raise FunErr(Errno.FUN_ERR, detail='nonpositive matrix dimension')

        return MatFun.diag_mat(Vec([1] * n))

    @staticmethod
    def diag_comp(m: Mat, anti: bool = False) -> Vec:
        n: int = m.ncol
        elem: List = [None] * min(m.nrow, n)

        if anti:
            for i in range(len(elem)):
                elem[i] = m[i][n - i - 1]
        else:
            for i in range(len(elem)):
                elem[i] = m[i][i]

        return Vec(elem)

    @staticmethod
    def diag_mat(v: Vec, anti: bool = False) -> Mat:
        if type(v) != Vec:
            return MatFun.tri_mat(Vec([v]), anti)

        if len(v) == 0:
            raise FunErr(Errno.FUN_ERR, detail='empty element list')

        n: int = len(v)

        if anti:
            return Mat([Vec([0] * (n - i - 1) + [v[i]] + [0] * i) for i in range(n)], [n, n])
        else:
            return Mat([Vec([0] * i + [v[i]] + [0] * (n - i - 1)) for i in range(n)], [n, n])

    # TODO: Implement me
    @staticmethod
    def tri_comp(m: Mat, strict: bool = True, lower: bool = True) -> Mat:
        pass

    @staticmethod
    def tri_mat(v: Vec, strict: bool = True, lower: bool = True) -> Mat:
        if type(v) != Vec:
            return MatFun.tri_mat(Vec([v]), strict, lower)

        if strict:
            if len(v) == 0:
                return Mat([Vec([0])], [1, 1])

            res: Mat = MatFun.tri_mat(v, False, lower)
            n: int = res.ncol

            if lower:
                return Mat([Vec([0] * n)], [1, n]).rbind(res).cbind(Vec([0] * (n + 1)))
            else:
                return Mat([Vec([0]) for _ in range(n)], [n, 1]).cbind(res).rbind(Vec([0] * (n + 1)))
        else:
            if len(v) == 0:
                raise FunErr(Errno.FUN_ERR, detail='empty element list')

            if lower:
                elem: List = []
                i, j = 0, 0
                n: int = len(v)

                while i < n:
                    if i + j >= n:
                        raise FunErr(Errno.FUN_ERR, detail='incompatible number of elements')

                    elem.append(v[i:(i + j + 1)])
                    j += 1
                    i += j

                for i in range(j):
                    elem[i] = Vec(elem[i] + [0] * (j - i - 1))
            else:
                elem_rev: List = []
                i, j = 0, 0
                n: int = len(v)

                while i < n:
                    if i + j >= n:
                        raise FunErr(Errno.FUN_ERR, detail='incompatible number of elements')

                    elem_rev.append(v[(n - i - j - 1):(n - i)])
                    j += 1
                    i += j

                elem: List = [None] * j

                for i in range(j):
                    elem[j - i - 1] = Vec([0] * (j - i - 1) + elem_rev[i])

            return Mat(elem, [j, j])

    @staticmethod
    def rbind(m: Mat, v: Mat) -> Mat:
        if type(m) == Vec:
            return MatFun.rbind(m.promote(1), v)
        elif type(m) != Mat:
            return MatFun.rbind(Vec([m]), v)

        if type(v) == Vec:
            if m.ncol != len(v):
                raise FunErr(Errno.FUN_ERR,
                             detail=f'dimension mismatch (cannot bind {v.dim} vector to {m.dim} matrix)')

            return deepcopy(m).rbind(v)
        elif type(v) == Mat:
            if m.ncol != v.ncol:
                raise FunErr(Errno.FUN_ERR,
                             detail=f'dimension mismatch (cannot bind {v.dim} matrix to {m.dim} matrix)')

            return deepcopy(m).rbind(v)
        else:
            return MatFun.rbind(m, Vec([v]))

    @staticmethod
    def cbind(m: Mat, v: Mat) -> Mat:
        if type(v) == int or type(v) == bool or type(v) == float:
            return MatFun.cbind(m, Vec([v]))

        if m.nrow != len(v):
            raise FunErr(Errno.FUN_ERR, detail=f'dimension mismatch (cannot bind {v.dim} vector to {m.dim} matrix)')

        return deepcopy(m).cbind(v)

    @staticmethod
    def t(m: Mat) -> Mat:
        if type(m) == Mat:
            return Mat([Vec([m[j][i] for j in range(m.nrow)]) for i in range(m.ncol)], [m.ncol, m.nrow])
        if type(m) == Vec:
            return Mat([Vec([m[i]]) for i in range(len(m))], [len(m), 1])
        else:
            return Mat([Vec([m])], [1, 1])

    # TODO: Implement me
    @staticmethod
    def lu(m: Mat, cp: bool = False, tol: float = 1e-8) -> Tuple[Mat, Vec]:
        if m.ncol == 0:
            raise NotImplementedError

        if cp:
            m, p, q, flag = CLib.LU(m, cp, tol)
            print(m.format(100, 100, 10))
            print(p.format(100, 100, 10))
            print(q.format(100, 100, 10))
            print(flag)
        else:
            m, p, flag = CLib.LU(m, cp, tol)
            print(m.format(100, 100, 10))
            print(p.format(100, 100, 10))
            print(flag)

        return m

    # TODO: Implement me
    @staticmethod
    def chol(m: Mat, tol: float = 1e-8):
        if not m.is_sqr:
            raise NotImplementedError

        m, flag = CLib.CHOL(m, tol)
        print(m.format(100, 100, 10))
        print(flag)

        return m

    @staticmethod
    def qr(m: Mat, tol: float = 1e-8):
        if m.nrow < m.ncol:
            raise NotImplementedError

        m, v, flag = CLib.QR(m, tol)
        print(m.format(100, 100, 10))
        print(v.format(100, 100, 10))
        print(flag)

        return m


if __name__ == '__main__':
    A: Mat = Mat([Vec([0.3769721, 0.7205735, -0.8531228]),
                  Vec([0.3015484, 0.9391210, 0.9092592]),
                  Vec([-1.0980232, -0.2293777, 1.1963730]),
                  Vec([-1.1304059, 1.7591313, -0.3715839]),
                  Vec([-2.7965343, 0.1173668, -0.1232602])], [5, 3])

    # x=[[0.3769721, 0.7205735, -0.8531228],[0.3015484, 0.9391210, 0.9092592],[-1.0980232, -0.2293777, 1.1963730],[-1.1304059, 1.7591313, -0.3715839],[-2.7965343, 0.1173668, -0.1232602]]
    # A = MatFun.t(A)
    # m, n = 3, 5
    # v: Vec = Vec([0] * m)
    #
    # for i in range(m):
    #     norm = 0
    #     s = -1 if A[i][i] < 0 else 1
    #
    #     for j in range(n - i):
    #         norm += A[i][i + j] ** 2
    #
    #     norm = sqrt(norm)
    #     u1 = A[i][i] + s * norm
    #     v[i] = u1 / (s * norm)
    #
    #     for j in range(n - i - 1):
    #         A[i][i + j + 1] /= u1
    #
    #     A[i][i] = -s * norm
    #
    #     for j in range(m - i - 1):
    #         tmp = A[i + j + 1][i]
    #
    #         for k in range(n - i - 1):
    #             tmp += A[i][i + k + 1] * A[i + j + 1][i + k + 1]
    #
    #         A[i + j + 1][i] -= tmp * v[i]
    #
    #         for k in range(n - i - 1):
    #             A[i + j + 1][i + k + 1] -= tmp * A[i][i + k + 1] * v[i]
    #     # print(A.format(100, 100, 10))
    #
    # print(MatFun.t(A).format(100, 100, 10))
    # print(v.format(100, 100, 10))
