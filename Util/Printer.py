from __future__ import annotations

import sys
from typing import *


@final
class Printer:
    """
    Printer class.

    Simple wrapper for write method with useful utils.
    It is implemented as singleton.
    """
    # Singleton object.
    __inst: ClassVar[Printer] = None
    # Special characters for red output.
    __RED_BGN: Final[ClassVar[str]] = '\x1b[1;31m'
    __RED_END: Final[ClassVar[str]] = '\x1b[0m'

    @classmethod
    def inst(cls, *args, **kwargs) -> Printer:
        if not cls.__inst:
            Printer.__inst = cls(*args, **kwargs)

        return cls.__inst

    def __init__(self, dest: TextIO = sys.stdout, w: int = 100, h: int = 100, it_w: int = 10) -> None:
        """
        Constructor of Printer class.

        :param dest: Destination. (Default: sys.stdout)
        :param w: Width of display. (Default: 100)
        :param h: Height of display. (Default: 100)
        :param it_w: Maximum width of element to be displayed. Elements exceeding this width will be abbreviated.
                     (Default: 10)
        """
        self.__dest: Final[TextIO] = dest
        self.__w: Final[int] = w
        self.__h: Final[int] = h
        self.__it_w: Final[int] = it_w

    """
    UTILS
    """

    @classmethod
    def as_red(cls, line: str) -> str:
        return cls.__RED_BGN + line + cls.__RED_END

    def format(self, obj: Any, w: int = None, h: int = None, it_w: int = None, h_remain: bool = False) \
            -> Union[str, Tuple[str, int]]:
        """
        Format object like R.
        Object whose string expression is too long will be abbreviated using three dots(...).
        String will be enclosed by double quote(").
        Object with base types will be formatted directly with preceding '[1]'.
        Other objects will be formatted by calling custom format method.
        If w, h, and it_w are not given, it uses display width, height, and maximum element width as default value.

        :param obj: Object to be formatted.
        :param w: Width of the output. (Default: self.__w)
        :param h: Height of the output. (Default: self.__h)
        :param it_w: Maximum width of the element in the object. (Default: self.__it_w)

        :return: Formatted object string expression.
        """
        if w is None:
            w = self.__w

        if h is None:
            h = self.__h

        if it_w is None:
            it_w = self.__it_w

        if h <= 0:
            return ('', h) if h_remain else ''

        if type(obj) == bool:
            return ('[1] ' + str(obj), h - 1) if h_remain else '[1] ' + str(obj)
        elif type(obj) == int or type(obj) == float:
            v_str: str = str(obj)

            if len(v_str) > w:
                v_str = v_str[:(w - 3)] + '...'

            return ('[1] ' + v_str, h - 1) if h_remain else '[1] ' + v_str
        elif type(obj) == str:
            if len(obj) > w - 2:
                obj = obj[:(w - 5)] + '...'

            return ('[1] "' + obj + '"', h - 1) if h_remain else '[1] "' + obj + '"'
        else:
            return obj.format(w, h, it_w, h_remain)

    """
    PRINT LOGIC
    """

    def print(self, line: str, newline: bool = True) -> NoReturn:
        """
        Print string.

        :param line: String to be printed.
        :param newline: If true, attach trailing newline character.
        """
        self.__dest.write(line + '\n' if newline else line)
