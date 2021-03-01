from __future__ import annotations

from Util.Printer import *


@final
class Strt:
    def __init__(self, elem: Dict[str, Any], id_: List[str]) -> None:
        self.__elem: Dict[str, Any] = elem
        self.__id: List[str] = id_

    def format(self, w: int, h: int, it_w: int, h_remain: bool = False) -> Union[str, Tuple[str, int]]:
        if len(self.__elem) == 0:
            return ('Empty struct', 1) if h_remain else 'Empty struct'

        buf: str = ''

        for i in range(len(self.__id)):
            buf += f'${self.__id[i]}\n'

            it_str, h = Printer.inst().format(self.__elem[self.__id[i]], w, h - 1, it_w, True)
            buf += it_str + '\n\n'
            h -= 1

            if h <= 0:
                buf.rstrip()
                buf += f'\n... and {len(self.__id) - i - 1} more members in this struct.'

                break

        return (buf.rstrip(), h) if h_remain else buf.rstrip()
