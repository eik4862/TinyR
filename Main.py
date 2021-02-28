from __future__ import annotations

import sys
from Core.Initialization import InitMan
from Util.Reader import Reader
from Util.Printer import Printer
from Core.Parser import Parser
from Core.SemanticChecker import SemanticChk
from Core.Interpreter import Interp
from Core.AST import AST
from Error.Exception import Err
from Core.Lexer import Lexer
from Class.Array import Mat

if __name__ == '__main__':
    InitMan.inst().init()

    while True:
        if Reader.inst().src == sys.stdin:
            Printer.inst().print('>> ', False)

        line: str = Reader.inst().readline()

        # Lexer.inst().test(line)
        ast: AST = Parser.inst().parse(line)
        SemanticChk.inst().chk(ast, line)
        Interp.inst().test(ast, line)

        # try:
        #     ast: AST = Parser.inst().parse(line)
        #
        #     if ast is None:
        #         continue
        #
        #     ast = SemanticChk.inst().chk(ast, line)
        #     res: str = Interp.inst().interp(ast, line)
        # except Err as e:
        #     Printer.inst().print(e.msg)
        # else:
        #     Printer.inst().print(res)
