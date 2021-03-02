from __future__ import annotations

from .Token import *
from .TypeSymbol import *


@final
class AST:
    """
    AST(Abstract Syntax Tree) class.

    Represents node in AST.
    For simplicity, there is no differentiation b/w terminal and internal nodes.

    This class is the end of inheritance. No further inheritance is allowed.
    """

    def __init__(self, tok: Tok, ch: List[AST] = None, t: TSym = None, call: Optional[Callable] = None,
                 lval: bool = False) -> None:
        # Corresponding token.
        self.__tok: Tok = tok
        # List of children.
        self.__ch: List[AST] = ch if ch is not None else []
        # Following three fields will be assigned by semantic checker. Refer to the comments of SemanticChk class.
        # Inferred type.
        self.__t: TSym = t
        # Function pointer which is to be called for interpretation.
        # This field is only used by nodes with function token or operator token.
        self.__call: Optional[Callable] = call
        # Flag indicating whether the node is l-value or not.
        self.__lval: bool = lval

    """
    BUILT-IN OVERRIDING
    """

    def __str__(self) -> str:
        return f'AST Node\n  @token type   : {self.__tok.t.name}\n  @token value  : {str(self.__tok.v)}\n' \
               f'  @inferred type: {self.__t}\n  @# of children: {len(self.__ch)}\n  @connection   : {self.__call}\n' \
               f'  @l-value      : {self.__lval}'

    __repr__ = __str__

    """
    GETTER & SETTER
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
