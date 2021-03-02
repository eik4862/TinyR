from __future__ import annotations

from .Type import *


@final
class Tok:
    """
    Token class.

    This class is the end of inheritance. No further inheritance is allowed.
    """

    def __init__(self, t: TokT, v: Any = None, pos: int = -1) -> None:
        # Token type.
        self.__t: TokT = t
        # Token value.
        # For array token and struct token, this field will be assigned by interpreter.
        # For void token and EOF token, this field will never be assigned.
        # For other tokens, this field will be assigned at the time of instantiation by lexer.
        self.__v: Any = v
        # Position in the raw input string where the token is derived.
        self.__pos: int = pos

    """
    BUILT-IN OVERRIDING
    """

    def __str__(self) -> str:
        return f'Token\n  @type : {self.__t.name}\n  @value: {str(self.__v)}\n  @pos  : {self.__pos}'

    __repr__ = __str__

    """
    GETTER & SETTER
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


"""
COMMENT WRITTEN: 2021.3.2.
"""
