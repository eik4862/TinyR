from __future__ import annotations

from typing import NoReturn, ClassVar, final, Optional, List
from Core.Token import Tok
from Core.Type import TokT, OpT, Errno
from timeit import default_timer as timer
from Core.Lexer import Lexer
from Core.AST import AST
from Error.Exception import ParserErr
from Class.Function import Fun


@final
class Parser:
    """
    Parser class.

    Builds AST from the raw input string.
    It is implemented as singleton.
    """
    # Singleton object.
    __inst: ClassVar[Parser] = None

    @classmethod
    def inst(cls, *args, **kwargs) -> Parser:
        if not cls.__inst:
            Parser.__inst = cls(*args, **kwargs)

        return cls.__inst

    def __init__(self) -> None:
        self.__line: str = ''
        self.__curr_tok: Optional[Tok] = None

    def __eat(self) -> NoReturn:
        self.__curr_tok = Lexer.inst().next_tok()

    """
    PARSING LOGIC
    """

    def __expr(self) -> AST:
        """
        expr = or_expr (= or_expr)*
        """
        rt: AST = self.__or_expr()

        # Since assignment is right to left associative.
        if self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.ASGN:
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            return AST(rt_tok, [rt, self.__expr()])

        return rt

    def __or_expr(self) -> AST:
        """
        or_expr = and_expr (| and_expr)*
        """
        rt: AST = self.__and_expr()

        # Since or operation is left to right associative.
        while self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.OR:
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__and_expr()])

        return rt

    def __and_expr(self) -> AST:
        """
        and_expr = neg_expr (& neg_expr)*
        """
        rt: AST = self.__neg_expr()

        # Since and operation is left to right associative.
        while self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.AND:
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__neg_expr()])

        return rt

    def __neg_expr(self) -> AST:
        """
        neg_expr = !* comp_expr
        """
        if self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.NEG:
            rt_tok: Tok = self.__curr_tok

            self.__eat()

            return AST(rt_tok, [self.__neg_expr()])

        return self.__comp_expr()

    def __comp_expr(self) -> AST:
        """
        comp_expr = add_expr ((<|<=|>|>=|==|!=) add_expr)*
        """
        rt: AST = self.__add_expr()

        # Since comparison is left to right associative.
        while self.__curr_tok.t == TokT.OP and \
                self.__curr_tok.v in [OpT.LSS, OpT.LEQ, OpT.GRT, OpT.GEQ, OpT.EQ, OpT.NEQ]:
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__add_expr()])

        return rt

    def __add_expr(self) -> AST:
        """
        add_expr = mul_expr((+|-) mul_expr)*
        """
        rt: AST = self.__mul_expr()

        # Since addition and subtraction are left to right associative.
        while self.__curr_tok.t == TokT.OP and (self.__curr_tok.v == OpT.ADD or self.__curr_tok.v == OpT.SUB):
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__mul_expr()])

        return rt

    def __mul_expr(self) -> AST:
        """
        mul_expr = rem_expr ((*|/) rem_expr)*
        """
        rt: AST = self.__rem_expr()

        # Since multiplication and division are left to right associative.
        while self.__curr_tok.t == TokT.OP and (self.__curr_tok.v == OpT.MUL or self.__curr_tok.v == OpT.DIV):
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__rem_expr()])

        return rt

    def __rem_expr(self) -> AST:
        """
        rem_expr = seq_expr ((%*%|%%|%/%) seq_expr)*
        """
        rt: AST = self.__seq_expr()

        # Since matrix multiplication, mod operation, and quotient operation are left to right associative.
        while self.__curr_tok.t == TokT.OP and self.__curr_tok.v in [OpT.MATMUL, OpT.MOD, OpT.QUOT]:
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__seq_expr()])

        return rt

    def __seq_expr(self) -> AST:
        """
        seq_expr = pls_expr(:pls_expr)*
        """
        rt: AST = self.__pls_expr()

        # Since sequence construction operation is left to right associative.
        while self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.SEQ:
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__pls_expr()])

        return rt

    def __pls_expr(self) -> AST:
        """
        pls_expr = (+|-)* exp_expr
        """
        if self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.ADD:
            rt_tok: Tok = self.__curr_tok

            self.__eat()

            return AST(rt_tok, [self.__pls_expr()])
        elif self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.SUB:
            rt_tok: Tok = self.__curr_tok

            self.__eat()

            return AST(rt_tok, [self.__pls_expr()])

        return self.__exp_expr()

    def __exp_expr(self) -> AST:
        """
        exp_expr = idx_expr (^ idx_expr)*
        """
        rt: AST = self.__idx_expr()

        # Since exponentiation is right to left associative.
        if self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.EXP:
            rt_tok: Tok = self.__curr_tok

            self.__eat()

            return AST(rt_tok, [rt, self.__exp_expr()])

        return rt

    def __idx_expr(self) -> AST:
        """
        idx_expr = term([expr? (, expr?)*])*

        :raise ParserErr: Input without closing bracket(]) raises exception with errno NCLOSED_PARN.
        """
        rt: AST = self.__term()

        # Since indexing is left to right associative.
        while self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.IDX:
            rt_tok: Tok = self.__curr_tok
            idx: List[AST] = []

            self.__eat()

            if self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.RBRA:
                idx.append(AST(Tok(TokT.VOID, pos=self.__curr_tok.pos)))
                self.__eat()

                rt = AST(rt_tok, [rt, *idx])

                continue
            elif self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.COM:
                idx.append(AST(Tok(TokT.VOID, pos=self.__curr_tok.pos)))
            else:
                idx.append(self.__expr())

            while self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.COM:
                self.__eat()

                if self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.RBRA:
                    idx.append(AST(Tok(TokT.VOID, pos=self.__curr_tok.pos)))

                    break
                elif self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.COM:
                    idx.append(AST(Tok(TokT.VOID, pos=self.__curr_tok.pos)))
                    self.__eat()
                else:
                    idx.append(self.__expr())

            if self.__curr_tok.t != TokT.OP or self.__curr_tok.v != OpT.RBRA:
                raise ParserErr(rt_tok.pos, self.__line, Errno.NCLOSED_PARN)

            self.__eat()

            rt = AST(rt_tok, [rt, *idx])

            continue

        return rt

    def __term(self) -> AST:
        """
        term = (expr)
             | arr_expr
             | strt_expr
             | fun_expr
             | Numeric
             | Boolean
             | String
             | Variable

        :raise ParserErr: Input without closing parenthesis()) raises exception with errno NCLOSED_PARN.
        :raise ParserErr: Incomplete input raises exception with errno INCOMP_EXPR.
        :raise ParserErr: Any other 'non-terminal' tokens encountered at this level raise exception
                          with errno INVALID_TOK.
        """
        rt_tok: Tok = self.__curr_tok

        if rt_tok.t == TokT.OP and rt_tok.v == OpT.LPAR:
            self.__eat()

            rt: AST = self.__expr()

            if self.__curr_tok.t != TokT.OP or self.__curr_tok.v != OpT.RPAR:
                raise ParserErr(rt_tok.pos, self.__line, Errno.NCLOSED_PARN)

            self.__eat()

            return rt
        elif rt_tok.t == TokT.OP and rt_tok.v == OpT.LBRA:
            return self.__arr_expr()
        elif rt_tok.t == TokT.OP and rt_tok.v == OpT.LCUR:
            return self.__strt_expr()
        elif rt_tok.t == TokT.FUN:
            return self.__fun_expr()
        elif rt_tok.t in [TokT.NUM, TokT.BOOL, TokT.STR, TokT.VAR]:
            self.__eat()

            return AST(rt_tok)
        else:
            if self.__curr_tok.t == TokT.EOF:
                raise ParserErr(self.__curr_tok.pos, self.__line, Errno.INCOMP_EXPR)
            else:
                raise ParserErr(self.__curr_tok.pos, self.__line, Errno.INVALID_TOK)

    def __arr_expr(self) -> AST:
        """
        arr_expr = [(expr (, expr)*)?]

        :raise ParserErr: Input without closing bracket(]) raises exception with errno NCLOSED_PARN.
        """
        rt_tok: Tok = self.__curr_tok
        elem: List[AST] = []

        self.__eat()

        if self.__curr_tok.t != TokT.OP or self.__curr_tok.v != OpT.RBRA:
            elem.append(self.__expr())

        while self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.COM:
            self.__eat()
            elem.append(self.__expr())

        if self.__curr_tok.t != TokT.OP or self.__curr_tok.v != OpT.RBRA:
            raise ParserErr(rt_tok.pos, self.__line, Errno.NCLOSED_PARN)

        self.__eat()

        return AST(Tok(TokT.ARR, pos=rt_tok.pos), elem)

    def __strt_expr(self) -> AST:
        """
        strt_expr = {(id : expr (, id : expr)*)?}
        """
        rt_tok: Tok = self.__curr_tok
        elem: List = []

        self.__eat()

        if self.__curr_tok.t != TokT.OP or self.__curr_tok.v != OpT.RCUR:
            if self.__curr_tok.t != TokT.VAR:
                raise ParserErr(self.__curr_tok.pos, self.__line, Errno.MEMID_MISS)

            id_tok: Tok = self.__curr_tok

            self.__eat()

            if self.__curr_tok.t != TokT.OP or self.__curr_tok.v != OpT.SEQ:
                raise ParserErr(self.__curr_tok.pos, self.__line, Errno.INCOMP_EXPR)

            self.__eat()
            elem.append(AST(Tok(TokT.MEM, id_tok.v, id_tok.pos), [self.__expr()]))

            while self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.COM:
                self.__eat()

                if self.__curr_tok.t != TokT.VAR:
                    raise ParserErr(self.__curr_tok.pos, self.__line, Errno.MEMID_MISS)

                id_tok: Tok = self.__curr_tok

                self.__eat()

                if self.__curr_tok.t != TokT.OP or self.__curr_tok.v != OpT.SEQ:
                    raise ParserErr(self.__curr_tok.pos, self.__line, Errno.INCOMP_EXPR)

                self.__eat()
                elem.append(AST(Tok(TokT.MEM, id_tok.v, id_tok.pos), [self.__expr()]))

        if self.__curr_tok.t != TokT.OP or self.__curr_tok.v != OpT.RCUR:
            raise ParserErr(rt_tok.pos, self.__line, Errno.NCLOSED_PARN)

        self.__eat()

        return AST(Tok(TokT.STRT, pos=rt_tok.pos), elem)

    def __fun_expr(self) -> AST:
        """
        fun_expr = id ((expr (, expr)*)?)
                 | id ((id = expr (, id = expr)*)?)
                 | id (expr (, expr)*, id = expr (, id = expr)*)
        """
        rt_tok: Tok = self.__curr_tok
        fun: Fun = rt_tok.v
        args: List[AST] = []
        kwargs: List[AST] = []

        self.__eat()

        if self.__curr_tok.t != TokT.OP or self.__curr_tok.v != OpT.LPAR:
            raise ParserErr(rt_tok.pos, self.__line, Errno.FUN_CALL_MISS)

        paren_start: int = self.__curr_tok.pos

        self.__eat()

        if self.__curr_tok.t != TokT.OP or self.__curr_tok.v != OpT.RPAR:
            if self.__curr_tok.t != TokT.VAR or not fun.is_kw(self.__curr_tok.v):
                args.append(self.__expr())

                while self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.COM:
                    self.__eat()

                    if self.__curr_tok.t == TokT.VAR and fun.is_kw(self.__curr_tok.v):
                        break
                    elif self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.RPAR:
                        raise ParserErr(self.__curr_tok.pos, self.__line, Errno.INCOMP_EXPR)

                    args.append(self.__expr())

                if self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.RPAR:
                    self.__eat()

                    return AST(rt_tok, args)

            if self.__curr_tok.t != TokT.VAR or not fun.is_kw(self.__curr_tok.v):
                raise ParserErr(paren_start, self.__line, Errno.NCLOSED_PARN)

            id_tok: Tok = self.__curr_tok

            self.__eat()

            if self.__curr_tok.t != TokT.OP or self.__curr_tok.v != OpT.ASGN:
                raise ParserErr(self.__curr_tok.pos, self.__line, Errno.INCOMP_EXPR)

            self.__eat()
            kwargs.append(AST(Tok(TokT.KWARG, id_tok.v, id_tok.pos), [self.__expr()]))

            while self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.COM:
                self.__eat()

                if self.__curr_tok.t != TokT.VAR or not fun.is_kw(self.__curr_tok.v):
                    raise ParserErr(self.__curr_tok.pos, self.__line, Errno.KWARG_MISS)

                id_tok = self.__curr_tok

                self.__eat()

                if self.__curr_tok.t != TokT.OP or self.__curr_tok.v != OpT.ASGN:
                    raise ParserErr(self.__curr_tok.pos, self.__line, Errno.INCOMP_EXPR)

                self.__eat()
                kwargs.append(AST(Tok(TokT.KWARG, id_tok.v, id_tok.pos), [self.__expr()]))

        if self.__curr_tok.t != TokT.OP or self.__curr_tok.v != OpT.RPAR:
            raise ParserErr(paren_start, self.__line, Errno.NCLOSED_PARN)

        self.__eat()

        return AST(rt_tok, args + kwargs)

    def parse(self, line: str) -> Optional[AST]:
        """
        Builds AST from the input raw string.
        AST building utilizes LL parsing strategy.

        :param line: Raw input string to be parsed.

        :return: Built AST.

        :raise ParserErr: If there are left tokens after applying all grammar, it raises exception
                          with errno INVALID_TOK.
        """
        self.__line = line

        Lexer.inst().init(line)

        self.__curr_tok = Lexer.inst().next_tok()

        if self.__curr_tok.t == TokT.EOF:
            return None

        ast: AST = self.__expr()

        if self.__curr_tok.t != TokT.EOF:
            raise ParserErr(self.__curr_tok.pos, self.__line, Errno.INVALID_TOK)

        return ast

    """
    DEBUGGING
    """

    def test(self, line: str) -> NoReturn:
        start: float = timer()
        rt: AST = self.parse(line)
        end: float = timer()

        print('------ TEST SUMMARY ------')
        print(f'  @module : PARSER')
        print(f'  @elapsed: {round((end - start) * 1e4, 4)}ms')
        print(f'  @sample : {line}')
        print('--------- RESULT ---------')
        print('  * Postorder traversal')
        self.__test_hlpr(rt, 0)

    def __test_hlpr(self, ast: AST, cnt: int) -> int:
        for node in ast.ch:
            cnt = self.__test_hlpr(node, cnt)

        print(f'[{cnt}] {ast.tok}')

        return cnt + 1
