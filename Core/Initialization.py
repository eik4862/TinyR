from __future__ import annotations

import sys
import signal
from Util.Printer import Printer
from Util.Reader import Reader
from typing import NoReturn, ClassVar, final, TextIO
from Class.Array import Mat
from Function.MatrixFunction import MatFun


@final
class InitMan:
    __inst: ClassVar[InitMan] = None

    @classmethod
    def inst(cls, *args, **kwargs) -> InitMan:
        if not cls.__inst:
            InitMan.__inst = cls(*args, **kwargs)

        return cls.__inst

    @staticmethod
    def sigint_handler(sig, frame):
        print(f'Received SIGINT({sig}). Terminate.')

        sys.exit()

    @staticmethod
    def sigtstp_handler(sig, frame):
        print(f'Received SIGTSTP({sig}). Terminate.')

        sys.exit()

    def __init__(self) -> None:
        pass

    def init(self, src: TextIO = sys.stdin, dest: TextIO = sys.stdout) -> NoReturn:
        signal.signal(signal.SIGINT, InitMan.sigint_handler)
        signal.signal(signal.SIGTSTP, InitMan.sigtstp_handler)

        Reader.inst(src=src)
        Printer.inst(dest=dest)

        Mat.init()
        MatFun.init()
