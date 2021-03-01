from __future__ import annotations

import sys
from typing import *


@final
class Reader:
    """
    Reader class.

    Simple wrapper for readline method with useful utils.
    It is implemented as singleton.
    """
    # Singleton object.
    __inst: ClassVar[Reader] = None

    @classmethod
    def inst(cls, *args, **kwargs) -> Reader:
        if not cls.__inst:
            Reader.__inst = cls(*args, **kwargs)

        return cls.__inst

    def __init__(self, src: TextIO = sys.stdin) -> None:
        """
        Constructor of Reader class.

        :param src: Source. (Default: sys.stdin)
        """
        self.__src: Final[TextIO] = src

    """
    READING LOGIC
    """

    def readline(self) -> str:
        """
        Read one line including trailing newline character.

        :return: Read line.
        """
        return self.__src.readline()

    """
    GETTERS & SETTERS
    """

    @property
    def src(self) -> TextIO:
        return self.__src
