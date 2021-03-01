from __future__ import annotations

from typing import List, Any, Tuple, Dict, NoReturn, Union
from ctypes import c_long, c_double, c_void_p, c_int, c_bool, CDLL, POINTER, Array
import Class


class CLib:
    __LIBC: Dict[str, CDLL] = {}

    def __init__(self) -> None:
        raise NotImplementedError

    @staticmethod
    def __C2Mat(m: Array, d: List[int], trans: bool = False) -> Class.Array.Mat:
        if trans:
            return Class.Array.Mat([Class.Array.Vec([m[j][i] for j in range(d[0])]) for i in range(d[1])], [d[1], d[0]])
        else:
            return Class.Array.Mat([Class.Array.Vec([m[i][j] for j in range(d[1])]) for i in range(d[0])], d.copy())

    @staticmethod
    def __C2Vec(v: Array, d: int) -> Class.Array.Vec:
        return Class.Array.Vec([v[i] for i in range(d)])

    @staticmethod
    def __Mat2C(self, t: Any = None, trans: bool = False) -> Tuple[Array, Any]:
        if t is None:
            t = c_long if all([all([type(it) == int for it in row]) for row in self._elem]) else c_double

        if trans:
            m, n = self._dim[1], self._dim[0]

            return (POINTER(t) * m)(*[(t * n)(*[self._elem[j][i] for j in range(n)]) for i in range(m)]), t

        else:
            m, n = self._dim[0], self._dim[1]

            return (POINTER(t) * m)(*[(t * n)(*[self._elem[i][j] for j in range(n)]) for i in range(m)]), t

    @classmethod
    def init(cls) -> NoReturn:
        cls.__LIBC['MatOp'] = CDLL('./CDLL/MatOp.so')

        cls.__LIBC['MatOp'].GEMM.argtype = [POINTER(c_void_p), POINTER(c_void_p), POINTER(c_void_p), c_int, c_int,
                                            c_int, c_int, c_bool]
        cls.__LIBC['MatOp'].LU.argtype = [POINTER(c_void_p), POINTER(c_int), POINTER(c_int), POINTER(c_int), c_int,
                                          c_int, c_bool, c_double]
        cls.__LIBC['MatOp'].CHOL.argtype = [POINTER(c_void_p), POINTER(c_int), c_int, c_double]
        cls.__LIBC['MatOp'].QR.argtype = [POINTER(c_void_p), POINTER(c_double), POINTER(c_int), c_int, c_int, c_double]

    @classmethod
    def GEMM(cls, A: Class.Array.Mat, B: Class.Array.Mat, blk_sz: int) -> Class.Array.Mat:
        l, m, n = A.nrow, A.ncol, B.ncol
        A, t1 = cls.__Mat2C(A)
        B, t2 = cls.__Mat2C(B)
        t: Any = c_long if t1 == t2 == c_long else c_double
        C: Array = (POINTER(t) * l)(*[(t * n)() for _ in range(l)])

        cls.__LIBC['MatOp'].GEMM(A, B, C, l, m, n, blk_sz, t == c_long)

        return cls.__C2Mat(C, [l, n])

    @classmethod
    def LU(cls, A: Class.Array.Mat, cp: bool, tol: float) -> Union[
            Tuple[Class.Array.Mat, Class.Array.Vec, Class.Array.Vec, int],
            Tuple[Class.Array.Mat, Class.Array.Vec, int]]:
        m, n = A.nrow, A.ncol
        A, _ = cls.__Mat2C(A, c_double)
        p: Array = (c_int * n)(*[i for i in range(m)])
        q: Array = (c_int * n)(*[i for i in range(n)]) if cp else None
        flag = POINTER(c_int)(c_int())

        cls.__LIBC['MatOp'].GECP(A, p, q, flag, m, n, c_double(tol))

        if cp:
            return cls.__C2Mat(A, [m, n]), cls.__C2Vec(p, m), cls.__C2Vec(q, n), flag.contents.value
        else:
            return cls.__C2Mat(A, [m, n]), cls.__C2Vec(p, m), flag.contents.value

    @classmethod
    def CHOL(cls, A: Class.Array.Mat, tol: float) -> Tuple[Class.Array.Mat, int]:
        n: int = A.nrow
        A, _ = cls.__Mat2C(A, c_double)
        flag = POINTER(c_int)(c_int())

        cls.__LIBC['MatOp'].CHOL(A, flag, n, c_double(tol))

        return cls.__C2Mat(A, [n, n]), flag.contents.value

    @classmethod
    def QR(cls, A: Class.Array.Mat, tol: float) -> Tuple[Class.Array.Mat, Class.Array.Vec, int]:
        m, n = A.ncol, A.nrow
        A, _ = cls.__Mat2C(A, c_double, True)
        v: Array = (c_double * m)(*[c_double() for _ in range(m)])
        flag = POINTER(c_int)(c_int())

        cls.__LIBC['MatOp'].QR(A, v, flag, m, n, c_double(tol))

        return cls.__C2Mat(A, [m, n], True), cls.__C2Vec(v, m), flag.contents.value
