from __future__ import annotations

from .TypeSymbol import *
from .Type import *


@final
class SymTab:
    __inst: ClassVar[SymTab] = None

    @classmethod
    def inst(cls, *args, **kwargs) -> SymTab:
        if not cls.__inst:
            SymTab.__inst = cls(*args, **kwargs)

        return cls.__inst

    def __init__(self) -> None:
        self.__kword: Dict[str, Tuple[TokT, Any]] = {
            'T': (TokT.BOOL, True), 'F': (TokT.BOOL, False), 'TRUE': (TokT.BOOL, True), 'FALSE': (TokT.BOOL, False)
        }

        self.__t: Dict[str, TSym] = {}
        self.__v: Dict[str, Any] = {}

    def lookup_kw(self, id_: str) -> Optional[Tuple[TokT, Any]]:
        return self.__kword.get(id_, None)

    def lookup_t(self, id_: str) -> Optional[TSym]:
        return self.__t.get(id_, None)

    def lookup_v(self, id_: str) -> Any:
        return self.__v.get(id_, None)

    def update_kw(self, id_: str, v: Any, t: TokT = TokT.FUN) -> NoReturn:
        self.__kword[id_] = (t, v)

    def update_t(self, id_: str, t: TSym) -> NoReturn:
        self.__t[id_] = t

    def update_v(self, id_: str, v: Any) -> NoReturn:
        self.__v[id_] = v
