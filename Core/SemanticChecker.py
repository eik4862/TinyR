from __future__ import annotations

from .Operator import *
from .Parser import *
from Error.Exception import *


@final
class SemanticChk:
    """
    Semantic checker class.

    Traverses through AST and checks semantics.
    It is implemented as singleton.
    """
    # Singleton object.
    __inst: ClassVar[SemanticChk] = None

    @classmethod
    def inst(cls, *args, **kwargs) -> SemanticChk:
        if not cls.__inst:
            SemanticChk.__inst = cls(*args, **kwargs)

        return cls.__inst

    def __init__(self) -> None:
        self.__ast: Optional[AST] = None
        self.__line: str = ''

    """
    SEMANTIC CHECKING LOGIC
    """

    def __chk_mem(self, ast: AST) -> NoReturn:
        if ast.lval:
            raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

        self.__chk_hlpr(ast.ch[0])

        if ast.ch[0].t.t == T.NA:
            raise SemanticChkErr(ast.ch[0].tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[0].tok.v)

        ast.t = ast.ch[0].t

    def __chk_kwarg(self, ast: AST) -> NoReturn:
        if ast.lval:
            raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

        self.__chk_hlpr(ast.ch[0])

        if ast.ch[0].t.t == T.NA:
            raise SemanticChkErr(ast.ch[0].tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[0].tok.v)

        ast.t = ast.ch[0].t

    def __chk_op(self, ast: AST) -> NoReturn:
        if ast.lval:
            raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

        if ast.tok.v == OpT.EXP:
            self.__chk_hlpr(ast.ch[1])
            self.__chk_hlpr(ast.ch[0])
        else:
            for node in ast.ch:
                self.__chk_hlpr(node)

        ch_t: List[TSym] = [node.t for node in ast.ch]

        for i in range(len(ch_t)):
            if ch_t[i].t == T.NA:
                raise SemanticChkErr(ast.ch[i].tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[i].tok.v)

        if ast.tok.v <= OpT.DIV.value:
            t, hndl = Arith.t_chk(ast.tok.v, ch_t)
        elif ast.tok.v <= OpT.NEQ.value:
            t, hndl = Comp.t_chk(ast.tok.v, ch_t)
        else:
            t, hndl = Logi.t_chk(ast.tok.v, ch_t)

        if t is None or hndl is None:
            raise SemanticChkErr(ast.tok.pos, self.__line, Errno.SGNTR_NFOUND, infer=str(FunTSym(ch_t, TSym())))

        ast.t = t
        ast.call = hndl

    def __chk_idx(self, ast: AST) -> NoReturn:
        ast.ch[0].lval = ast.lval

        for node in ast.ch:
            self.__chk_hlpr(node)

        ch_t: List[TSym] = [node.t for node in ast.ch]

        for i in range(len(ch_t)):
            if ch_t[i].t == T.NA:
                raise SemanticChkErr(ast.ch[i].tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[i].tok.v)

        t, hndl = Sp.t_chk(ast.tok.v, ch_t, ast.lval)

        if t is None or hndl is None:
            raise SemanticChkErr(ast.tok.pos, self.__line, Errno.SGNTR_NFOUND, infer=str(FunTSym(ch_t, TSym())))

        ast.t = t
        ast.call = hndl

    def __chk_asgn(self, ast: AST) -> NoReturn:
        if ast.lval:
            raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

        ast.ch[0].lval = True

        try:
            self.__chk_hlpr(ast.ch[0])
            self.__chk_hlpr(ast.ch[1])
        except SemanticChkErr as e:
            if e.errno == Errno.INVALID_LVAL:
                e.pos = ast.tok.pos

            raise e

        tar_t, val_t = ast.ch[0].t, ast.ch[1].t

        if val_t.t == T.NA:
            raise SemanticChkErr(ast.tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[1].tok.v)
        elif tar_t.t == T.NA:
            SymTab.inst().update_t(ast.ch[0].tok.v, val_t)
            ast.ch[0].t = val_t
            ast.t = val_t
        else:
            if ast.ch[0].tok.t != TokT.OP:
                t = ast.ch[1].t
            else:
                t, _ = Sp.t_chk(ast.tok.v, [ast.ch[0].t, ast.ch[1].t])

                if t is None:
                    raise SemanticChkErr(ast.tok.pos, self.__line, Errno.ASGN_T_MISS, tar_t=str(ast.ch[0].t),
                                         val_t=str(ast.ch[1].t))

            SymTab.inst().update_t(ast.ch[0].tok.v, t)
            ast.t = t

    def __chk_arr(self, ast: AST) -> NoReturn:
        if ast.lval:
            raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

        for node in ast.ch:
            self.__chk_hlpr(node)

        ch_t: List[TSym] = [node.t for node in ast.ch]

        for i in range(len(ch_t)):
            if ch_t[i].t == T.NA:
                raise SemanticChkErr(ast.ch[i].tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[i].tok.v)

        if len(ch_t) == 0:
            t: TSym = ArrTSym(VoidTSym(), 1)
        else:
            elem_t: Optional[TSym] = VoidTSym()

            for t in ch_t:
                elem_t = TSym.sup(elem_t, t)

                if elem_t is None:
                    raise SemanticChkErr(ast.tok.pos, self.__line, Errno.INHOMO_ELEM,
                                         infer=', '.join(map(str, ch_t)))

            t: TSym = ArrTSym(elem_t, 1) if elem_t.base else ArrTSym(elem_t.elem, elem_t.dept + 1)

        ast.t = t

    def __chk_strt(self, ast: AST) -> NoReturn:
        if ast.lval:
            raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

        for node in ast.ch:
            self.__chk_hlpr(node)

        id_: List[str] = [node.tok.v for node in ast.ch]
        ch_t: List[TSym] = [node.t for node in ast.ch]

        if len(ch_t) == 0:
            t: TSym = StrtTSym({})
        else:
            elem_t: Dict[str, TSym] = {}

            for i in range(len(id_)):
                if id_[i] in elem_t:
                    raise SemanticChkErr(ast.ch[i].tok.pos, self.__line, Errno.ID_DUP, id_=id_[i])

                elem_t[id_[i]] = ch_t[i]

            t: TSym = StrtTSym(elem_t)

        ast.t = t

    def __chk_fun(self, ast: AST) -> NoReturn:
        if ast.lval:
            raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

        kwargs: List[Tuple[str, Any]] = ast.tok.v.kwargs
        ch: List[AST] = []

        i: int = 0

        while i < len(ast.ch) and ast.ch[i].tok.t != TokT.KWARG:
            ch.append(ast.ch[i])
            i += 1

        for k, v in kwargs[max(i - ast.tok.v.nargs, 0):]:
            j: int = 0

            while j < len(ast.ch) - i:
                if ast.ch[i + j].tok.v == k:
                    ch.append(ast.ch[i + j].ch[0])

                    break

                j += 1

            if j == len(ast.ch) - i:
                ch.append(Parser.inst().parse(v))

        ast.ch = ch

        for node in ast.ch:
            self.__chk_hlpr(node)

        ch_t: List[TSym] = [node.t for node in ast.ch]

        for i in range(len(ch_t)):
            if ch_t[i].t == T.NA:
                raise SemanticChkErr(ast.ch[i].tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[i].tok.v)

        if not (FunTSym(ch_t, ast.tok.v.t.ret) <= ast.tok.v.t):
            raise SemanticChkErr(ast.tok.pos, self.__line, Errno.SGNTR_NFOUND, infer=str(FunTSym(ch_t, TSym())))

        ast.t = ast.tok.v.t.ret
        ast.call = ast.tok.v.call

    def __chk_hlpr(self, ast: AST) -> NoReturn:
        """
        Checks the follows:
            1. Type mismatch
            2. Variable usage w.o. assignment
            3. Not proper l-value
        The first one is bottom-up process and the third one is top-down process.
        These three checks are interwoven, thus the logic is somehow 'dirty'.

        [Type rules]
        n => Num
        b => Bool
        s => Str
        v => Void
        Var[x] => a if T_TB[x] = a
        Var[x] => NA if a is not in T_TB.
        op(a1, ..., ap) => t_chk(op, [a1, ..., ap])
        [a1, ..., ap] => t_chk([a1, ..., ap])

        [Variable usage w.o. assignment]
        Var[x] not found => Nil
        Var[x] = b, Var[x] is not found => Nil, now Var[x] is assigned.
        op(..., Var[x], ...), Var[x] is not found => Error
        [..., Var[x], ...], Var[x] is not found => Error

        [L-value rules]
        Var[x] = b => Var[x] is l-value
        Var[x] is l-value => Nil
        Var[x][i1, ..., ip] is l-value => Var[x] is l-value
        a is l-value => Error

        :param ast: AST to be checked.

        :raise SemanticChkErr: Expression containing invalid l-values raises exception with errno INVALID_LVAL.
        :raise SemanticChkErr: Expression containing the usage of variable before its assignment raise exception
                               with errno NOT_DEFINE.
        :raise SemanticChkErr: Expression containing array constructions with inhomogeneous elements raise exception
                               with errno INHOMO_ELEM.
        :raise SemanticChkErr: Expression containing operations with incompatible types raise exception
                               with errno SGNTR_NFOUND.
        """
        # Handle NUM, BOOL, STR, VOID, and VAR tokens.
        # Except for VAR token, these cannot be l-value, thus raises exception.
        # However, the position of wrong assignment will be assigned latter.
        if ast.tok.t == TokT.NUM:
            if ast.lval:
                raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

            ast.t = NumTSym()
        elif ast.tok.t == TokT.BOOL:
            if ast.lval:
                raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

            ast.t = BoolTSym()
        elif ast.tok.t == TokT.STR:
            if ast.lval:
                raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

            ast.t = StrTSym()
        elif ast.tok.t == TokT.VOID:
            if ast.lval:
                raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

            ast.t = VoidTSym()
        elif ast.tok.t == TokT.VAR:
            var_t = SymTab.inst().lookup_t(ast.tok.v)
            ast.t = TSym() if var_t is None else var_t
        elif ast.tok.t == TokT.KWARG:
            self.__chk_kwarg(ast)
        elif ast.tok.t == TokT.MEM:
            self.__chk_mem(ast)
        elif ast.tok.t == TokT.OP:
            if ast.tok.v == OpT.IDX:
                self.__chk_idx(ast)
            elif ast.tok.v == OpT.ASGN:
                self.__chk_asgn(ast)
            else:
                self.__chk_op(ast)
        elif ast.tok.t == TokT.ARR:
            self.__chk_arr(ast)
        elif ast.tok.t == TokT.STRT:
            self.__chk_strt(ast)
        else:
            self.__chk_fun(ast)

    def chk(self, ast: AST, line: str) -> AST:
        """
        Checks semantics.
        For details, refer to the comments in __chk_hlpr.

        :param ast: AST to be checked.
        :param line: Raw input string.

        :return: Checked AST.

        :raise SemanticChkErr: Expression containing the usage of variable before its assignment raise exception
                               with errno NOT_DEFINE.
        """
        self.__ast = ast
        self.__line = line

        self.__chk_hlpr(ast)

        # One final check is needed to prevent expressions like 'x' where x is not assigned.
        if ast.t.t == T.NA:
            raise SemanticChkErr(ast.tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.tok.v)

        return ast

    """
    DEBUGGING
    """

    def test(self, ast: AST, line: str) -> NoReturn:
        start: float = timer()
        rt: AST = self.chk(ast, line)
        end: float = timer()

        print('------ TEST SUMMARY ------')
        print(f'  @module : PARSER')
        print(f'  @elapsed: {round((end - start) * 1e4, 4)}ms')
        print(f'  @sample : {line}')
        print('--------- RESULT ---------')
        print('* Postorder traversal')
        self.__test_hlpr(rt, 0)

    def __test_hlpr(self, ast: AST, cnt: int) -> int:
        for node in ast.ch:
            cnt = self.__test_hlpr(node, cnt)

        print(f'[{cnt}] {ast}')

        return cnt + 1
