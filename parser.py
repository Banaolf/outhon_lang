"""
Outhon Parser
"""

from lexer import TokType
from error_handler import report_error, errty

# AST

class Node:
    pass


class Statement(Node):
    def __init__(self, value):
        self.value = value


class Expression(Node):
    pass


class Order(Node):
    pass


class Program(Node):
    def __init__(self):
        self.body = []


class Block(Node):
    def __init__(self):
        self.body = []


# Expressions

class IntLiteral(Expression):
    def __init__(self, value: int):
        self.value = value


class FloatLiteral(Expression):
    def __init__(self, value: float):
        self.value = value


class StringLiteral(Expression):
    def __init__(self, value: str):
        self.value = value


class BoolLiteral(Expression):
    def __init__(self, value: bool):
        self.value = value


class VariableGet(Expression):
    def __init__(self, name: str):
        self.name = name


class FunctionCall(Expression):
    def __init__(self, callee: Expression, args: list):
        self.callee = callee
        self.args = args


class BinaryOp(Expression):
    def __init__(self, left, op: str, right):
        self.left = left
        self.op = op
        self.right = right


class UnaryOp(Expression):
    def __init__(self, op: str, expr):
        self.op = op
        self.expr = expr


# Orders

class VariableDecl(Order):
    def __init__(self, name: str, value):
        self.name = name
        self.value = value


class Assignment(Order):
    def __init__(self, target: str, value):
        self.target = target
        self.value = value


class FunctionDecl(Order):
    def __init__(self, name: str, params: list[str], body: Block):
        self.name = name
        self.params = params
        self.body = body


class IfStatement(Order):
    def __init__(self, condition, then_block: Block, elseif_clauses: list, else_block):
        # condition     : Expression
        # then_block    : Block
        # elseif_clauses: list of (Expression, Block) tuples for `else if` chains
        # else_block    : Block | None
        self.condition = condition
        self.then_block = then_block
        self.elseif_clauses = elseif_clauses
        self.else_block = else_block


class WhileLoop(Order):
    def __init__(self, condition, body: Block):
        # condition: Expression
        # body     : Block
        self.condition = condition
        self.body = body


# Parser State

gTL = []
pos = 0
current = None


# Helpers

def _adv():
    global pos, current

    pos += 1

    if pos >= len(gTL):
        current = gTL[-1]
    else:
        current = gTL[pos]


def peek(offset=1):
    idx = pos + offset

    if idx >= len(gTL):
        return gTL[-1]

    return gTL[idx]


def expect(expected):
    if isinstance(expected, TokType):
        if current.ty != expected:
            report_error(
                f"Expected {expected}, got {current.ty}",
                errty.ExpectationError,
                current.line,
                current.char
            )
            return False

    elif isinstance(expected, str):
        if current.value != expected:
            report_error(
                f"Expected '{expected}', got '{current.value}'",
                errty.ExpectationError,
                current.line,
                current.char
            )
            return False

    _adv()
    return True


def skip_newlines():
    while current.ty == TokType.Newline:
        _adv()


# Entry

def parse_tokens(tokens):
    global gTL, pos, current
    gTL = tokens
    pos = 0
    current = gTL[0]
    program = Program()
    while current.ty != TokType.EOF:
        skip_newlines()
        if current.ty == TokType.EOF:
            break
        stmt = parse_statement()
        if stmt is not None:
            program.body.append(stmt)
    return program


# Statements

def parse_statement():
    if current.ty == TokType.Keyword:
        if current.value == "let":
            return Statement(parse_let())
        if current.value == "if":
            return Statement(parse_if())
        if current.value == "while":
            return Statement(parse_while())
    if current.ty == TokType.Identifier:
        if current.ty == TokType.Identifier and (
            peek().ty == TokType.Equals
            or peek().ty == TokType.CompOperator
            or peek().ty == TokType.CompBinOperator
        ):
            return Statement(parse_assignment())
    return Statement(parse_expression())


# Orders

def parse_let():
    expect("let")
    name = current.value
    expect(TokType.Identifier)
    # function declaration
    if current.value == "(":
        params = []
        expect("(")
        while current.value != ")":

            params.append(current.value)
            expect(TokType.Identifier)

            if current.value == ",":
                expect(",")
        expect(")")
        body = parse_block()
        return FunctionDecl(
            name,
            params,
            body
        )
    # variable declaration
    expect("=")
    value = parse_expression()
    return VariableDecl(
        name,
        value
    )


def parse_block():
    block = Block()
    expect("{")
    skip_newlines()
    while current.value != "}":
        block.body.append(
            parse_statement()
        )
        skip_newlines()
    expect("}")
    return block


def parse_if():
    expect("if")
    expect("(")
    condition = parse_expression()
    expect(")")
    then_block = parse_block()

    elseif_clauses = []
    else_block = None

    # Consume newlines between the closing `}` and a potential `else`
    skip_newlines()

    while current.ty == TokType.Keyword and current.value == "else":
        _adv()  # consume `else`

        if current.ty == TokType.Keyword and current.value == "if":
            # `else if` branch
            _adv()  # consume `if`
            expect("(")
            elseif_cond = parse_expression()
            expect(")")
            elseif_block = parse_block()
            elseif_clauses.append((elseif_cond, elseif_block))
            skip_newlines()
        else:
            # plain `else` — must be the last clause
            else_block = parse_block()
            break

    return IfStatement(condition, then_block, elseif_clauses, else_block)


def parse_while():
    expect("while")
    expect("(")
    condition = parse_expression()
    expect(")")
    body = parse_block()
    return WhileLoop(condition, body)


def parse_assignment():
    name = current.value
    expect(TokType.Identifier)
    op = current.value
    if current.ty in (
        TokType.CompOperator,
        TokType.CompBinOperator
    ):
        expect(current.ty)
        rhs = parse_expression()
        base_op = op[:-1]
        return Assignment(
            name,
            BinaryOp(
                VariableGet(name),
                base_op,
                rhs
            )
        )
    expect("=")
    value = parse_expression()
    return Assignment(
        name,
        value
    )


# Expressions

def parse_expression():
    return parse_bitwise()

def parse_bitwise():
    expr = parse_comparison()
    while (
        current.ty == TokType.BinOperator
    ):
        op = current.value
        _adv()
        right = parse_comparison()
        expr = BinaryOp(
            expr,
            op,
            right
        )
    return expr


def parse_comparison():
    expr = parse_shift()
    while current.ty in (
        TokType.GRT,
        TokType.LOT,
        TokType.ComparisonEqu
    ):
        op = current.value
        _adv()
        right = parse_shift()
        expr = BinaryOp(
            expr,
            op,
            right
        )
    return expr


def parse_shift():
    expr = parse_additive()
    while (
        current.ty == TokType.BinOperator
        and current.value in ("<<", ">>")
    ):
        op = current.value
        _adv()
        right = parse_additive()
        expr = BinaryOp(
            expr,
            op,
            right
        )

    return expr


def parse_additive():
    expr = parse_multiplicative()
    while (
        current.ty == TokType.Operator
        and current.value in ("+", "-")
    ):
        op = current.value
        _adv()
        right = parse_multiplicative()

        expr = BinaryOp(
            expr,
            op,
            right
        )

    return expr


def parse_multiplicative():
    expr = parse_unary()

    while (
        current.ty == TokType.Operator
        and current.value in ("*", "/")
    ) or current.ty == TokType.Modulo:
        op = current.value
        _adv()
        right = parse_unary()
        expr = BinaryOp(
            expr,
            op,
            right
        )

    return expr


def parse_unary():
    if (
        current.ty == TokType.Operator
        and current.value == "-"
    ):
        _adv()
        return UnaryOp(
            "-",
            parse_unary()
        )

    if (
        current.ty == TokType.BinOperator
        and current.value == "~"
    ):

        _adv()

        return UnaryOp(
            "~",
            parse_unary()
        )

    return parse_primary()


def parse_primary():
    tok = current

    if tok.ty == TokType.Int:
        _adv()
        return IntLiteral(int(tok.value))

    if tok.ty == TokType.Float:
        _adv()
        return FloatLiteral(float(tok.value))

    if tok.ty in (
        TokType.String,
        TokType.RString
    ):
        _adv()
        return StringLiteral(tok.value)

    if tok.ty == TokType.Boolean:
        _adv()
        return BoolLiteral(
            tok.value.lower() == "true"
        )

    if tok.ty == TokType.Identifier:
        return parse_identifier()

    if tok.value == "(":
        expect("(")
        expr = parse_expression()
        expect(")")
        return expr

    report_error(
        "Expected expression",
        errty.SyntaxErr,
        tok.line,
        tok.char
    )

    return None


def parse_identifier():
    name = current.value
    expect(TokType.Identifier)
    expr = VariableGet(name)
    while current.value == "(":
        args = []
        expect("(")
        while current.value != ")":
            args.append(
                parse_expression()
            )
            if current.value == ",":
                expect(",")

        expect(")")
        expr = FunctionCall(
            expr,
            args
        )

    return expr