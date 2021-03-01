from __future__ import annotations

from typing import final, NoReturn, Dict, Any
from Core.Type import Errno
from Util.Printer import Printer


class Err(Exception):
    """
    Exception class.

    This supplies interface for other exception classes.
    """

    def __init__(self, pos: int, line: str, errno: Errno) -> None:
        """
        Constructor of Err class.

        :param pos: The position in the raw input string where the exception is raised.
        :param line: Raw input string.
        :param errno: Error code.
        """
        self._pos: int = pos
        self._line: str = line
        self._errno: Errno = errno

    """
    GETTERS & SETTERS
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
        This method should return formatted error message.
        The format may be different according to the errno.
        Use Printer.as_red to display error message in red color.

        :return: Formatted error message.
        """
        return ''

    @pos.setter
    def pos(self, pos: int) -> NoReturn:
        self._pos = pos

    @line.setter
    def line(self, line: str) -> NoReturn:
        self._line = line


@final
class ParserErr(Err):
    def __init__(self, pos: int, line: str, errno: Errno) -> None:
        super().__init__(pos, line, errno)

    @property
    def msg(self) -> str:
        msg: str = self._line + '~' * self._pos + '^' + '\n'

        if self._errno == Errno.INVALID_TOK:
            msg += Printer.as_red(f'[Invalid syntax] Unexpected token encountered at {self._pos}.')
        elif self._errno == Errno.NCLOSED_PARN:
            msg += Printer.as_red(f'[Invalid syntax] Parenthesis(quote) at {self._pos} is not closed.')
        elif self._errno == Errno.INCOMP_EXPR:
            msg += Printer.as_red('[Invalid syntax] Expression is incomplete.')
        elif self._errno == Errno.FUN_CALL_MISS:
            msg += Printer.as_red(f'[Invalid syntax] Function call at {self._pos} is not complete.')
        elif self._errno == Errno.KWARG_MISS:
            msg += Printer.as_red('[Invalid syntax] Only keyword arguments can be placed here.')
        elif self._errno == Errno.MEMID_MISS:
            msg += Printer.as_red('[Invalid syntax] Member id is missing.')

        return msg


@final
class SemanticChkErr(Err):
    def __init__(self, pos: int, line: str, errno: Errno, **kwargs) -> None:
        super().__init__(pos, line, errno)
        self.__info: Dict[str, Any] = kwargs

    @property
    def msg(self) -> str:
        msg: str = self._line + '~' * self._pos + '^' + '\n'

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
            msg += Printer.as_red(
                f'[Semantic error] The left hand side of assignment at {self._pos} cannot be a l-value.')
        elif self._errno == Errno.ID_DUP:
            id_:str = self.__info['id_']
            msg += Printer.as_red(f'[Semantic error] Struct id {id_} is duplicated.')

        return msg


class InterpErr(Err):
    def __init__(self, pos: int, line: str, errno: Errno, **kwargs) -> None:
        super().__init__(pos, line, errno)
        self.__info: Dict[str, Any] = kwargs

    @property
    def msg(self) -> str:
        msg: str = self._line + '~' * self._pos + '^' + '\n'

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


@final
class ArrErr(InterpErr):
    def __init__(self, errno: Errno, **kwargs) -> None:
        super().__init__(kwargs.get('pos', None), '', errno)
        self.__info: Dict[str, Any] = kwargs

    @property
    def msg(self) -> str:
        msg: str = self._line + '~' * self._pos + '^' + '\n'

        if self._errno == Errno.DIM_MISMATCH:
            op, dim1, dim2 = self.__info['op'], self.__info['dim1'], self.__info['dim2']
            msg += Printer.as_red(f'[Invalid operation] Dimension mismatch occurred during {op}.\n')
            msg += Printer.as_red(f'                    Dimensions {dim1} and {dim2} are not compatible.')
        elif self._errno == Errno.EMPTY_IDX:
            msg += Printer.as_red(f'[Invalid operation] Empty index is not allowed.')
        elif self._errno == Errno.IDX_BOUND:
            idx: int = self.__info['idx']
            msg += Printer.as_red(f'[Invalid operation] Index out of bound. There is no {idx}th element.')
        elif self._errno == Errno.ASGN_N_MISS:
            need, given = self.__info['need'], self.__info['given']
            msg += Printer.as_red(f'[Semantic error] You provided {given} elements for assignment, '
                                  f'but it needs (only) {need} elements.')

        return msg


@final
class FunErr(InterpErr):
    def __init__(self, errno: Errno, **kwargs) -> None:
        super().__init__(kwargs.get('pos', None), '', errno)
        self.__info: Dict[str, Any] = kwargs

    @property
    def msg(self) -> str:
        msg: str = self._line + '~' * self._pos + '^' + '\n'

        if self._errno == Errno.FUN_ERR:
            detail = self.__info['detail']
            msg += Printer.as_red('[Matrix error] Matrix module reported as error during computation.\n')
            msg += Printer.as_red(f'               Message from the module: {detail}')

        return msg
