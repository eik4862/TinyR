from __future__ import annotations

from typing import *
from ctypes import *
import Class


@final
class CLib:
    """
    Wrapper class for C DLL(Dynamic-Link Library).

    Some numerical algorithms which entail heavy computation are implemented in C for efficiency.
    They are compiled as shared libraries(.so) and will be loaded by this class.
    Since types in Python are not compatible with those in C, we need wrapper functions to transfer data b/w Python & C.
    CLib class implements those wrappers.

    This class is implemented as an abstract class. It can not be (and should not be) instantiated.
    This class is the end of inheritance. No further inheritance is allowed.
    """
    # Dictionary containing all loaded DLL.
    __LIBC: Dict[str, CDLL] = {}

    def __init__(self) -> None:
        raise NotImplementedError

    @classmethod
    def init(cls) -> NoReturn:
        """
        Loads DLL.

        MatOp.so contains the following matrix operation algorithms.
            void GEMM(const void **A, const void **B, void **C, int l, int m, int n, int blkSz, _Bool int_mat)
            void LU(double **A, int *p, int *q, int *flag, int m, int n, _Bool cp, double tol)
            void CHOL(double **A, int *flag, int n, double tol)
            void QR(double **A, double *v, int *flag, int m, int n, double tol)
        """
        cls.__LIBC['MatOp'] = CDLL('./CDLL/MatOp.so')

        cls.__LIBC['MatOp'].GEMM.argtype = [POINTER(c_void_p), POINTER(c_void_p), POINTER(c_void_p), c_int, c_int,
                                            c_int, c_int, c_bool]
        cls.__LIBC['MatOp'].LU.argtype = [POINTER(c_void_p), POINTER(c_int), POINTER(c_int), POINTER(c_int), c_int,
                                          c_int, c_bool, c_double]
        cls.__LIBC['MatOp'].CHOL.argtype = [POINTER(c_void_p), POINTER(c_int), c_int, c_double]
        cls.__LIBC['MatOp'].QR.argtype = [POINTER(c_void_p), POINTER(c_double), POINTER(c_int), c_int, c_int, c_double]

    """
    TYPE CASTING LOGIC
    
    This logic is for internal use only.
    """

    @staticmethod
    def __C2Mat(m: Array, d: List[int], trans: bool = False) -> Class.Array.Mat:
        """
        Converts a matrix represented as a double array(double pointer) in C to a Mat class in Python.

        Flag trans indicates whether transpose is needed or not.
        For some numerical algorithms, especially when the size of matrix is large,
        transposing matrix before computation and transpose the result again is profitable by reducing cache miss.

        :param m: C representation of a matrix to be converted.
        :param d: Dimension of matrix m.
        :param trans: If true, transpose the input matrix m. (Default: False)

        :return: Converted matrix.
        """
        if trans:
            return Class.Array.Mat([Class.Array.Vec([m[j][i] for j in range(d[0])]) for i in range(d[1])], [d[1], d[0]])
        else:
            return Class.Array.Mat([Class.Array.Vec([m[i][j] for j in range(d[1])]) for i in range(d[0])], d.copy())

    @staticmethod
    def __C2Vec(v: Array, d: int) -> Class.Array.Vec:
        """
        Converts a vector represented as an array(pointer) in C to a Vec class in Python.

        :param v: C representation of a vector to be converted.
        :param d: Length of vector v.

        :return: Converted vector.
        """
        return Class.Array.Vec([v[i] for i in range(d)])

    @staticmethod
    def __Mat2C(m: Class.Array.Mat, t: Any = None, trans: bool = False) -> Tuple[Array, Any]:
        """
        Converts a matrix represented as a Mat class in Python to a double array(double pointer) in C.

        Parameter t indicates the type of elements of a matrix.
        Unlike Python, C strictly differentiates integer and floating point value.
        If t is given, it casts all elements in a matrix to the type specified by t.
        Otherwise, it casts all elements to long in C iff all elements are integer.
        If a matrix contains at least one floating point value, then all elements will be casted to double in C.
        For flag trans, refer to the comments of __C2Mat.

        :param m: Mat object to be converted.
        :param t: Type of elements in matrix m. (Default: None)
        :param trans: If true, transpose the input matrix m. (Default: False)

        :return: Converted matrix.
        """
        if t is None:
            t = c_long if all([all([type(it) == int for it in row]) for row in m.elem]) else c_double

        if trans:
            m, n = m.dim[1], m.dim[0]

            return (POINTER(t) * m)(*[(t * n)(*[m[j][i] for j in range(n)]) for i in range(m)]), t

        else:
            m, n = m.dim[0], m.dim[1]

            return (POINTER(t) * m)(*[(t * n)(*[m[i][j] for j in range(n)]) for i in range(m)]), t

    """
    WRAPPER
    
    One can use the following functions as if they are Python functions.
    However, since they are just wrappers, it does NOT check validity of passed parameters nor raise exceptions.
    Wrong input parameters may crash the whole program in the worst case.
    """

    @classmethod
    def GEMM(cls, A: Class.Array.Mat, B: Class.Array.Mat, blk_sz: int) -> Class.Array.Mat:
        """
        General matrix multiplication. Multiplies two matrices A and B.

        For l by m matrix A and m by n matrix B, GEMM costs O(2lmn) FLOPs which grows quite fast.
        Thus GEMM is internally implemented using multithreading.
        It divides the input matrix into smaller blocks and computes the multiplication in parallel.
        Parameter blk_sz sets the size of these small blocks.
        If blk_sz is too small, overhead of fetching new thread overwhelms the benefit of parallel computing.
        If blk_sz is too large, blocked matrices will be too large to benefit from multithreading.
        So it must be determined with care and may depend on one's system.

        Since GEMM does not involve any floating point arithmetic,
        it supports two versions, one for an integer matrix and one for a floating point matrix.
        It checks types of elements and cast elements to long in C iff all elements are integer.
        Otherwise, all elements will be casted to double in C.

        :param A: LHS of matrix multiplication.
        :param B: RHS of matrix multiplication.
        :param blk_sz: Block size for parallel computing.

        :return: A * B.
        """
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
        """
        LU decomposition.

        Decomposes non-singular n by n matrix A into L * U where L is n by n unit lower triangular matrix
        and U is n by n upper triangular matrix.
        LU costs O(2n^3/4) FLOPs and employs Gaussian elimination.
        Internal implementation of LU computes in-place, that is, it overwrites the input matrix with the elements of
        L and U in a compact form, rather than producing two additional matrices for L and U.
        However, this does NOT imply that parameter A will be overwritten. This function takes care of this issue.

        If the input matrix A is singular, the internal algorithm will encounter zero pivot during computation
        and cannot proceed anymore.
        In that case, the algorithm sets flag as the column index where it stopped and immediately returns.
        In case of successful decomposition, the flag will be set as # of columns, n.
        Theoretically, this flag is the rank of the input matrix A.
        LU still works for non-square matrices, but then L or U is not triangular any more.

        It supports two types of pivoting strategies, partial pivoting and complete pivoting.
        In case of partial pivoting, it returns a matrix in which elements of L and U are stored in a compact form,
        a vector indicating permutation of rows, and the flag described above.
        In case of complete pivoting, it returns one more vector which indicates permutation of columns.

        :param A: Matrix to be LU decomposed.
        :param cp: If true, complete pivoting is employed. Otherwise, partial pivoting is used.
        :param tol: Tolerance value. If abs(x) < tol, then x will be considered as 0.

        :return: Refer to the paragraph 3 in the comments above.
        """
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
        """
        Cholesky decomposition.

        Decomposes symmetric, positive definite n by n matrix A into L * L' where L is n by n upper triangular matrix
        with positive diagonal entries.
        CHOL costs O(n^3/3) FLOPs and it is internally implemented as an in-place algorithm.
        Thus internally, it overwrites the input matrix with the elements of L in a compact form,
        rather than producing another matrix for L.
        However, this does NOT imply that parameter A will be overwritten. This function takes care of this issue.

        If the input matrix A is not positive definite, the internal algorithm will encounter zero pivot during
        computation and cannot proceed anymore.
        In that case, the algorithm sets flag as the column index where it stopped and immediately returns.
        In case of successful decomposition, the flag will be set as # of columns, n.

        It returns a matrix in which the elements of L are stored in a compact form and the flag described above.

        :param A: Matrix to be Cholesky decomposed.
        :param tol: Tolerance value. If abs(x) < tol, then x will be considered as 0.

        :return: Refer to the paragraph 3 in the comments above.
        """
        n: int = A.nrow
        A, _ = cls.__Mat2C(A, c_double)
        flag = POINTER(c_int)(c_int())

        cls.__LIBC['MatOp'].CHOL(A, flag, n, c_double(tol))

        return cls.__C2Mat(A, [n, n]), flag.contents.value

    @classmethod
    def QR(cls, A: Class.Array.Mat, tol: float) -> Tuple[Class.Array.Mat, Class.Array.Vec, int]:
        """
        QR decomposition.

        Decomposes full column rank m by n matrix A with m >= n into Q * R where Q is m by m orthogonal matrix
        and R is m by n upper triangular matrix with positive diagonal entries.
        QR costs O(2mn^2 - 2n^3/3) FLOPs and employs Householder transformation.
        Internal implementation of QR computes in-place, that is, it overwrites the input matrix with the elements of
        R and constructing vectors of Householder transformations in a compact form,
        rather than producing two additional matrices for Q and R.
        However, this does NOT imply that parameter A will be overwritten. This function takes care of this issue.

        If the input matrix A is not of full column rank, the internal algorithm will encounter zero pivot during
        computation and cannot proceed anymore.
        In that case, the algorithm sets flag as the column index where it stopped and immediately returns.
        In case of successful decomposition, the flag will be set as # of columns, n.

        It returns a matrix in which the elements of R and normalized constructing vectors of Householder
        transformations are stored in a compact form, a vector which contains normalizing factors of those constructing
        vectors, and the flag described above.

        :param A: Matrix to be QR decomposed.
        :param tol: Tolerance value. If abs(x) < tol, then x will be considered as 0.

        :return: Refer to the paragraph 3 in the comments above.
        """
        m, n = A.ncol, A.nrow
        A, _ = cls.__Mat2C(A, c_double, True)
        v: Array = (c_double * m)(*[c_double() for _ in range(m)])
        flag = POINTER(c_int)(c_int())

        cls.__LIBC['MatOp'].QR(A, v, flag, m, n, c_double(tol))

        return cls.__C2Mat(A, [m, n], True), cls.__C2Vec(v, m), flag.contents.value
