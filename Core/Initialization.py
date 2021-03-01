from __future__ import annotations

import signal
from Util.Reader import *
from Function.Matrix import *


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

        CLib.init()
        MatFun.init()
