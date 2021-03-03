from __future__ import annotations

from Core.Type import *
from Util.Printer import *

"""
CLASSES FOR EXCEPTIONS.

All custom exception classes must inherit Err class.
"""


class Err(Exception):
    """
    Root class for custom exceptions.

    This class should not be directly instantiated.
    Instead, use this class as a wild card meaning 'any custom exceptions'.
    """

    def __init__(self, pos: int, line: str, errno: Errno) -> None:
        # Position in the raw input string where the exception is raised.
        self._pos: int = pos
        # Raw input string.
        self._line: str = line
        # Errno.
        self._errno: Errno = errno

    """
    GETTER & SETTER
    """

    @property
    def pos(self) -> int:
        return self._pos

    @property
    def line(self) -> str:
        return self._line

    @property
    def errno(self) -> Errno:
        return self._errno

    @property
    def msg(self) -> str:
        """
        Returns an error message.

        All error messages are preceded by the raw input string
        and an indicator pointing the position where the exception is raised.

        Override this function to attach additional information regarding specific exception.
        Use Printer.as_red to print out error messages in red color.

        :return: Error message.
        """
        return self._line.rstrip() + '\n' + '~' * self._pos + '^\n'

    @pos.setter
    def pos(self, pos: int) -> NoReturn:
        self._pos = pos

    @line.setter
    def line(self, line: str) -> NoReturn:
        self._line = line


"""
EXCEPTIONS FROM CORE MODULES: PARSER, SEMANTIC CHECKER, AND INTERPRETER.
"""


@final
class ParserErr(Err):
    """
    Exceptions from parser.

    There are six scenarios raising this exception.
        1. INVALID_TOK: Invalid token is encountered. (eg. 2 + @)
        2. NCLOSED_PARN: Parenthesis or quote is not closed. (eg. x[2=3)
        3. INCOMP_EXPR: Input expression is incomplete. (eg. 2 + )
        4. FUN_CALL_MISS: Function call expression is not complete. (eg. idMat + 2)
        5. ARG_MISPOS: Non-keyword argument for function call is followed by keyword arguments.
                       (eg. triMat(1:3, strict = T, 2))
        6. MEMID_MISS: Member id in a struct is missing. (eg. {x: 2, 3})

    This class is the end of inheritance. No further inheritance is allowed.
    """

    def __init__(self, pos: int, line: str, errno: Errno) -> None:
        super().__init__(pos, line, errno)

    @property
    def msg(self) -> str:
        """
        Returns an error message.

        For detail, refer to the comments of Err.msg.
        Examples of additional error messages are as follows:
            1. INVALID_TOK: [Invalid syntax] Unexpected token encountered at 2.
            2. NCLOSED_PARN: [Invalid syntax] Parenthesis(quote) at 2 is not closed.
            3. INCOMP_EXPR: [Invalid syntax] Expression is incomplete.
            4. FUN_CALL_MISS: [Invalid syntax] Function call at 2 is not complete.
            5. ARG_MISPOS: [Invalid syntax] Only keyword arguments can be placed here.
            6. MEMID_MISS: [Invalid syntax] Member id is missing.

        :return: Error message.
        """
        msg: str = self._line.rstrip() + '\n' + '~' * self._pos + '^\n'

        if self._errno == Errno.INVALID_TOK:
            msg += Printer.as_red(f'[Invalid syntax] Unexpected token encountered at {self._pos}.')
        elif self._errno == Errno.NCLOSED_PARN:
            msg += Printer.as_red(f'[Invalid syntax] Parenthesis(quote) at {self._pos} is not closed.')
        elif self._errno == Errno.INCOMP_EXPR:
            msg += Printer.as_red('[Invalid syntax] Expression is incomplete.')
        elif self._errno == Errno.FUN_CALL_MISS:
            msg += Printer.as_red(f'[Invalid syntax] Function call at {self._pos} is not complete.')
        elif self._errno == Errno.ARG_MISPOS:
            msg += Printer.as_red('[Invalid syntax] Only keyword arguments can be placed here.')
        elif self._errno == Errno.MEMID_MISS:
            msg += Printer.as_red('[Invalid syntax] Member id is missing.')

        return msg


@final
class SemanticChkErr(Err):
    """
    Exceptions from semantic checker.

    There are six scenarios raising this exception.
        1. INHOMO_ELEM: Types of elements in an array are not identical. (eg. [2, 'a'])
        2. SGNTR_NFOUND: Operator or function call signature is wrong. (eg. 2 + 'a')
        3. NOT_DEFINE: Variable is used before assignment. (eg. x + 2 where x is not assigned.)
        4. ASGN_T_MISS: Types of both hand sides do not match in case of assignment with indexing.
                        (eg. x[2] = 3 where x is of type Arr[Num, 1].)
        5. INVALID_LVAL: LHS of an assignment cannot be interpreted as a l-value. (eg. 2 = 3)
        6. ID_DUP: Member ids in a strut are duplicated. (eg. {x: 2, x: 3})

    This class is the end of inheritance. No further inheritance is allowed.
    """

    def __init__(self, pos: int, line: str, errno: Errno, **kwargs) -> None:
        super().__init__(pos, line, errno)
        self.__info: Dict[str, Any] = kwargs

    @property
    def msg(self) -> str:
        """
        Returns an error message.

        For detail, refer to the comments of Err.msg.
        Examples of additional error messages are as follows:
            1. INHOMO_ELEM: [Type error] Types of elements consisting a vector are not homogeneous.
                                         Inferred type is [Num, Str].
            2. SGNTR_NFOUND: [Type error] Signature for function call(operator) does not match.
                                          Inferred type is (Num, Str) => NA.
            3. NOT_DEFINE: [Semantic error] Variable x is not defined.
            4. ASGN_T_MISS: [Type error] You cannot assign Str to Num.
            5. INVALID_LVAL: [Semantic error] The LHS of assignment at 2 cannot be a l-value.
            6. ID_DUP: [Semantic error] Struct member id x is duplicated.

        :return: Error message.
        """
        msg: str = self._line.rstrip() + '\n' + '~' * self._pos + '^\n'

        if self._errno == Errno.INHOMO_ELEM:
            infer: str = self.__info['infer']
            msg += Printer.as_red(f'[Type error] Types of elements consisting a vector are not homogeneous.\n')
            msg += Printer.as_red(f'             Inferred type is [{infer}].')
        elif self._errno == Errno.SGNTR_NFOUND:
            infer: str = self.__info['infer']
            msg += Printer.as_red(f'[Type error] Signature for function call(operator) does not match.\n')
            msg += Printer.as_red(f'             Inferred type is {infer}.')
        elif self._errno == Errno.NOT_DEFINE:
            var: str = self.__info['var']
            msg += Printer.as_red(f'[Semantic error] Variable {var} is not defined.')
        elif self._errno == Errno.ASGN_T_MISS:
            tar_t, val_t = self.__info['tar_t'], self.__info['val_t']
            msg += Printer.as_red(f'[Type error] You cannot assign {val_t} to {tar_t}.')
        elif self._errno == Errno.INVALID_LVAL:
            msg += Printer.as_red(f'[Semantic error] The LHS of assignment at {self._pos} cannot be a l-value.')
        elif self._errno == Errno.ID_DUP:
            id_: str = self.__info['id_']
            msg += Printer.as_red(f'[Semantic error] Struct member id {id_} is duplicated.')

        return msg


class InterpErr(Err):
    """
    Exceptions from interpreter.

    There are three scenarios raising this exception.
        1. KERNEL_ERR: Python kernel raised exception during computation. (eg. 2 / 0)
        2. NOT_IMPLE: The functionality is not implemented.
        3. DIM_MISMATCH: Dimension is not compatible for some computation. (eg. [[2,3], 4])

    Exceptions raised by modules in Class or Function packages must inherit this class.
    This class can be used as a root class catching all exceptions raised during various computations.
    """

    def __init__(self, pos: int, line: str, errno: Errno, **kwargs) -> None:
        super().__init__(pos, line, errno)
        self.__info: Dict[str, Any] = kwargs

    @property
    def msg(self) -> str:
        """
        Returns an error message.

        For detail, refer to the comments of Err.msg.
        Examples of additional error messages are as follows:
            1. KERNEL_ERR: [Kernel error] Python kernel reported an error during computation.
                                          Message from the kernel: division by zero
            2. NOT_IMPLE: [Not implemented] This functionality is not implemented yet. Sorry.
            3. DIM_MISMATCH: [Invalid operation] Dimension mismatch occurred during array construction.
                             Dimensions 1 and 0(base type) are not compatible.

        :return: Error message.
        """
        msg: str = self._line.rstrip() + '\n' + '~' * self._pos + '^\n'

        if self._errno == Errno.KERNEL_ERR:
            k_msg: str = self.__info['k_msg']
            msg += Printer.as_red(f'[Kernel error] Python kernel reported an error during computation.\n')
            msg += Printer.as_red(f'               Message from the kernel: {k_msg}')
        elif self._errno == Errno.NOT_IMPLE:
            msg += Printer.as_red(f'[Not implemented] This functionality is not implemented yet. Sorry.')
        elif self._errno == Errno.DIM_MISMATCH:
            op, dim1, dim2 = self.__info['op'], self.__info['dim1'], self.__info['dim2']
            msg += Printer.as_red(f'[Invalid operation] Dimension mismatch occurred during {op}.\n')
            msg += Printer.as_red(f'                    Dimensions {dim1} and {dim2} are not compatible.')
        return msg


"""
EXCEPTIONS FROM CLASS & FUNCTION MODULES.

All custom exception classes below must inherit InterpErr class.
"""


@final
class ArrErr(InterpErr):
    """
    Exceptions from Array class and its subclasses.

    There are four scenarios raising this exception.
        1. DIM_MISMATCH: Dimension is not compatible for some computation. (eg. [[2, 3], [4, 5]] %*% [[2, 3]])
        2. EMPTY_IDX: Index list for indexing is empty. (eg. x[[]])
        3. IDX_BOUND: Index is out of bound. (eg. x[2] where x = [1, 2])
        4. ASGN_N_MISS: # of elements in LHS and HHS do not match in case of assignment with indexing.
                        (eg. x[1:2] = [2, 3, 4] where x = [1, 2, 3].)

    This class is the end of inheritance. No further inheritance is allowed.
    """

    def __init__(self, errno: Errno, **kwargs) -> None:
        super().__init__(kwargs.get('pos', None), '', errno)
        self.__info: Dict[str, Any] = kwargs

    @property
    def msg(self) -> str:
        """
        Returns an error message.

        For detail, refer to the comments of Err.msg.
        Examples of additional error messages are as follows:
            1. DIM_MISMATCH: [Invalid operation] Dimension mismatch occurred during matrix multiplication.
                                                 Dimensions [2, 2] and [1, 2] are not compatible.
            2. EMPTY_IDX: [Invalid operation] Empty index list is not allowed.
            3. IDX_BOUND: [Invalid operation] Index out of bound. There is no element at 2.
            4. ASGN_N_MISS: [Semantic error] You provided 3 elements for assignment, but it needs (only) 2 elements.

        :return: Error message.
        """
        msg: str = self._line.rstrip() + '\n' + '~' * self._pos + '^\n'

        if self._errno == Errno.DIM_MISMATCH:
            op, dim1, dim2 = self.__info['op'], self.__info['dim1'], self.__info['dim2']
            msg += Printer.as_red(f'[Invalid operation] Dimension mismatch occurred during {op}.\n')
            msg += Printer.as_red(f'                    Dimensions {dim1} and {dim2} are not compatible.')
        elif self._errno == Errno.EMPTY_IDX:
            msg += Printer.as_red(f'[Invalid operation] Empty index list is not allowed.')
        elif self._errno == Errno.IDX_BOUND:
            idx: int = self.__info['idx']
            msg += Printer.as_red(f'[Invalid operation] Index out of bound. There is no element at {idx}.')
        elif self._errno == Errno.ASGN_N_MISS:
            need, given = self.__info['need'], self.__info['given']
            msg += Printer.as_red(f'[Semantic error] You provided {given} elements for assignment, '
                                  f'but it needs (only) {need} elements.')

        return msg


# TODO: Is complete? I don't think so...
@final
class FunErr(InterpErr):
    def __init__(self, errno: Errno, **kwargs) -> None:
        super().__init__(kwargs.get('pos', None), '', errno)
        self.__info: Dict[str, Any] = kwargs

    @property
    def msg(self) -> str:
        msg: str = self._line.rstrip() + '\n' + '~' * self._pos + '^\n'

        if self._errno == Errno.FUN_ERR:
            detail = self.__info['detail']
            msg += Printer.as_red('[Matrix error] Matrix module reported as error during computation.\n')
            msg += Printer.as_red(f'               Message from the module: {detail}')

        return msg


"""
COMMENT WRITTEN: 2021.3.3.
"""
