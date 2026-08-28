"""
EraLang Recursive Descent Parser
"""
from typing import List, Optional, Tuple, Any
from .token import Token, TokenType, SourceLocation
from .ast_nodes import (
    Program, Stmt, Expr, Pattern,
    LetStmt, VarStmt, AssignStmt, FnDecl, Param, ReturnStmt,
    ForStmt, WhileStmt, BreakStmt, ContinueStmt, ImportStmt,
    ActorDecl, SpawnStmt, ExprStmt,
    LiteralExpr, IdentifierExpr, BinaryExpr, UnaryExpr,
    CallExpr, MemberExpr, IndexExpr, ArrayLitExpr, MapLitExpr,
    OptionLitExpr, ResultLitExpr, RangeExpr, MatchExpr, MatchArm,
    IfExpr, BlockExpr, TensorLitExpr, AICompleteExpr, QuestionExpr,
    LiteralPattern, IdentifierPattern, SomePattern, NonePattern,
    OkPattern, ErrPattern, WildcardPattern, EnumPattern,
    StructDecl, StructField, EnumDecl
)


class ParserError(Exception):
    def __init__(self, message: str, location: SourceLocation):
        super().__init__(f"Syntax Error at {location}: {message}")
        self.message = message
        self.location = location


class Parser:
    def __init__(self, tokens: List[Token], filename: str = "<stdin>"):
        self.tokens = tokens
        self.filename = filename
        self.current = 0

    def parse(self) -> Program:
        statements: List[Stmt] = []
        loc = self._peek().location
        while not self._is_at_end():
            # Skip stray semicolons
            if self._match(TokenType.SEMICOLON):
                continue
            stmt = self._declaration()
            if stmt:
                statements.append(stmt)
        return Program(statements=statements, location=loc)

    # -------------------------------------------------------------------------
    # Helper Navigation Methods
    # -------------------------------------------------------------------------

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise ParserError(message, self._peek().location)

    # -------------------------------------------------------------------------
    # Declarations and Statements
    # -------------------------------------------------------------------------

    def _declaration(self) -> Stmt:
        if self._match(TokenType.LET):
            return self._let_statement()
        if self._match(TokenType.VAR):
            return self._var_statement()
        if self._match(TokenType.FN):
            return self._function_declaration()
        if self._match(TokenType.IMPORT):
            return self._import_statement()
        if self._match(TokenType.STRUCT):
            return self._struct_declaration()
        if self._match(TokenType.ENUM):
            return self._enum_declaration()
        if self._match(TokenType.ACTOR):
            return self._actor_declaration()
        if self._match(TokenType.SPAWN):
            return self._spawn_statement()
        return self._statement()

    def _let_statement(self) -> LetStmt:
        loc = self._previous().location
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'let'")
        type_annotation = None
        if self._match(TokenType.COLON):
            type_annotation = self._parse_type_annotation()
        
        self._consume(TokenType.ASSIGN, "Expected '=' after variable name in 'let' binding")
        initializer = self._expression()
        self._match(TokenType.SEMICOLON)
        return LetStmt(name=name_tok.lexeme, type_annotation=type_annotation, initializer=initializer, location=loc)

    def _var_statement(self) -> VarStmt:
        loc = self._previous().location
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'var'")
        type_annotation = None
        if self._match(TokenType.COLON):
            type_annotation = self._parse_type_annotation()

        self._consume(TokenType.ASSIGN, "Expected '=' after variable name in 'var' declaration")
        initializer = self._expression()
        self._match(TokenType.SEMICOLON)
        return VarStmt(name=name_tok.lexeme, type_annotation=type_annotation, initializer=initializer, location=loc)

    def _parse_type_annotation(self) -> str:
        # e.g., int, string, [int], Option<string>, Result<int, Error>, Tensor<float32, [3, 3]>
        if self._match(TokenType.LBRACKET):
            inner = self._parse_type_annotation()
            self._consume(TokenType.RBRACKET, "Expected ']' closing array type")
            return f"[{inner}]"

        token = self._advance()
        type_str = token.lexeme
        if self._match(TokenType.LT):
            type_str += "<"
            depth = 1
            while depth > 0 and not self._is_at_end():
                t = self._advance()
                if t.type == TokenType.LT:
                    depth += 1
                elif t.type == TokenType.GT:
                    depth -= 1
                type_str += t.lexeme
        return type_str

    def _function_declaration(self) -> FnDecl:
        loc = self._previous().location
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected function name after 'fn'")
        
        self._consume(TokenType.LPAREN, "Expected '(' after function name")
        params: List[Param] = []
        if not self._check(TokenType.RPAREN):
            while True:
                p_loc = self._peek().location
                p_name = self._consume(TokenType.IDENTIFIER, "Expected parameter name").lexeme
                p_type = None
                if self._match(TokenType.COLON):
                    p_type = self._parse_type_annotation()
                p_default = None
                if self._match(TokenType.ASSIGN):
                    p_default = self._expression()
                params.append(Param(name=p_name, type_annotation=p_type, default_value=p_default, location=p_loc))
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RPAREN, "Expected ')' after parameters")

        return_type = None
        if self._match(TokenType.ARROW):
            return_type = self._parse_type_annotation()

        capabilities: List[str] = []
        if self._match(TokenType.WITH):
            self._consume(TokenType.LBRACKET, "Expected '[' after 'with' capabilities")
            while not self._check(TokenType.RBRACKET) and not self._is_at_end():
                cap_tok = self._advance()
                capabilities.append(cap_tok.lexeme)
                if not self._match(TokenType.COMMA):
                    break
            self._consume(TokenType.RBRACKET, "Expected ']' closing capabilities")

        body = self._block()
        return FnDecl(name=name_tok.lexeme, params=params, return_type=return_type, body=body, capabilities=capabilities, location=loc)

    def _import_statement(self) -> ImportStmt:
        loc = self._previous().location
        kind = "era"
        module_path = ""
        
        # Check if python:pkg or c:header or js:pkg
        tok = self._advance()
        if tok.lexeme in ("python", "c", "js", "rust") and self._match(TokenType.COLON):
            kind = tok.lexeme
            # Consume module or string
            if self._check(TokenType.STRING):
                module_path = self._advance().value
            elif self._check(TokenType.IDENTIFIER):
                module_path = self._advance().lexeme
            else:
                raise ParserError("Expected module name or header string in import", self._peek().location)
        elif tok.type == TokenType.STRING:
            kind = "era"
            module_path = tok.value
        elif tok.type == TokenType.IDENTIFIER:
            kind = "era"
            module_path = tok.lexeme
        else:
            raise ParserError("Invalid import syntax", loc)

        alias = None
        if self._match(TokenType.AS):
            alias = self._consume(TokenType.IDENTIFIER, "Expected alias identifier after 'as'").lexeme
        else:
            alias = module_path.split("/")[-1].split(".")[0]

        self._match(TokenType.SEMICOLON)
        return ImportStmt(kind=kind, module_path=module_path, alias=alias, location=loc)

    def _actor_declaration(self) -> ActorDecl:
        loc = self._previous().location
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected actor name")
        self._consume(TokenType.LBRACE, "Expected '{' in actor body")
        
        fields: List[Stmt] = []
        methods: List[FnDecl] = []

        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            if self._match(TokenType.VAR):
                fields.append(self._var_statement())
            elif self._match(TokenType.LET):
                fields.append(self._let_statement())
            elif self._match(TokenType.FN):
                methods.append(self._function_declaration())
            else:
                raise ParserError("Only fields (let/var) and methods (fn) are allowed inside actor", self._peek().location)

        self._consume(TokenType.RBRACE, "Expected '}' closing actor body")
        return ActorDecl(name=name_tok.lexeme, fields=fields, methods=methods, location=loc)

    def _struct_declaration(self) -> StructDecl:
        loc = self._previous().location
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected struct name")
        self._consume(TokenType.LBRACE, "Expected '{' in struct body")
        
        fields: List[StructField] = []
        methods: List[FnDecl] = []

        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            if self._match(TokenType.FN):
                methods.append(self._function_declaration())
            else:
                f_loc = self._peek().location
                f_name = self._consume(TokenType.IDENTIFIER, "Expected field name in struct").lexeme
                f_type = None
                if self._match(TokenType.COLON):
                    f_type = self._parse_type_annotation()
                f_default = None
                if self._match(TokenType.ASSIGN):
                    f_default = self._expression()
                fields.append(StructField(name=f_name, type_annotation=f_type, default_value=f_default, location=f_loc))
                self._match(TokenType.COMMA)
                self._match(TokenType.SEMICOLON)

        self._consume(TokenType.RBRACE, "Expected '}' closing struct body")
        return StructDecl(name=name_tok.lexeme, fields=fields, methods=methods, location=loc)

    def _enum_declaration(self) -> EnumDecl:
        loc = self._previous().location
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected enum name")
        self._consume(TokenType.LBRACE, "Expected '{' in enum body")
        
        variants: List[str] = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            v_tok = self._consume(TokenType.IDENTIFIER, "Expected enum variant name")
            variants.append(v_tok.lexeme)
            if not self._match(TokenType.COMMA):
                break

        self._consume(TokenType.RBRACE, "Expected '}' closing enum body")
        return EnumDecl(name=name_tok.lexeme, variants=variants, location=loc)

    def _spawn_statement(self) -> SpawnStmt:
        loc = self._previous().location
        expr = self._expression()
        if not isinstance(expr, CallExpr):
            raise ParserError("Expected function or method call after 'spawn'", loc)
        self._match(TokenType.SEMICOLON)
        return SpawnStmt(call=expr, location=loc)

    def _statement(self) -> Stmt:
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.FOR):
            return self._for_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.BREAK):
            loc = self._previous().location
            self._match(TokenType.SEMICOLON)
            return BreakStmt(location=loc)
        if self._match(TokenType.CONTINUE):
            loc = self._previous().location
            self._match(TokenType.SEMICOLON)
            return ContinueStmt(location=loc)

        return self._expr_or_assign_statement()

    def _return_statement(self) -> ReturnStmt:
        loc = self._previous().location
        value = None
        if not self._check(TokenType.SEMICOLON) and not self._check(TokenType.RBRACE):
            value = self._expression()
        self._match(TokenType.SEMICOLON)
        return ReturnStmt(value=value, location=loc)

    def _for_statement(self) -> ForStmt:
        loc = self._previous().location
        var_tok = self._consume(TokenType.IDENTIFIER, "Expected iterator variable name in 'for' loop")
        self._consume(TokenType.IN, "Expected 'in' after loop variable")
        iterable = self._expression()
        body = self._block()
        return ForStmt(var_name=var_tok.lexeme, iterable=iterable, body=body, location=loc)

    def _while_statement(self) -> WhileStmt:
        loc = self._previous().location
        condition = self._expression()
        body = self._block()
        return WhileStmt(condition=condition, body=body, location=loc)

    def _expr_or_assign_statement(self) -> Stmt:
        loc = self._peek().location
        expr = self._expression()

        if self._match(TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
                        TokenType.STAR_ASSIGN, TokenType.SLASH_ASSIGN):
            op = self._previous()
            val = self._expression()
            self._match(TokenType.SEMICOLON)
            return AssignStmt(target=expr, op=op, value=val, location=loc)

        self._match(TokenType.SEMICOLON)
        return ExprStmt(expression=expr, location=loc)

    def _block(self) -> BlockExpr:
        loc = self._consume(TokenType.LBRACE, "Expected '{' to start block").location
        stmts: List[Stmt] = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            if self._match(TokenType.SEMICOLON):
                continue
            stmt = self._declaration()
            if stmt:
                stmts.append(stmt)
        self._consume(TokenType.RBRACE, "Expected '}' to close block")
        return BlockExpr(statements=stmts, location=loc)

    # -------------------------------------------------------------------------
    # Expressions (Precedence Climbing)
    # -------------------------------------------------------------------------

    def _expression(self) -> Expr:
        return self._range_expr()

    def _range_expr(self) -> Expr:
        expr = self._logical_or()
        if self._match(TokenType.DOT_DOT_LT):
            loc = self._previous().location
            end = self._logical_or()
            return RangeExpr(start=expr, end=end, half_open=True, location=loc)
        elif self._match(TokenType.DOT_DOT):
            loc = self._previous().location
            end = self._logical_or()
            return RangeExpr(start=expr, end=end, half_open=False, location=loc)
        return expr

    def _logical_or(self) -> Expr:
        expr = self._logical_and()
        while self._match(TokenType.OR):
            op = self._previous()
            right = self._logical_and()
            expr = BinaryExpr(left=expr, operator=op, right=right, location=op.location)
        return expr

    def _logical_and(self) -> Expr:
        expr = self._equality()
        while self._match(TokenType.AND):
            op = self._previous()
            right = self._equality()
            expr = BinaryExpr(left=expr, operator=op, right=right, location=op.location)
        return expr

    def _equality(self) -> Expr:
        expr = self._comparison()
        while self._match(TokenType.EQ, TokenType.NEQ):
            op = self._previous()
            right = self._comparison()
            expr = BinaryExpr(left=expr, operator=op, right=right, location=op.location)
        return expr

    def _comparison(self) -> Expr:
        expr = self._term()
        while self._match(TokenType.LT, TokenType.LTE, TokenType.GT, TokenType.GTE):
            op = self._previous()
            right = self._term()
            expr = BinaryExpr(left=expr, operator=op, right=right, location=op.location)
        return expr

    def _term(self) -> Expr:
        expr = self._factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._previous()
            right = self._factor()
            expr = BinaryExpr(left=expr, operator=op, right=right, location=op.location)
        return expr

    def _factor(self) -> Expr:
        expr = self._unary()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT, TokenType.MATMUL):
            op = self._previous()
            right = self._unary()
            expr = BinaryExpr(left=expr, operator=op, right=right, location=op.location)
        return expr

    def _unary(self) -> Expr:
        if self._match(TokenType.NOT, TokenType.MINUS):
            op = self._previous()
            right = self._unary()
            return UnaryExpr(operator=op, right=right, location=op.location)
        return self._postfix()

    def _postfix(self) -> Expr:
        expr = self._primary()

        while True:
            if self._match(TokenType.LPAREN):
                # Function call
                loc = self._previous().location
                args: List[Expr] = []
                if not self._check(TokenType.RPAREN):
                    while True:
                        args.append(self._expression())
                        if not self._match(TokenType.COMMA):
                            break
                self._consume(TokenType.RPAREN, "Expected ')' after function arguments")
                expr = CallExpr(callee=expr, arguments=args, location=loc)
            elif self._match(TokenType.DOT):
                # Member access
                loc = self._previous().location
                member_tok = self._consume(TokenType.IDENTIFIER, "Expected property or method name after '.'")
                expr = MemberExpr(target=expr, member=member_tok.lexeme, location=loc)
            elif self._match(TokenType.LBRACKET):
                # Index access
                loc = self._previous().location
                index_expr = self._expression()
                self._consume(TokenType.RBRACKET, "Expected ']' after index")
                expr = IndexExpr(target=expr, index=index_expr, location=loc)
            elif self._match(TokenType.QUESTION):
                # Question unwrap / propagation
                loc = self._previous().location
                expr = QuestionExpr(expr=expr, location=loc)
            else:
                break

        return expr

    def _primary(self) -> Expr:
        loc = self._peek().location

        if self._match(TokenType.BOOLEAN):
            return LiteralExpr(value=self._previous().value, type_name="bool", location=loc)
        if self._match(TokenType.INT):
            return LiteralExpr(value=self._previous().value, type_name="int", location=loc)
        if self._match(TokenType.FLOAT):
            return LiteralExpr(value=self._previous().value, type_name="float", location=loc)
        if self._match(TokenType.STRING):
            return LiteralExpr(value=self._previous().value, type_name="string", location=loc)

        if self._match(TokenType.IDENTIFIER):
            return IdentifierExpr(name=self._previous().lexeme, location=loc)

        if self._match(TokenType.CHAN):
            return IdentifierExpr(name="Chan", location=loc)

        # Parenthesized expression
        if self._match(TokenType.LPAREN):
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        # Array literal: [1, 2, 3]
        if self._match(TokenType.LBRACKET):
            elements: List[Expr] = []
            if not self._check(TokenType.RBRACKET):
                while True:
                    elements.append(self._expression())
                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RBRACKET, "Expected ']' closing array literal")
            return ArrayLitExpr(elements=elements, location=loc)

        # Map literal or block: {"key": value}
        if self._check(TokenType.LBRACE):
            return self._map_or_block()

        # Option: Some(val) or None
        if self._match(TokenType.SOME):
            self._consume(TokenType.LPAREN, "Expected '(' after 'Some'")
            val = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' closing 'Some'")
            return OptionLitExpr(variant="Some", value=val, location=loc)
        if self._match(TokenType.NONE):
            return OptionLitExpr(variant="None", value=None, location=loc)

        # Result: Ok(val) or Err(err)
        if self._match(TokenType.OK):
            self._consume(TokenType.LPAREN, "Expected '(' after 'Ok'")
            val = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' closing 'Ok'")
            return ResultLitExpr(variant="Ok", value=val, location=loc)
        if self._match(TokenType.ERR):
            self._consume(TokenType.LPAREN, "Expected '(' after 'Err'")
            val = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' closing 'Err'")
            return ResultLitExpr(variant="Err", value=val, location=loc)

        # Control flow expressions
        if self._match(TokenType.IF):
            return self._if_expression()
        if self._match(TokenType.MATCH):
            return self._match_expression()

        # Tensor literal
        if self._match(TokenType.TENSOR):
            return self._tensor_literal()

        # AI complete expression
        if self._match(TokenType.AI):
            return self._ai_expression()

        raise ParserError(f"Unexpected token '{self._peek().lexeme}' in expression", loc)

    def _map_or_block(self) -> Expr:
        loc = self._peek().location
        # Try to parse as Map literal: {"a": 1}
        # A map starts with { followed by expr : expr
        self._consume(TokenType.LBRACE, "Expected '{'")
        if self._check(TokenType.RBRACE):
            # Empty map {}
            self._advance()
            return MapLitExpr(entries=[], location=loc)

        # Save position to backtrack if it's a block vs map
        saved_pos = self.current
        try:
            k = self._expression()
            if self._match(TokenType.COLON):
                v = self._expression()
                entries = [(k, v)]
                while self._match(TokenType.COMMA):
                    if self._check(TokenType.RBRACE):
                        break
                    k2 = self._expression()
                    self._consume(TokenType.COLON, "Expected ':' after map key")
                    v2 = self._expression()
                    entries.append((k2, v2))
                self._consume(TokenType.RBRACE, "Expected '}' closing map literal")
                return MapLitExpr(entries=entries, location=loc)
        except Exception:
            pass

        # Backtrack to block
        self.current = saved_pos - 1
        return self._block()

    def _if_expression(self) -> IfExpr:
        loc = self._previous().location
        cond = self._expression()
        then_branch = self._block()
        else_branch = None
        if self._match(TokenType.ELSE):
            if self._match(TokenType.IF):
                else_branch = self._if_expression()
            else:
                else_branch = self._block()
        return IfExpr(condition=cond, then_branch=then_branch, else_branch=else_branch, location=loc)

    def _match_expression(self) -> MatchExpr:
        loc = self._previous().location
        subject = self._expression()
        self._consume(TokenType.LBRACE, "Expected '{' in match block")
        
        arms: List[MatchArm] = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            arm_loc = self._peek().location
            pattern = self._parse_pattern()
            guard = None
            if self._match(TokenType.IF):
                guard = self._expression()
            self._consume(TokenType.FAT_ARROW, "Expected '=>' after match pattern")
            
            if self._check(TokenType.LBRACE):
                body = self._block()
            else:
                body = self._expression()
                self._match(TokenType.COMMA)
            
            arms.append(MatchArm(pattern=pattern, guard=guard, body=body, location=arm_loc))

        self._consume(TokenType.RBRACE, "Expected '}' closing match block")
        return MatchExpr(subject=subject, arms=arms, location=loc)

    def _parse_pattern(self) -> Pattern:
        loc = self._peek().location
        if self._match(TokenType.SOME):
            self._consume(TokenType.LPAREN, "Expected '(' after 'Some'")
            inner = self._parse_pattern()
            self._consume(TokenType.RPAREN, "Expected ')' after 'Some' pattern")
            return SomePattern(inner=inner, location=loc)
        if self._match(TokenType.NONE):
            return NonePattern(location=loc)
        if self._match(TokenType.OK):
            self._consume(TokenType.LPAREN, "Expected '(' after 'Ok'")
            inner = self._parse_pattern()
            self._consume(TokenType.RPAREN, "Expected ')' after 'Ok' pattern")
            return OkPattern(inner=inner, location=loc)
        if self._match(TokenType.ERR):
            self._consume(TokenType.LPAREN, "Expected '(' after 'Err'")
            inner = self._parse_pattern()
            self._consume(TokenType.RPAREN, "Expected ')' after 'Err' pattern")
            return ErrPattern(inner=inner, location=loc)

        if self._match(TokenType.INT, TokenType.FLOAT, TokenType.STRING, TokenType.BOOLEAN):
            tok = self._previous()
            return LiteralPattern(value=tok.value, location=loc)

        if self._match(TokenType.IDENTIFIER):
            name = self._previous().lexeme
            if name == "_":
                return WildcardPattern(location=loc)
            if self._match(TokenType.DOT):
                variant_tok = self._consume(TokenType.IDENTIFIER, "Expected variant name after '.' in enum pattern")
                inner_pat = None
                if self._match(TokenType.LPAREN):
                    inner_pat = self._parse_pattern()
                    self._consume(TokenType.RPAREN, "Expected ')' after pattern")
                return EnumPattern(enum_name=name, variant=variant_tok.lexeme, inner=inner_pat, location=loc)
            return IdentifierPattern(name=name, location=loc)

        raise ParserError(f"Invalid pattern '{self._peek().lexeme}'", loc)

    def _tensor_literal(self) -> TensorLitExpr:
        loc = self._previous().location
        self._consume(TokenType.DOT, "Expected '.' after 'Tensor' (e.g. Tensor.zeros, Tensor.randn)")
        method_tok = self._consume(TokenType.IDENTIFIER, "Expected Tensor method name (zeros, ones, randn, from_array)")
        self._consume(TokenType.LPAREN, "Expected '(' in Tensor constructor")
        args: List[Expr] = []
        if not self._check(TokenType.RPAREN):
            while True:
                args.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RPAREN, "Expected ')' closing Tensor constructor")
        return TensorLitExpr(method=method_tok.lexeme, args=args, location=loc)

    def _ai_expression(self) -> AICompleteExpr:
        loc = self._previous().location
        self._consume(TokenType.DOT, "Expected '.' after 'ai'")
        self._consume(TokenType.IDENTIFIER, "Expected 'complete' after 'ai.'")
        schema_type = None
        if self._match(TokenType.LT):
            schema_type = self._parse_type_annotation()
            self._consume(TokenType.GT, "Expected '>' closing ai schema type")
        
        self._consume(TokenType.LPAREN, "Expected '(' in ai call")
        prompt_expr = self._expression()
        model_expr = None
        if self._match(TokenType.COMMA):
            if self._check(TokenType.IDENTIFIER) and self._peek().lexeme == "model":
                self._advance()
                self._consume(TokenType.COLON, "Expected ':' after 'model'")
                model_expr = self._expression()
            else:
                model_expr = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' closing ai call")
        return AICompleteExpr(prompt=prompt_expr, model=model_expr, schema_type=schema_type, location=loc)
