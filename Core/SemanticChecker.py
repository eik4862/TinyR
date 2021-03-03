from __future__ import annotations

from .Operator import *
from .Parser import *
from Error.Exception import *


# TODO: kwargs unnecessary/duplicated, member id duplicated?
@final
class SemanticChk:
    """
    Semantic checker class.

    Traverses through AST and checks semantics.
    Semantic checking does the followings:
        1. Static type inference.                                           [ChkT]
        2. Detect a usage of a variable without assignment.                 [ChkVar]
        3. Determine whether LHS of an assignment is valid l-value of not.  [ChkLVal]
        4. Detect duplicated member ids in a struct.                        [ChkDup]
    Logic for each is interwoven so that semantic checking process can be done during a single traversal.

    This class is implemented as a singleton. The singleton object will be instantiated at its first call.
    This class is the end of inheritance. No further inheritance is allowed.
    """
    # Singleton object.
    __inst: ClassVar[SemanticChk] = None

    @classmethod
    def inst(cls, *args, **kwargs) -> SemanticChk:
        if not cls.__inst:
            SemanticChk.__inst = cls(*args, **kwargs)

        return cls.__inst

    def __init__(self) -> None:
        # AST to be checked.
        self.__ast: Optional[AST] = None
        # Raw input string.
        self.__line: str = ''

    """
    SEMANTIC CHECKING LOGIC
    
    [ChkT] logic is quite complicated, and thus most of them are deferred to Operator module.
    For detail, refer to the comments of Operator module.
    Here, only following inference rules are implemented:
        1. [TMem]
           If   env |- e => env', a
           Then env |- id: e => env', a
        2. [TKwarg]
           If   env |- e => env', a
           Then env |- kw = e => env', a
        3. [TAsgn]
           If   e1 = x
                env |- e => env', a
           Then env |- e1 = e2 => env' U {Var: a}, a
        4. [TAsgnIdx]
           If   e1 = e'1[e'2]
                env |- e1 => env', b
                env' |- e2 => env'', a
                a <: b
           Then env |- e1 = e2 => env'', a
        5. [TSnglArr]
           If   env(i - 1) |- ei => envi, ai for all i
                Sup(a1, ..., ap) = b is not array type
           Then env0 |- [e1, ..., ep] => envp, Arr[b, 1]
        6. [TDblArr]
           If   env(i - 1) |- ei => envi, ai for all i
                Sup(a1, ..., ap) = Arr[b, n]
           Then env0 |- [e1, ..., ep] => envp, Arr[b, n + 1]
        7. [TStrt]
           If   ei = idi: e'i for all i
                env(i - 1) |- ei => envi, ai for all i
           Then env0 |- {e1, ..., ep} => envp, {id1: a1, ..., idp: ap}
        8. [TFun]
           If   env(i - 1) |- ei => envi, ai for all i
                envp[f] = (bi, ..., bp) => c
                ai <: bi for all i
           Then env0 |- f(e1, ..., ep) => envp, c
        9. [TNum]
           env |- n => env, Num
        10. [TBool]
            env |- b => env, Bool
        11. [TStr]
            env |- s => env, Str
        12. [TVoid]
            env |- v => env, Void
        13. [TVarFound]
            If   env[x] = a
            Then env |- x => a
        14. [TVarNFound]
            If   x not in env
            Then env |- x => NA
        
    [ChkVar] can be done by checking whether inferred types of children are NA or not.
    Since it looks up types of variables from symTab class, there should be no NA types after checking,
    unless a certain variable is used before assignment which is semantically wrong.
    Though, there is one minor exception: assignment to new variable.
    
    [ChkLVal] is top-down process.
    Logic for this check can be summarized as follows:
        1. expr1 = expr2 cannot be l-value itself,
           but if the pattern is encountered, then expr1 should be l-value.
        2. Var can be l-value.
        3. expr1[expr2] can be l-value and in that case, expr should be l-value.
        4. All other patterns cannot be l-value.
    
    [ChkDup] is trivial and straightforward.
    
    Most of this logic is for internal use only.
    """

    def __chk_mem(self, ast: AST) -> NoReturn:
        """
        [ChkT] - [TMem]
            If   env |- e => env', a
            Then env |- id: e => env', a
        [ChkVar] Type of a child should not be NA.
        [ChkLVal] Cannot be a l-value.

        :raise SemanticErr[INVALID_LVAL]: If LHS of an assignment cannot be a l-value.
        :raise SemanticErr[NOT_DEFINE]: If variables are used without assignment.
        """
        # [ChkLVal]
        if ast.lval:
            raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

        self.__chk_hlpr(ast.ch[0])

        # [ChkVar]
        if ast.ch[0].t.t == T.NA:
            raise SemanticChkErr(ast.ch[0].tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[0].tok.v)

        # [ChkT] - [TMem]
        ast.t = ast.ch[0].t

    def __chk_kwarg(self, ast: AST) -> NoReturn:
        """
        [ChkT] - [TKwarg]
            If   env |- e => env', a
            Then env |- kw = e => env', a
        [ChkVar] Type of a child should not be NA.
        [ChkLVal] Cannot be a l-value.

        :raise SemanticErr[INVALID_LVAL]: If LHS of an assignment cannot be a l-value.
        :raise SemanticErr[NOT_DEFINE]: If variables are used without assignment.
        """
        # [ChkLVal]
        if ast.lval:
            raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

        self.__chk_hlpr(ast.ch[0])

        # [ChkVar]
        if ast.ch[0].t.t == T.NA:
            raise SemanticChkErr(ast.ch[0].tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[0].tok.v)

        # [ChkT] - [TKwarg]
        ast.t = ast.ch[0].t

    def __chk_op(self, ast: AST) -> NoReturn:
        """
        [ChkT] Deferred to Operator module.
        [ChkVar] Types of children should not be NA.
        [ChkLVal] Cannot be a l-value.

        For exponentiation, checking should be done from the rightmost child because of its right to left associativity.
        For other operators, check can be done from the leftmost child.
        Although unary plus and minus has right to left associativity,
        it has no need to take care of them since they has only one child.

        To outsource type inference, it calls t_chk function in Operator module.
        t_chk function returns both inferred type and function pointer(handle) which will be called for interpretation.
        It attaches these returns to ast.

        :raise SemanticErr[INVALID_LVAL]: If LHS of an assignment cannot be a l-value.
        :raise SemanticErr[NOT_DEFINE]: If variables are used without assignment.
        :raise SemanticErr[SGNTR_NFOUND]: If there is a type error.
        """
        # [ChkLVal]
        if ast.lval:
            raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

        if ast.tok.v == OpT.EXP:
            self.__chk_hlpr(ast.ch[1])
            self.__chk_hlpr(ast.ch[0])
        else:
            for node in ast.ch:
                self.__chk_hlpr(node)

        ch_t: List[TSym] = [node.t for node in ast.ch]

        # [ChkVar]
        for i in range(len(ch_t)):
            if ch_t[i].t == T.NA:
                raise SemanticChkErr(ast.ch[i].tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[i].tok.v)

        # [ChkT]
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
        """
        [ChkT] Deferred to Operator module.
        [ChkVar] Types of children should not be NA.
        [ChkLVal] It can be l-value and in that case,
                  its first child which is the target of indexing operation should be l-value.

        For function t_chk, refer to the comments of SemanticChk.__chk_op.

        :raise SemanticErr[NOT_DEFINE]: If variables are used without assignment.
        :raise SemanticErr[SGNTR_NFOUND]: If there is a type error.
        """
        # [ChkLVal]
        ast.ch[0].lval = ast.lval

        for node in ast.ch:
            self.__chk_hlpr(node)

        ch_t: List[TSym] = [node.t for node in ast.ch]

        # [ChkVar]
        for i in range(len(ch_t)):
            if ch_t[i].t == T.NA:
                raise SemanticChkErr(ast.ch[i].tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[i].tok.v)

        # [ChkT]
        t, hndl = Sp.t_chk(ast.tok.v, ch_t, ast.lval)

        if t is None or hndl is None:
            raise SemanticChkErr(ast.tok.pos, self.__line, Errno.SGNTR_NFOUND, infer=str(FunTSym(ch_t, TSym())))

        ast.t = t
        ast.call = hndl

    def __chk_asgn(self, ast: AST) -> NoReturn:
        """
        [ChkT] - [TAsgn]
            If   e1 = Var
                 env |- e2 => env', a
            Then env |- e1 = e2 => env' U {Var: a}, a
        [ChkT] - [TAsgnIdx]
            If   e1 = e'1[e'2]
                 env |- e1 => env', b
                 env' |- e2 => env'', a
                 a <: b
            Then env |- e1 = e2 => env'', a
        [ChkVar] Its left child can have NA type while its right child cannot.
                 Left child whit NA type implies that it is an initial assignment.
        [ChkLVal] Cannot be a l-value. But its left child should be l-value.

        For function t_chk, refer to the comments of SemanticChk.__chk_op.

        :raise SemanticErr[INVALID_LVAL]: If LHS of an assignment cannot be a l-value.
        :raise SemanticErr[NOT_DEFINE]: If variables are used without assignment.
        :raise SemanticErr[ASGN_T_MISS]: If there is a type error.
        """
        # [ChkLVal]
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

        # [ChkVar]
        if val_t.t == T.NA:
            raise SemanticChkErr(ast.tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[1].tok.v)

        # [ChkT]
        if tar_t.t == T.NA or ast.ch[0].tok.t == TokT.VAR:
            # [TAsgn]
            SymTab.inst().update_t(ast.ch[0].tok.v, val_t)
        else:
            # [TAsgnIdx]
            t, _ = Sp.t_chk(ast.tok.v, [ast.ch[0].t, ast.ch[1].t])

            if t is None:
                raise SemanticChkErr(ast.tok.pos, self.__line, Errno.ASGN_T_MISS, tar_t=str(ast.ch[0].t),
                                     val_t=str(ast.ch[1].t))

        ast.t = val_t

    def __chk_arr(self, ast: AST) -> NoReturn:
        """
        [ChkT] - [TSnglArr]
            If   env(i - 1) |- ei => envi, ai for all i
                 Sup(a1, ..., ap) = b is not array type
            Then env0 |- [e1, ..., ep] => envp, Arr[b, 1]
        [ChkT] - [TDblArr]
            If   env(i - 1) |- ei => envi, ai for all i
                 Sup(a1, ..., ap) = Arr[b, n]
            Then env0 |- [e1, ..., ep] => envp, Arr[b, n + 1]
        [ChkVar] Types of children should not be NA.
        [ChkLVal] Cannot be a l-value.

        :raise SemanticErr[INVALID_LVAL]: If LHS of an assignment cannot be a l-value.
        :raise SemanticErr[NOT_DEFINE]: If variables are used without assignment.
        :raise SemanticErr[INHOMO_ELEM]: If types of the elements of an array are not identical.
        """
        # [ChkLVal]
        if ast.lval:
            raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

        for node in ast.ch:
            self.__chk_hlpr(node)

        ch_t: List[TSym] = [node.t for node in ast.ch]

        # [ChkVar]
        for i in range(len(ch_t)):
            if ch_t[i].t == T.NA:
                raise SemanticChkErr(ast.ch[i].tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[i].tok.v)

        # [ChkT] - [TSnglArr] & [TDblArr]
        elem_t: Optional[TSym] = TSym.sup(*ch_t)

        if elem_t is None:
            raise SemanticChkErr(ast.tok.pos, self.__line, Errno.INHOMO_ELEM, infer=', '.join(map(str, ch_t)))

        ast.t = ArrTSym(elem_t, 1) if elem_t.base else ArrTSym(elem_t.elem, elem_t.dept + 1)

    def __chk_strt(self, ast: AST) -> NoReturn:
        """
        [ChkT] - [TStrt]
            If   ei = idi: e'i for all i
                 env(i - 1) |- ei => envi, ai for all i
            Then env0 |- {e1, ..., ep} => envp, {id1: a1, ..., idp: ap}
        [ChkVar] Types of children should not be NA.
        [ChkLVal] Cannot be a l-value.
        [ChkDup] Duplicated member ids are not allowed.

        :raise SemanticErr[INVALID_LVAL]: If LHS of an assignment cannot be a l-value.
        :raise SemanticErr[NOT_DEFINE]: If variables are used without assignment.
        :raise SemanticErr[ID_DUP]: If some member ids are duplicated.
        """
        # [ChkLVal]
        if ast.lval:
            raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

        for node in ast.ch:
            self.__chk_hlpr(node)

        id_: List[str] = [node.tok.v for node in ast.ch]
        ch_t: List[TSym] = [node.t for node in ast.ch]

        # [ChkVar]
        for i in range(len(ch_t)):
            if ch_t[i].t == T.NA:
                raise SemanticChkErr(ast.ch[i].tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[i].tok.v)

        elem_t: Dict[str, TSym] = {}

        # [ChkT] - [TStrt], [ChkDup]
        for i in range(len(id_)):
            if id_[i] in elem_t:
                raise SemanticChkErr(ast.ch[i].tok.pos, self.__line, Errno.ID_DUP, id_=id_[i])

            elem_t[id_[i]] = ch_t[i]

        t: TSym = StrtTSym(elem_t)
        ast.t = t

    def __chk_fun(self, ast: AST) -> NoReturn:
        """
        [ChkT] - [TFun]
            If   env(i - 1) |- ei => envi, ai for all i
                 envp[f] = (bi, ..., bp) => c
                 ai <: bi for all i
            Then env0 |- f(e1, ..., ep) => envp, c
        [ChkVar] Types of children should not be NA.
        [ChkLVal] Cannot be a l-value.

        

        :raise SemanticErr[INVALID_LVAL]: If LHS of an assignment cannot be a l-value.
        :raise SemanticErr[NOT_DEFINE]: If variables are used without assignment.
        :raise SemanticErr[SGNTR_NFOUND]: If there is a type error.
        """
        # [ChkLVal]
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

        # [ChkVar]
        for i in range(len(ch_t)):
            if ch_t[i].t == T.NA:
                raise SemanticChkErr(ast.ch[i].tok.pos, self.__line, Errno.NOT_DEFINE, var=ast.ch[i].tok.v)

        # [ChkT] - [TFun]
        if not (FunTSym(ch_t, ast.tok.v.t.ret) <= ast.tok.v.t):
            raise SemanticChkErr(ast.tok.pos, self.__line, Errno.SGNTR_NFOUND, infer=str(FunTSym(ch_t, TSym())))

        ast.t = ast.tok.v.t.ret
        ast.call = ast.tok.v.call

    def __chk_hlpr(self, ast: AST) -> NoReturn:
        """
        Routes semantic checking logic according to the type of currently visiting node ast.

        Checking logic for terminal nodes are implemented here since they are quite simple.

        [ChkT] - [TNum]
            env |- n => env, Num
        [ChkT] - [TBool]
            env |- b => env, Bool
        [ChkT] - [TStr]
            env |- s => env, Str
        [ChkT] - [TVoid]
            env |- v => env, Void
        [ChkT] - [TVarFound]
            If   env[x] = a
            Then env |- x => a
        [ChkT] - [TVarNFound]
            If   x not in env
            Then env |- x => NA
        [ChkVar] Terminal nodes have no children.
        [ChkLVal] Only Var can be l-value. Other terminal nodes cannot be l-values.

        :param ast: AST to be checked.

        :raise SemanticErr[INVALID_LVAL]: If LHS of an assignment cannot be a l-value.
        """
        if ast.tok.t == TokT.NUM:
            # [ChkLVal]
            if ast.lval:
                raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

            # [ChkT] - [TNum]
            ast.t = NumTSym()
        elif ast.tok.t == TokT.BOOL:
            # [ChkLVal]
            if ast.lval:
                raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

            # [ChkT] - [TBool]
            ast.t = BoolTSym()
        elif ast.tok.t == TokT.STR:
            # [ChkLVal]
            if ast.lval:
                raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

            # [ChkT] - [TStr]
            ast.t = StrTSym()
        elif ast.tok.t == TokT.VOID:
            # [ChkLVal]
            if ast.lval:
                raise SemanticChkErr(-1, self.__line, Errno.INVALID_LVAL)

            # [ChkT] - [TVoid]
            ast.t = VoidTSym()
        elif ast.tok.t == TokT.VAR:
            # [ChkT] - [TVarFound] & [TVarNFound]
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

        Traverses AST in postorder and recursively applies checking logic described above.
        If the check runs without any exception, it is ensured that there will be no semantic errors.
        During the check, type field of each node will be filled with the inferred type.
        (For nodes corresponding to operator or function token, call field will also be filled.)
        For detailed logic, refer to the comments above.

        :param ast: AST to be checked.
        :param line: Raw input string.

        :return: Checked AST.

        :raise SemanticErr[NOT_DEFINE]: If variables are used without assignment.
        """
        self.__ast = ast
        self.__line = line

        self.__chk_hlpr(ast)

        # Final [ChkVar] for the root node is needed to prevent the marginal case like 'x' where x is not assigned.
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
