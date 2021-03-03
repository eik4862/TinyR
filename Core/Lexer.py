from __future__ import annotations

from timeit import default_timer as timer
from .Token import *
from .SymbolTable import *
from Error.Exception import *


@final
class Lexer:
    """
    Lexer class.

    Derives tokens from the input string.
    Instead of deriving all tokens and storing them in a stack, it derives token one by one when requested.
    Parser will request tokens by calling Lexer.next_tok function. For detail, refer to the comments of Lexer.next_tok.

    This class is implemented as a singleton. The singleton object will be instantiated at its first call.
    This class is the end of inheritance. No further inheritance is allowed.
    """
    # Singleton object.
    __inst: ClassVar[Lexer] = None
    # Operator characters.
    __OP: Final[ClassVar[Set[str]]] = {'^', '*', '+', '-', ':', '%', '*', '/', '<', '=', '>', '!', '&', '|', '(', ')',
                                       '[', ']', '{', '}', ','}

    @classmethod
    def inst(cls, *args, **kwargs) -> Lexer:
        if not cls.__inst:
            Lexer.__inst = cls(*args, **kwargs)

        return cls.__inst

    def __init__(self) -> None:
        # Raw input string.
        self.__line: str = ''
        # Following two fields are automatically managed internally. Refer to the comments of Lexer.__step.
        # Current position from which tokenizing starts.
        self.__pos: int = 0
        # Character in the raw input string pointed by self.__pos.
        self.__curr_char: Optional[str] = None

    def init(self, line: str) -> NoReturn:
        self.__line: str = line
        self.__pos: int = 0
        self.__curr_char: Optional[str] = line[0]

    """
    HELPER FOR TOKEN DERIVING LOGIC
    
    This logic is for internal use only.
    """

    def __step(self, amt: int = 1) -> NoReturn:
        """
        Steps forward in the raw input string by amt.

        It updates internal variables holding current position and the character at the position.
        If current position exceeds the boundary of the input string,
        variable holding a current character will be set to None.

        :param amt: Amount of update. (Default: 1)
        """
        self.__pos += amt

        if self.__pos >= len(self.__line):
            self.__curr_char = None
        else:
            self.__curr_char = self.__line[self.__pos]

    def __peek(self, amt: int = 1) -> Optional[str]:
        """
        Looks ahead amt characters.

        If there are no amt characters in the raw input string succeeding current character, it returns None.

        :param amt: Amount of characters to look ahead. (Default: 1)

        :return: Looked up characters. None if look ahead is not possible.
        """
        peek_pos: int = self.__pos + amt

        if peek_pos >= len(self.__line):
            return None
        else:
            return self.__line[self.__pos + 1:peek_pos + 1]

    """
    TOKEN DERIVING LOGIC
    
    Grammar for token derivation is as follows:
        White = [ \t\r\n\v\f]
        Num = [0-9]+(.[0-9]*)?
            | .[0-9]+
        Str = ('|")[A-Za-z0-9]*('|")
        Id = [A-Za-z]+[A-Za-z0-9_]*
        Op = ^ | **? | + | - | : | %(* | /)?% | * | / | <=? | ==? | >=? | ! | &&? | ||? | ( | ) | [ | ] | { | } | ,
    
    Most of this logic is for internal use only.
    """

    def __skip_white(self) -> NoReturn:
        while self.__curr_char and self.__curr_char.isspace():
            self.__step()

    def __tok_num(self) -> Tok:
        """
        Derives numeric tokens.

        :return: Derived numeric token.

        :raise ParserErr[INVALID_TOK]: If a dot(.) is solely given.
        """
        pivot: int = self.__pos

        while self.__curr_char and self.__curr_char.isdigit():
            self.__step()

        if self.__curr_char == '.':
            self.__step()

            if not (self.__curr_char and self.__curr_char.isdigit()) and self.__pos - 1 == pivot:
                raise ParserErr(self.__pos - 1, self.__line, Errno.INVALID_TOK)

            while self.__curr_char and self.__curr_char.isdigit():
                self.__step()

            return Tok(TokT.NUM, float(self.__line[pivot:self.__pos]), pivot)
        else:
            return Tok(TokT.NUM, int(self.__line[pivot:self.__pos]), pivot)

    def __tok_str(self) -> Tok:
        """
        Derives string tokens.

        :return: Derived string token.

        :raise ParserErr[NCLOSED_PARN]: If quote is not closed.
        """
        pivot: int = self.__pos
        quote: str = self.__curr_char

        self.__step()

        while self.__curr_char and self.__curr_char != quote:
            self.__step()

        if not self.__curr_char:
            raise ParserErr(pivot, self.__line, Errno.NCLOSED_PARN)

        self.__step()

        return Tok(TokT.STR, self.__line[pivot + 1:self.__pos - 1], pivot)

    def __tok_id(self) -> Tok:
        """
        Derives boolean, function, and variable tokens.

        It looks up keyword table to determine
        whether the id represents keyword (or built-in function call) or variable.

        :return: Derived boolean, function, or variable token.
        """
        pivot: int = self.__pos

        self.__step()

        while self.__curr_char and (self.__curr_char.isalnum() or self.__curr_char == '_'):
            self.__step()

        tv_pair = SymTab.inst().lookup_kw(self.__line[pivot:self.__pos])

        if not tv_pair:
            return Tok(TokT.VAR, self.__line[pivot:self.__pos], pivot)

        return Tok(*tv_pair, pos=pivot)

    def __tok_op(self) -> Tok:
        """
        Derives operator, array, and struct tokens.

        Some operators are ambiguous.
        Most of ambiguity stems from the fact that
        some operator characters contain other operator characters as their substring.
        For example, * can be multiplication or exponentiation with succeeding *.
        Looking ahead some characters resolves most of these ambiguity issues.
        What left is ambiguity regarding indexing operator and array construction operator.
        These two share the same operator character, left bracket([). Thus, it is context-sensitive grammar.
        To resolve this, it resorts on the fact that indexing can appear only after right parenthesis()),
        right bracket(]), id of a variable([A-Za-z0-9_]), and numeric([0-9] | .).

        :return: Derived operator, array, or struct token.

        :raise ParserErr[INVALID_TOK]: If % is solely used.
        """
        if self.__curr_char == '^':
            self.__step()

            return Tok(TokT.OP, OpT.EXP, self.__pos - 1)
        elif self.__curr_char == '*':
            if self.__peek() == '*':
                self.__step(2)

                return Tok(TokT.OP, OpT.EXP, self.__pos - 2)
            else:
                self.__step()

                return Tok(TokT.OP, OpT.MUL, self.__pos - 1)
        elif self.__curr_char == '+':
            self.__step()

            return Tok(TokT.OP, OpT.ADD, self.__pos - 1)
        elif self.__curr_char == '-':
            self.__step()

            return Tok(TokT.OP, OpT.SUB, self.__pos - 1)
        elif self.__curr_char == ':':
            self.__step()

            return Tok(TokT.OP, OpT.SEQ, self.__pos - 1)
        elif self.__curr_char == '%':
            if self.__peek(2) == '*%':
                self.__step(3)

                return Tok(TokT.OP, OpT.MATMUL, self.__pos - 3)
            elif self.__peek(2) == '/%':
                self.__step(3)

                return Tok(TokT.OP, OpT.QUOT, self.__pos - 3)
            elif self.__peek() == '%':
                self.__step(2)

                return Tok(TokT.OP, OpT.MOD, self.__pos - 2)
            else:
                raise ParserErr(self.__pos, self.__line, Errno.INVALID_TOK)
        elif self.__curr_char == '/':
            self.__step()

            return Tok(TokT.OP, OpT.DIV, self.__pos - 1)
        elif self.__curr_char == '<':
            if self.__peek() == '=':
                self.__step(2)

                return Tok(TokT.OP, OpT.LEQ, self.__pos - 2)
            else:
                self.__step()

                return Tok(TokT.OP, OpT.LSS, self.__pos - 1)
        elif self.__curr_char == '>':
            if self.__peek() == '=':
                self.__step(2)

                return Tok(TokT.OP, OpT.GEQ, self.__pos - 2)
            else:
                self.__step()

                return Tok(TokT.OP, OpT.GRT, self.__pos - 1)
        elif self.__curr_char == '=':
            if self.__peek() == '=':
                self.__step(2)

                return Tok(TokT.OP, OpT.EQ, self.__pos - 2)
            else:
                self.__step()

                return Tok(TokT.OP, OpT.ASGN, self.__pos - 1)
        elif self.__curr_char == '!':
            if self.__peek() == '=':
                self.__step(2)

                return Tok(TokT.OP, OpT.NEQ, self.__pos - 2)
            else:
                self.__step()

                return Tok(TokT.OP, OpT.NEG, self.__pos - 1)
        elif self.__curr_char == '&':
            if self.__peek() == '&':
                self.__step(2)

                return Tok(TokT.OP, OpT.AND, self.__pos - 2)
            else:
                self.__step()

                return Tok(TokT.OP, OpT.AND, self.__pos - 1)
        elif self.__curr_char == '|':
            if self.__peek() == '|':
                self.__step(2)

                return Tok(TokT.OP, OpT.OR, self.__pos - 2)
            else:
                self.__step()

                return Tok(TokT.OP, OpT.OR, self.__pos - 1)
        elif self.__curr_char == '(':
            self.__step()

            return Tok(TokT.OP, OpT.LPAR, self.__pos - 1)
        elif self.__curr_char == ')':
            self.__step()

            return Tok(TokT.OP, OpT.RPAR, self.__pos - 1)
        elif self.__curr_char == '[':
            if self.__pos != 0 and \
                    (self.__line[self.__pos - 1] in [')', ']', '_', '.'] or self.__line[self.__pos - 1].isalnum()):
                self.__step()

                return Tok(TokT.OP, OpT.IDX, self.__pos - 1)
            else:
                self.__step()

                return Tok(TokT.OP, OpT.LBRA, self.__pos - 1)
        elif self.__curr_char == ']':
            self.__step()

            return Tok(TokT.OP, OpT.RBRA, self.__pos - 1)
        elif self.__curr_char == '{':
            self.__step()

            return Tok(TokT.OP, OpT.LCUR, self.__pos - 1)
        elif self.__curr_char == '}':
            self.__step()

            return Tok(TokT.OP, OpT.RCUR, self.__pos - 1)
        else:
            self.__step()

            return Tok(TokT.OP, OpT.COM, self.__pos - 1)

    def next_tok(self) -> Tok:
        """
        Derives a token starting from the position pointed by self.__curr_char.

        Starting position will be automatically updated internally.

        :return: Derived token. EOF token if it hits the end of the input string.

        :raise ParserErr[INVALID_TOK]: If unexpected characters are encountered.
        """
        while self.__curr_char:
            if self.__curr_char.isspace():
                self.__skip_white()

                continue
            elif self.__curr_char.isdigit() or self.__curr_char == '.':
                return self.__tok_num()
            elif self.__curr_char in Lexer.__OP:
                return self.__tok_op()
            elif self.__curr_char == '\'' or self.__curr_char == '"':
                return self.__tok_str()
            elif self.__curr_char.isapha():
                return self.__tok_id()
            else:
                raise ParserErr(self.__pos, self.__line, Errno.INVALID_TOK)

        return Tok(TokT.EOF, pos=self.__pos - 1)

    """
    DEBUGGING
    """

    def test(self, line: str) -> NoReturn:
        self.init(line)

        res: List[Tok] = []
        start: float = timer()

        while True:
            res.append(self.next_tok())

            if res[-1].t == TokT.EOF:
                break

        end: float = timer()

        print('------ TEST SUMMARY ------')
        print(f'  @module : LEXER')
        print(f'  @elapsed: {round((end - start) * 1e4, 4)}ms')
        print(f'  @sample : {line}')
        print('--------- RESULT ---------')

        for i in range(len(res)):
            print(f'[{i}] {res[i]}')
