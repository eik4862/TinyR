from __future__ import annotations

from .Lexer import *
from .AST import *
from Class.Function import *
from Error.Exception import *


@final
class Parser:
    """
    Parser class.

    Builds AST from the raw input string.
    It takes tokens from lexer and forms connections b/w them following the grammar.

    This class is implemented as a singleton. The singleton object will be instantiated at its first call.
    This class is the end of inheritance. No further inheritance is allowed.
    """
    # Singleton object.
    __inst: ClassVar[Parser] = None

    @classmethod
    def inst(cls, *args, **kwargs) -> Parser:
        if not cls.__inst:
            Parser.__inst = cls(*args, **kwargs)

        return cls.__inst

    def __init__(self) -> None:
        # Raw input string.
        self.__line: str = ''
        # Token received from lexer. This field is automatically managed internally.
        self.__curr_tok: Optional[Tok] = None

    """
    HELPER FOR PARSING LOGIC
    
    This logic is for internal use only.
    """

    def __eat(self) -> NoReturn:
        """
        Get next token to process from lexer and set the received one as a current token.
        """
        self.__curr_tok = Lexer.inst().next_tok()

    """
    PARSING LOGIC
    
    It employs LL(Leftmost derivation) parsing strategy.
    Precedence and associativity of operators are as follows:
        Precedence  Operator    Character  Description                            Associativity
        1           LPAR, RPAR  ( ... )    Function call                          Left to right
                    LBRA, RBRA  [ ... ]    Array construction
                    LCUR, RCUR  { ... }    Struct construction
        2           LBRA, RBRA  [ ... ]    Indexing                               Left to right
        3           EXP         ^ | **     Exponentiation                         Right to left
        4           ADD         +          Unary plus                             Right to left
                    SUB         -          Unary minus
        5           SEQ         :          Sequence construction                  Left to right
        6           MATMUL      %*%        Matrix multiplication                  Left to right
                    MOD         %%         Modular operation
                    QUOT        %/%        Quotient operation
        7           MUL         *          Multiplication                         Left to right
                    DIV         /          Division
        8           ADD         +          Addition                               Left to right
                    SUB         -          Subtraction
        9           LSS         <          Comparison (less than)                 Left to right
                    LEQ         <=         Comparison (less than or equal to)
                    GRT         >          Comparison (greater than)
                    GEQ         >=         Comparison (greater than or equal to)
                    EQ          ==         Comparison (equal to)
                    NEQ         !=         Comparison (not equal to)
        10          NEG         !          Boolean negation                       Right to left
        11          AND         & | &&     Logical and                            Left to right
        12          OR          | | ||     Logical or                             Left to right
        13          ASGN        =          Assignment                             Left to right
        14          COM         ,          Comma                                  Left to right
    Precedence with smaller number stands for higher precedence.
    
    Considering the precedence and associativity described above, grammar for LL parsing is as follows:
        expr      = or_expr (ASGN or_expr)*
        or_expr   = and_expr (OR and_expr)*
        and_expr  = neg_expr (AND neg_expr)*
        neg_expr  = NEG* comp_expr
        comp_expr = add_expr ((LSS | LEQ | GRT | GEQ | EQ | NEQ) add_expr)*
        add_expr  = mul_expr ((ADD | SUB) mul_expr)*
        mul_expr  = rem_expr ((MUL | DIV) rem_expr)*
        rem_expr  = seq_expr ((MATMUL | MOD | QUOT) seq_expr)*
        seq_expr  = pls_expr (SEQ pls_expr)*
        pls_expr  = (ADD | SUB)* exp_expr
        exp_expr  = (idx_expr EXP)* idx_expr
        idx_expr  = term (LBRA expr? (COM expr?)* RBRA)
        term      = LPAR expr RPAR
                  | arr_expr
                  | strt_expr
                  | fun_expr
                  | (Num | Bool | Str | Var)
        arr_expr  = LBRA (expr (COM expr)*)? RBRA
        strt_expr = LCUR (Var SEQ expr (COM Var SEQ expr)*)? RCUR
        fun_expr  = Fun LPAR (expr (COM expr)*)? RPAR
                  | Fun LPAR Var ASGN expr (COM Var ASGN expr)* RPAR
                  | Fun LPAR expr (COM expr)* COM Var ASGN expr (COM Var ASGN expr)* RPAR
                  
    This grammar (and some trick) naturally resolves ambiguity regarding
        1. SEQ: It can represent both sequence construction operator 
                and delimiter which separates member id of struct and its value.
        2. ASGN: It can represent both assignment 
                 and delimiter which separates id of keyword parameter and value to be passed.
        3. LPAR, RPAR: It can represent both parenthesis in arithmetic and function call.
        4. ADD, SUB: They can be both unary and binary.
    It replaces SEQ used as a delimiter with MEMID token, ASGN used as a delimiter with KWARG token.
    For ADD, SUB, LPAR and RPAR, it sets connections b/w them and other AST nodes differently according to their usage.
    Then there will be no ambiguity anymore.
    
    Most of this logic is for internal use only.
    """

    def __expr(self) -> AST:
        """
        expr = or_expr (ASGN or_expr)*
        """
        rt: AST = self.__or_expr()

        if self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.ASGN:
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            return AST(rt_tok, [rt, self.__expr()])

        return rt

    def __or_expr(self) -> AST:
        """
        or_expr = and_expr (OR and_expr)*
        """
        rt: AST = self.__and_expr()

        while self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.OR:
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__and_expr()])

        return rt

    def __and_expr(self) -> AST:
        """
        and_expr = neg_expr (AND neg_expr)*
        """
        rt: AST = self.__neg_expr()

        while self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.AND:
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__neg_expr()])

        return rt

    def __neg_expr(self) -> AST:
        """
        neg_expr = NEG* comp_expr
        """
        if self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.NEG:
            rt_tok: Tok = self.__curr_tok

            self.__eat()

            return AST(rt_tok, [self.__neg_expr()])

        return self.__comp_expr()

    def __comp_expr(self) -> AST:
        """
        comp_expr = add_expr ((LSS | LEQ | GRT | GEQ | EQ | NEQ) add_expr)*
        """
        rt: AST = self.__add_expr()

        while self.__curr_tok.t == TokT.OP and \
                self.__curr_tok.v in [OpT.LSS, OpT.LEQ, OpT.GRT, OpT.GEQ, OpT.EQ, OpT.NEQ]:
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__add_expr()])

        return rt

    def __add_expr(self) -> AST:
        """
        add_expr = mul_expr ((ADD | SUB) mul_expr)*
        """
        rt: AST = self.__mul_expr()

        while self.__curr_tok.t == TokT.OP and (self.__curr_tok.v == OpT.ADD or self.__curr_tok.v == OpT.SUB):
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__mul_expr()])

        return rt

    def __mul_expr(self) -> AST:
        """
        mul_expr = rem_expr ((MUL | DIV) rem_expr)*
        """
        rt: AST = self.__rem_expr()

        while self.__curr_tok.t == TokT.OP and (self.__curr_tok.v == OpT.MUL or self.__curr_tok.v == OpT.DIV):
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__rem_expr()])

        return rt

    def __rem_expr(self) -> AST:
        """
        rem_expr = seq_expr ((MATMUL | MOD | QUOT) seq_expr)*
        """
        rt: AST = self.__seq_expr()

        while self.__curr_tok.t == TokT.OP and self.__curr_tok.v in [OpT.MATMUL, OpT.MOD, OpT.QUOT]:
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__seq_expr()])

        return rt

    def __seq_expr(self) -> AST:
        """
        seq_expr = pls_expr (SEQ pls_expr)*
        """
        rt: AST = self.__pls_expr()

        while self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.SEQ:
            rt_tok: Tok = self.__curr_tok

            self.__eat()
            rt = AST(rt_tok, [rt, self.__pls_expr()])

        return rt

    def __pls_expr(self) -> AST:
        """
        pls_expr = (ADD | SUB)* exp_expr
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
        exp_expr = (idx_expr EXP)* idx_expr
        """
        rt: AST = self.__idx_expr()

        if self.__curr_tok.t == TokT.OP and self.__curr_tok.v == OpT.EXP:
            rt_tok: Tok = self.__curr_tok

            self.__eat()

            return AST(rt_tok, [rt, self.__exp_expr()])

        return rt

    def __idx_expr(self) -> AST:
        """
        idx_expr = term (LBRA expr? (COM expr?)* RBRA)

        :raise ParserErr[NCLOSED_PARN]: If a closing bracket(]) is missing.
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
        term = LPAR expr RPAR
             | arr_expr
             | strt_expr
             | fun_expr
             | (Num | Bool | Str | Var)

        :raise ParserErr[NCLOSED_PARN]: If a closing parenthesis()) is missing.
        :raise ParserErr[INCOMP_EXPR]: If EOF token is encountered.
        :raise ParserErr[INVALID_TOK]: If unexpected tokens are encountered.
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
        arr_expr = LBRA (expr (COM expr)*)? RBRA

        :raise ParserErr[NCLOSED_PARN]: If a closing bracket(]) is missing.
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
        strt_expr = LCUR (Var SEQ expr (COM Var SEQ expr)*)? RCUR

        :raise ParserErr[NCLOSED_PARN]: If a closing curly bracket(}) is missing.
        :raise ParserErr[MEMID_MISS]: If a member id is missing.
        :raise ParserErr[INCOMP_EXPR]: If a delimiter(:) is missing.
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
        fun_expr = Fun LPAR (expr (COM expr)*)? RPAR
                 | Fun LPAR Var ASGN expr (COM Var ASGN expr)* RPAR
                 | Fun LPAR expr (COM expr)* COM Var ASGN expr (COM Var ASGN expr)* RPAR

        It resolves the ambiguity regarding ASGN.
        However, with the help of grammar, it needs other information: id of keyword arguments.
        Suppose that built-in foo takes two arguments, one being non-keyword argument
        and the other being keyword argument with id y.
        Then foo(x = 2, y = 3) should be interpreted foo(2, 3) where the first ASGN is indeed an assignment
        but the second one is a delimiter.
        To resolve such ambiguity, it looks up ids of keywords of the called built-in by calling Fun.is_kw.

        :raise ParserErr[INCOMP_EXPR]: If a delimiter(=) is missing or unexpected tokens are encountered.
        :raise ParserErr[FUN_CALL_MISS]: If a opening parenthesis(() is missing.
        :raise ParserErr[NCLOSED_PARN]: If a closing parenthesis()) is missing.
        :raise ParserErr[ARG_MISPOS]: If non-keyword arguments follows keyword arguments.
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
                    raise ParserErr(self.__curr_tok.pos, self.__line, Errno.ARG_MISPOS)

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

        For detail, refer to the comments above.
        Note that after parsing, only EOF token should be left behind.

        :param line: Raw input string to be parsed.

        :return: Built AST.

        :raise ParserErr: If tokens other than EOF token are left behind.
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
