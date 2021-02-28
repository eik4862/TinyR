from __future__ import annotations

from typing import NoReturn, ClassVar, final, Optional
from Core.Type import TokT, Errno, OpT, T
from timeit import default_timer as timer
from Core.AST import AST
from Class.Array import Arr, Vec
from Class.ArrayFactory import ArrFact
from Error.Exception import InterpErr
from Util.Printer import Printer
from Core.SymbolTable import SymTab


@final
class Interp:
    """
    Interpreter class.

    Traverses through AST and interprets.
    It is implemented as singleton.
    """
    # Singleton object.
    __inst: ClassVar[Interp] = None

    @classmethod
    def inst(cls, *args, **kwargs) -> Interp:
        if not cls.__inst:
            Interp.__inst = cls(*args, **kwargs)

        return cls.__inst

    def __init__(self) -> None:
        self.__ast: Optional[AST] = None
        self.__line: str = ''

    """
    INTERPRETING LOGIC
    """

    def __interp_op(self, ast: AST) -> NoReturn:
        if ast.tok.v == OpT.EXP:
            self.__interp_hlpr(ast.ch[1])
            self.__interp_hlpr(ast.ch[0])
        else:
            for node in ast.ch:
                self.__interp_hlpr(node)

        try:
            ast.tok.v = ast.call(*[node.tok.v for node in ast.ch])
        except InterpErr as e:
            e.pos = ast.tok.pos
            e.line = self.__line

            raise e
        except Exception as e:
            raise InterpErr(ast.tok.pos, self.__line, Errno.KERNEL_ERR, k_msg=str(e))

    def __interp_asgn(self, ast: AST) -> NoReturn:
        self.__interp_hlpr(ast.ch[1])
        self.__interp_hlpr(ast.ch[0])

        if type(ast.ch[0].tok.v) == str:
            SymTab.inst().update_v(ast.ch[0].tok.v, ast.ch[1].tok.v)
            ast.tok.v = ast.ch[1].tok.v
        else:
            id_, idx = ast.ch[0].tok.v
            tar, val = SymTab.inst().lookup_v(id_), ast.ch[1].tok.v

            if ast.ch[0].t.t == T.ARR and ast.ch[1].t.t == T.ARR:
                val = val.promote(ast.ch[0].t.dept - val.dept)

            try:
                if isinstance(tar, Arr):
                    SymTab.inst().update_v(id_, tar.update(idx, val))
                else:
                    # A little trick here.
                    # When base type is indexed and then assigned,
                    # the target(base type) needs AT LEAST one promotion.
                    # Then it may be further promoted internally.
                    # After the assignment, we need to degrade it back to keep base type as base type.
                    tar = Vec([tar]).update(idx, val)

                    SymTab.inst().update_v(id_, tar.degrade(tar.dept))
            except InterpErr as e:
                e.pos = ast.tok.pos
                e.line = self.__line

                raise e

            ast.tok.v = ast.ch[1].tok.v

    def __interp_hlpr(self, ast: AST) -> NoReturn:
        """
        Traverses AST and interprets.

        :param ast: AST to be interpreted.

        :raise InterpErr: Expression containing functionality which is not implemented yet raises exception
                          with errno NOT_IMPLE.
        :raise InterpErr: If kernel raises exception during computation, it raises exception with errno KERNEL_ERR.
        """
        # Lookup symbol table and retrieve assigned value.
        if ast.tok.t == TokT.VAR and not ast.lval:
            ast.tok.v = SymTab.inst().lookup_v(ast.tok.v)

        # OP token with ASGN or EXP is right to left associative.
        # Thus, the rightmost child should be interpreted first.
        elif ast.tok.t == TokT.OP:
            if ast.tok.v == OpT.ASGN:
                self.__interp_asgn(ast)
            else:
                self.__interp_op(ast)
        elif ast.tok.t == TokT.ARR:
            for node in ast.ch:
                self.__interp_hlpr(node)

            try:
                ast.tok.v = ArrFact.create(ast)
            except InterpErr as e:
                e.line = self.__line

                raise e
        elif ast.tok.t == TokT.FUN:
            for node in ast.ch:
                self.__interp_hlpr(node)

            try:
                ast.tok.v = ast.call(*[node.tok.v for node in ast.ch])
            except InterpErr as e:
                e.pos = ast.tok.pos
                e.line = self.__line

                raise e
            except Exception as e:
                raise InterpErr(ast.tok.pos, self.__line, Errno.KERNEL_ERR, k_msg=str(e))

    def interp(self, ast: AST, line: str) -> str:
        """
        Interprets AST.

        :param ast: AST to be interpreted.
        :param line: Raw input string.

        :return: Formatted interpretation result.
        """
        self.__ast = ast
        self.__line = line

        self.__interp_hlpr(self.__ast)

        return Printer.inst().format(self.__ast.tok.v)

    """
    DEBUGGING
    """

    def test(self, ast: AST, line: str) -> NoReturn:
        start: float = timer()
        res: str = self.interp(ast, line)
        end: float = timer()

        print('------ TEST SUMMARY ------')
        print(f'  @module : INTERPRETER')
        print(f'  @elapsed: {round((end - start) * 1e4, 4)}ms')
        print(f'  @sample : {line.rstrip()}')
        print(f'  @result : {res}')
        print(f'  @type   : {self.__ast.t}')
