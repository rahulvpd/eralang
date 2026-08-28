"""
EraLang Lexical Scanner
"""
from typing import List
from .token import Token, TokenType, KEYWORDS, SourceLocation


class LexerError(Exception):
    def __init__(self, message: str, location: SourceLocation):
        super().__init__(f"Lexer Error at {location}: {message}")
        self.message = message
        self.location = location


class Lexer:
    def __init__(self, source: str, filename: str = "<stdin>"):
        self.source = source.lstrip("\ufeff")
        self.filename = filename
        self.tokens: List[Token] = []
        
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.token_start_col = 1

    def tokenize(self) -> List[Token]:
        while not self._is_at_end():
            self.start = self.current
            self.token_start_col = self.column
            self._scan_token()

        self.tokens.append(
            Token(
                type=TokenType.EOF,
                lexeme="",
                value=None,
                location=SourceLocation(self.line, self.column, self.filename)
            )
        )
        return self.tokens

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _advance(self) -> str:
        if self._is_at_end():
            return "\0"
        char = self.source[self.current]
        self.current += 1
        self.column += 1
        return char

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def _match(self, expected: str) -> bool:
        if self._is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def _add_token(self, type: TokenType, value: any = None):
        lexeme = self.source[self.start:self.current]
        loc = SourceLocation(self.line, self.token_start_col, self.filename)
        self.tokens.append(Token(type, lexeme, value, loc))

    def _scan_token(self):
        c = self._advance()

        # Whitespace
        if c in (' ', '\r', '\t'):
            return

        if c == '\n':
            self.line += 1
            self.column = 1
            return

        # Single-line or multi-line comments
        if c == '/':
            if self._match('/'):
                while self._peek() != '\n' and not self._is_at_end():
                    self._advance()
                return
            elif self._match('*'):
                self._block_comment()
                return
            elif self._match('='):
                self._add_token(TokenType.SLASH_ASSIGN)
                return
            else:
                self._add_token(TokenType.SLASH)
                return

        # Single-character and compound delimiters / operators
        if c == '(': self._add_token(TokenType.LPAREN); return
        if c == ')': self._add_token(TokenType.RPAREN); return
        if c == '{': self._add_token(TokenType.LBRACE); return
        if c == '}': self._add_token(TokenType.RBRACE); return
        if c == '[': self._add_token(TokenType.LBRACKET); return
        if c == ']': self._add_token(TokenType.RBRACKET); return
        if c == ',': self._add_token(TokenType.COMMA); return
        if c == ':': self._add_token(TokenType.COLON); return
        if c == ';': self._add_token(TokenType.SEMICOLON); return
        if c == '?': self._add_token(TokenType.QUESTION); return
        if c == '%': self._add_token(TokenType.PERCENT); return
        if c == '@': self._add_token(TokenType.MATMUL); return

        if c == '+':
            self._add_token(TokenType.PLUS_ASSIGN if self._match('=') else TokenType.PLUS)
            return

        if c == '-':
            if self._match('>'):
                self._add_token(TokenType.ARROW)
            elif self._match('='):
                self._add_token(TokenType.MINUS_ASSIGN)
            else:
                self._add_token(TokenType.MINUS)
            return

        if c == '*':
            self._add_token(TokenType.STAR_ASSIGN if self._match('=') else TokenType.STAR)
            return

        if c == '!':
            self._add_token(TokenType.NEQ if self._match('=') else TokenType.NOT)
            return

        if c == '=':
            if self._match('='):
                self._add_token(TokenType.EQ)
            elif self._match('>'):
                self._add_token(TokenType.FAT_ARROW)
            else:
                self._add_token(TokenType.ASSIGN)
            return

        if c == '<':
            self._add_token(TokenType.LTE if self._match('=') else TokenType.LT)
            return

        if c == '>':
            self._add_token(TokenType.GTE if self._match('=') else TokenType.GT)
            return

        if c == '&':
            if self._match('&'):
                self._add_token(TokenType.AND)
            else:
                raise LexerError("Expected '&&' for logical AND", SourceLocation(self.line, self.token_start_col, self.filename))
            return

        if c == '|':
            if self._match('|'):
                self._add_token(TokenType.OR)
            else:
                raise LexerError("Expected '||' for logical OR", SourceLocation(self.line, self.token_start_col, self.filename))
            return

        if c == '.':
            if self._match('.'):
                if self._match('<'):
                    self._add_token(TokenType.DOT_DOT_LT)
                else:
                    self._add_token(TokenType.DOT_DOT)
            else:
                self._add_token(TokenType.DOT)
            return

        # Strings
        if c == '"':
            self._string()
            return

        # Numbers
        if c.isdigit():
            self._number()
            return

        # Identifiers and keywords
        if c.isalpha() or c == '_':
            self._identifier()
            return

        raise LexerError(f"Unexpected character: '{c}'", SourceLocation(self.line, self.token_start_col, self.filename))

    def _block_comment(self):
        depth = 1
        while depth > 0 and not self._is_at_end():
            if self._peek() == '\n':
                self.line += 1
                self.column = 0
            if self._peek() == '/' and self._peek_next() == '*':
                self._advance()
                self._advance()
                depth += 1
            elif self._peek() == '*' and self._peek_next() == '/':
                self._advance()
                self._advance()
                depth -= 1
            else:
                self._advance()

        if depth > 0:
            raise LexerError("Unterminated block comment", SourceLocation(self.line, self.token_start_col, self.filename))

    def _string(self):
        chars = []
        while self._peek() != '"' and not self._is_at_end():
            if self._peek() == '\n':
                self.line += 1
                self.column = 0

            c = self._advance()
            if c == '\\':
                escaped = self._advance()
                if escaped == 'n': chars.append('\n')
                elif escaped == 't': chars.append('\t')
                elif escaped == 'r': chars.append('\r')
                elif escaped == '"': chars.append('"')
                elif escaped == '\\': chars.append('\\')
                else: chars.append(escaped)
            else:
                chars.append(c)

        if self._is_at_end():
            raise LexerError("Unterminated string literal", SourceLocation(self.line, self.token_start_col, self.filename))

        # Consume closing quote
        self._advance()
        value = "".join(chars)
        self._add_token(TokenType.STRING, value)

    def _number(self):
        is_float = False
        while self._peek().isdigit():
            self._advance()

        # Check for fractional part
        if self._peek() == '.' and self._peek_next().isdigit():
            is_float = True
            self._advance() # consume '.'
            while self._peek().isdigit():
                self._advance()

        # Check for scientific notation (only if followed by digits)
        if self._peek() in ('e', 'E'):
            saved_pos = self.current
            saved_col = self.column
            self._advance()
            if self._peek() in ('+', '-'):
                self._advance()
            if self._peek().isdigit():
                is_float = True
                while self._peek().isdigit():
                    self._advance()
            else:
                # Backtrack if not a valid exponent
                self.current = saved_pos
                self.column = saved_col

        lexeme = self.source[self.start:self.current]
        try:
            value = float(lexeme) if is_float else int(lexeme)
        except ValueError:
            raise LexerError(f"Invalid numeric literal '{lexeme}'", SourceLocation(self.line, self.token_start_col, self.filename))
        self._add_token(TokenType.FLOAT if is_float else TokenType.INT, value)

    def _identifier(self):
        while self._peek().isalnum() or self._peek() == '_':
            self._advance()

        text = self.source[self.start:self.current]
        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        
        if token_type == TokenType.BOOLEAN:
            value = (text == "true")
            self._add_token(TokenType.BOOLEAN, value)
        else:
            self._add_token(token_type, text)
