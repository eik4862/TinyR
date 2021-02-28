from __future__ import annotations

from typing import NoReturn, ClassVar, final, Optional, List, Final, Set
from Core.Token import Tok
from Core.Type import TokT, OpT, Errno
from timeit import default_timer as timer
from Error.Exception import ParserErr
from Core.SymbolTable import SymTab


@final
class Lexer:
    """
    Lexer class.

    Reads raw input string and derives tokens.
    It is implemented as singleton.
    """
    # Singleton object.
    __inst: ClassVar[Lexer] = None
    # Operator characters.
    __OP: Final[ClassVar[Set[str]]] = {'^', '*', '+', '-', ':', '%', '*', '/', '<', '=', '>', '!', '&', '|', '(', ')',
                                       '[', ']', ','}

    @classmethod
    def inst(cls, *args, **kwargs) -> Lexer:
        if not cls.__inst:
            Lexer.__inst = cls(*args, **kwargs)

        return cls.__inst

    def __init__(self) -> None:
        self.__line: str = ''
        self.__pos: int = 0
        self.__curr_char: Optional[str] = None

    def init(self, line: str) -> NoReturn:
        """
        Initialize lexer.

        :param line: Raw input string to be tokenized.
        """
        self.__line: str = line
        self.__pos: int = 0
        self.__curr_char: Optional[str] = line[0]

    """
    TOKEN DERIVING LOGIC
    """

    def __step(self, amt: int = 1) -> NoReturn:
        """
        Helper for tokenizing.
        Steps forward in the raw input string and set self.__curr_char as the newly visited character.

        :param amt: The amount of step. (Default: 1)
        """
        self.__pos += amt

        if self.__pos >= len(self.__line):
            self.__curr_char = None
        else:
            self.__curr_char = self.__line[self.__pos]

    def __peek(self, amt: int = 1) -> Optional[str]:
        """
        Helper for tokenizing.
        Looks up one or more characters in the raw input string and return the looked up characters as one string.

        :param amt: The amount of characters to be looked up. (Default: 1)

        :return: Looked up characters. If it hits the end of the raw input string, it returns None.
        """
        peek_pos: int = self.__pos + amt

        if peek_pos >= len(self.__line):
            return None
        else:
            return self.__line[self.__pos + 1:peek_pos + 1]

    def __skip_white(self) -> NoReturn:
        """
        Skips consecutive white spaces(\n, ' ') in the raw input string.
        """
        while self.__curr_char and self.__curr_char.isspace():
            self.__step()

    def __tok_num(self) -> Tok:
        """
        Derives numeric token.
        It does not differentiate float and integer. Both will be tokenized as numeric token.

        :return: Derived numeric token.

        :raise ParserErr: Single dot(.) raises exception with errno INVALID_TOK.
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
        Derives string token.
        String token should be enclosed by double quote(") or single quote(').
        Currently, escaping is not supported.

        :return: Derived string token.

        :raise ParserErr: Input without closing quote raises exception with errno NCLOSED_PARN.
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
        Derives boolean and variable token.
        It refers Lexer.__KWORD dictionary to determine whether user input is built-in keyword or variable.
        Note that variable or keyword should start with alphabet. However, digits or underscore(_) can be followed.
        Built-in keywords include boolean symbols, like TRUE and F.

        :return: Derived boolean or variable token.
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
        Derives operator token.
        For some operators, their value can be determined immediately. (eg. +)
        For others, lexer should 'peek' some more characters to fully determine their values. (eg. %*%)

        :return: Derived operator token.

        :raise ParserErr: Operators enclosed by % which are not given properly raises exception with errno INVALID_TOK.
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
            # Left bracket([) needs a special treat.
            # It can be either array construction operator or indexing operator.
            # These two can be differentiated by considering one character preceding the left bracket.
            # If it is preceded by alphabet, digit, left parenthesis()), left bracket(]), or underscore(_),
            # then it must be array construction operator, and vice versa.
            if self.__pos != 0 and \
                    (self.__line[self.__pos - 1] in [')', ']', '_'] or self.__line[self.__pos - 1].isalnum()):
                self.__step()

                return Tok(TokT.OP, OpT.IDX, self.__pos - 1)
            else:
                self.__step()

                return Tok(TokT.OP, OpT.LBRA, self.__pos - 1)
        elif self.__curr_char == ']':
            self.__step()

            return Tok(TokT.OP, OpT.RBRA, self.__pos - 1)
        else:
            self.__step()

            return Tok(TokT.OP, OpT.COM, self.__pos - 1)

    def next_tok(self) -> Tok:
        """
        Derives next token based on the current position.
        Current position will be automatically updated internally.

        :return: Newly derived token. If it hits the end of the raw input string, it returns EOF token.

        :raise ParserErr: Any invalid input raises exception with errno INVALID_TOK.
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
            elif self.__curr_char.isalnum():
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
