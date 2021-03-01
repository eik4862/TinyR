from __future__ import annotations

from Core.TypeSymbol import *


@final
class Fun:
    def __init__(self, call: Callable, t: FunTSym, kwargs: List[Tuple[str, str]] = None) -> None:
        self.__call: Callable = call
        self.__t: FunTSym = t

        if kwargs is None:
            self.__kwargs: List[Tuple[str, str]] = []
        else:
            self.__kwargs: List[Tuple[str, str]] = kwargs

    def is_kw(self, id_: str) -> bool:
        for k, _ in self.__kwargs:
            if k == id_:
                return True

        return False

    @property
    def call(self) -> Callable:
        return self.__call

    @property
    def t(self) -> FunTSym:
        return self.__t

    @property
    def kwargs(self) -> List[Tuple[str, str]]:
        return self.__kwargs

    @property
    def nargs(self) -> int:
        return len(self.__t.args) - len(self.__kwargs)

    @property
    def nkwargs(self) -> int:
        return len(self.__kwargs)
