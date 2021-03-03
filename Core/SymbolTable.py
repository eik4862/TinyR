from __future__ import annotations

from .TypeSymbol import *
from .Type import *


@final
class SymTab:
    """
    Symbol table class.

    During interpretation process, some information needs to be tracked and symbol table does this tracking.
    This class manages three tables: keyword table, type table, and symbol table.

    Keyword table is used by lexer to identify keywords like 'TRUE' and built-in function calls like 'idMat'.
    It uses keyword string as a key and has two entries:
    token type and the value corresponds to the keyword or built-in.
    Note that only information of keywords are hard coded here.
    Since built-ins are encapsulated in Function package, hard coding their information here will be messy.
    Their information will be registered by initializer when the interpreter starts to run.
    For detail, refer to the comments of Initialization module.

    Type table is used by semantic checker to infer types of variables.
    It uses the id of variable as a key and has one entry, the type of the variable.
    Symbol table is used by interpreter to load values assigned to variables.
    It uses the id of variable as a key and has one entry, the value of the variable.
    Since this language does not support scoping (all variables are in global scope)
    there is no need to store additional information in type table and symbol table.

    This class is implemented as a singleton. The singleton object will be instantiated at its first call.
    This class is the end of inheritance. No further inheritance is allowed.
    """
    # Singleton object.
    __inst: ClassVar[SymTab] = None

    @classmethod
    def inst(cls, *args, **kwargs) -> SymTab:
        if not cls.__inst:
            SymTab.__inst = cls(*args, **kwargs)

        return cls.__inst

    def __init__(self) -> None:
        # Keyword table.
        self.__kword: Dict[str, Tuple[TokT, Any]] = {
            'T': (TokT.BOOL, True), 'F': (TokT.BOOL, False), 'TRUE': (TokT.BOOL, True), 'FALSE': (TokT.BOOL, False)
        }
        # Type table.
        self.__t: Dict[str, TSym] = {}
        # Symbol table.
        self.__v: Dict[str, Any] = {}

    """
    LOOKUP & UPDATE
    
    Lookup function takes key and returns the stored entries.
    If it cannot find entry with the passed key, it returns None instead.
    
    Update function takes key and entry information and stores it.
    If entries with the passed key already exist in the table, then they will be overwritten.
    """

    def lookup_kw(self, k: str) -> Optional[Tuple[TokT, Any]]:
        return self.__kword.get(k, None)

    def lookup_t(self, k: str) -> Optional[TSym]:
        return self.__t.get(k, None)

    def lookup_v(self, k: str) -> Any:
        return self.__v.get(k, None)

    def update_kw(self, k: str, v: Any, t: TokT = TokT.FUN) -> NoReturn:
        self.__kword[k] = (t, v)

    def update_t(self, k: str, t: TSym) -> NoReturn:
        self.__t[k] = t

    def update_v(self, k: str, v: Any) -> NoReturn:
        self.__v[k] = v


"""
COMMENT WRITTEN: 2021.3.2.
"""
