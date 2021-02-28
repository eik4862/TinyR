from __future__ import annotations

from typing import List, Any, Tuple, Dict, NoReturn
from ctypes import c_long, c_double, c_void_p, c_int, c_bool, CDLL, POINTER, Array
import Class


class CLib:
    __LIBC: Dict[str, CDLL] = {}

    def __init__(self) -> None:
        raise NotImplementedError

    @staticmethod
    def __C2Mat(m: Array, d: List[int]) -> Class.Array.Mat:
        return Class.Array.Mat([Class.Array.Vec([m[i][j] for j in range(d[1])]) for i in range(d[0])], d.copy())

    @staticmethod
    def __C2Vec(v: Array, d: int) -> Class.Array.Vec:
        return Class.Array.Vec([v[i] for i in range(d)])

    @staticmethod
    def __Mat2C(self) -> Tuple[Array, Any]:
        m, n = self._dim[0], self._dim[1]

        t = c_long if all([all([type(it) == int for it in row]) for row in self._elem]) else c_double

        return (POINTER(t) * m)(*[(t * n)(*[self._elem[i][j] for j in range(n)]) for i in range(m)]), t

    @classmethod
    def init(cls) -> NoReturn:
        cls.__LIBC['GEMM'] = CDLL('./CDLL/GEMM.so')
        cls.__LIBC['LU'] = CDLL('./CDLL/LU.so')

        cls.__LIBC['GEMM'].argtype = [POINTER(c_void_p), POINTER(c_void_p), POINTER(c_void_p), c_int, c_int, c_int,
                                      c_bool]
        cls.__LIBC['LU'].argtype = [POINTER(c_void_p), POINTER(c_int), c_int, c_bool]

    @classmethod
    def GEMM(cls, A: Class.Array.Mat, B: Class.Array.Mat) -> Class.Array.Mat:
        l, m, n = A.nrow, A.ncol, B.ncol
        A, t1 = cls.__Mat2C(A)
        B, t2 = cls.__Mat2C(B)
        t: Any = c_long if t1 == t2 == c_long else c_double
        C: Array = (POINTER(t) * l)(*[(t * n)() for _ in range(l)])

        cls.__LIBC['GEMM'].GEMM(A, B, C, l, m, n, t == c_long)

        return cls.__C2Mat(C, [l, n])

    @classmethod
    def LU(cls, A: Class.Array.Mat) -> Tuple[Class.Array.Mat, Class.Array.Vec]:
        n: int = A.ncol
        A, t = cls.__Mat2C(A)
        perm: Array = (c_int * n)(*[i for i in range(n)])

        cls.__LIBC['LU'].LU(A, perm, n, t == c_long)

        return cls.__C2Mat(A, [n, n]), cls.__C2Vec(perm, n)
