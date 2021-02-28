from __future__ import annotations

from typing import NoReturn, final, List, Callable, Optional
from Core.Token import Tok
from Core.TypeSymbol import TSym


@final
class AST:
    """
    Abstract Syntax Tree class for interpretation.
    """

    def __init__(self, tok: Tok, ch: List[AST] = None, t: TSym = None, call: Optional[Callable] = None,
                 lval: bool = False) -> None:
        """
        Constructor of AST class.

        Generally, tok and ch will be given at its first construction.
        Then semantic checker will fill in other fields.

        :param tok: Token which corresponds to this node.
        :param ch: Pointer to the child AST nodes. (Default: [])
        :param t: Inferred type of this node. (Default: None)
        :param call: Pointer to the function which will be called during interpretation. (Default: None)
        :param lval: Flag indicating l-value for assignment. (Default: False)
        """
        self.__tok: Tok = tok
        self.__ch: List[AST] = ch if ch is not None else []
        self.__t: TSym = t
        self.__call: Optional[Callable] = call
        self.__lval: bool = lval

    """
    BUILT-INS
    """
    def __str__(self) -> str:
        return f'AST Node\n  @token type   : {self.__tok.t.name}\n  @token value  : {self.__tok.v}\n' \
               f'  @inferred type: {self.__t}\n  @# of children: {len(self.__ch)}\n  @connection   : {self.__call}\n' \
               f'  @l-value      : {self.__lval}'

    __repr__ = __str__

    """
    GETTERS & SETTERS
    """
    @property
    def tok(self) -> Tok:
        return self.__tok

    @property
    def ch(self) -> List[AST]:
        return self.__ch

    @property
    def t(self) -> TSym:
        return self.__t

    @property
    def call(self) -> Optional[Callable]:
        return self.__call

    @property
    def lval(self) -> bool:
        return self.__lval

    @tok.setter
    def tok(self, tok: Tok) -> NoReturn:
        self.__tok = tok

    @ch.setter
    def ch(self, ch: List[AST]) -> NoReturn:
        self.__ch = ch

    @t.setter
    def t(self, t: TSym) -> NoReturn:
        self.__t = t

    @call.setter
    def call(self, hndl: Callable) -> NoReturn:
        self.__call = hndl

    @lval.setter
    def lval(self, lval: bool) -> NoReturn:
        self.__lval = lval
