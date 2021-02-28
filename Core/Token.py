from __future__ import annotations

from typing import NoReturn, final, Any
from Core.Type import TokT


@final
class Tok:
    """
    Token class for parsing.
    """

    def __init__(self, t: TokT, v: Any = None, pos: int = -1) -> None:
        """
        Constructor of Tok class.

        :param t: Type of the token.
        :param v: Value of the token. (Default: None)
        :param pos: Position in the raw input where the token is derived. (Default: -1)
        """
        self.__t: TokT = t
        self.__v: Any = v
        self.__pos: int = pos

    """
    BUILT-INS
    """
    def __str__(self) -> str:
        return f'Token\n  @type : {self.__t.name}\n  @value: {str(self.__v)}\n  @pos  : {self.__pos}'

    __repr__ = __str__

    """
    GETTERS & SETTERS
    """
    @property
    def t(self) -> TokT:
        return self.__t

    @property
    def v(self) -> Any:
        return self.__v

    @property
    def pos(self) -> int:
        return self.__pos

    @t.setter
    def t(self, t: TokT) -> NoReturn:
        self.__t: TokT = t

    @v.setter
    def v(self, v: Any) -> NoReturn:
        self.__v: Any = v

    @pos.setter
    def pos(self, pos: int) -> NoReturn:
        self.__pos = pos
