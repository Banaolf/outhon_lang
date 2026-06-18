"""
Outhon Interpreter
"""

from parser import (
    Program, Block, Statement,
    IntLiteral, FloatLiteral, StringLiteral, BoolLiteral,
    VariableGet, FunctionCall, BinaryOp, UnaryOp,
    VariableDecl, Assignment, FunctionDecl, IfStatement, WhileLoop,
)
from error_handler import report_error, errty


class OuthonFunction:
    def __init__(self, name: str, params: list, body: Block, closure: "Environment"):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

    def __repr__(self):
        return f"<function {self.name}>"


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class Environment:
    def __init__(self, parent: "Environment | None" = None):
        self._vars: dict = {}
        self.parent = parent

    def get(self, name: str, line=None, char=None):
        if name in self._vars:
            return self._vars[name]
        if self.parent is not None:
            return self.parent.get(name, line, char)
        report_error(
            f"Undefined variable '{name}'",
            errty.RuntimeError,
            line, char
        )
        return None

    def set(self, name: str, value):
        self._vars[name] = value

    def assign(self, name: str, value, line=None, char=None):
        if name in self._vars:
            self._vars[name] = value
            return
        if self.parent is not None:
            self.parent.assign(name, value, line, char)
            return
        report_error(
            f"Assignment to undeclared variable '{name}'",
            errty.RuntimeError,
            line, char
        )


def _builtin_print(*args):
    print(*args)
    return None


def _builtin_str(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _builtin_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        report_error(f"Cannot convert {value!r} to int", errty.RuntimeError, None, None)
        return None


def _builtin_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        report_error(f"Cannot convert {value!r} to float", errty.RuntimeError, None, None)
        return None


def _builtin_bool(value):
    return bool(value)


def _builtin_len(value):
    try:
        return len(value)
    except TypeError:
        report_error(f"len() argument has no length", errty.RuntimeError, None, None)
        return None


def _builtin_type(value):
    if isinstance(value, bool):   return "bool"
    if isinstance(value, int):    return "int"
    if isinstance(value, float):  return "float"
    if isinstance(value, str):    return "str"
    if isinstance(value, OuthonFunction): return "function"
    if value is None:             return "null"
    return "unknown"


def build_global_env() -> Environment:
    env = Environment()
    env.set("print",  _builtin_print)
    env.set("str",    _builtin_str)
    env.set("int",    _builtin_int)
    env.set("float",  _builtin_float)
    env.set("bool",   _builtin_bool)
    env.set("len",    _builtin_len)
    env.set("type",   _builtin_type)
    env.set("null",   None)
    env.set("true",   True)
    env.set("false",  False)
    return env


class Interpreter:
    def __init__(self):
        self.global_env = build_global_env()

    def run(self, program: Program):
        self.exec_block_in_env(program.body, self.global_env)

    def exec_block(self, block: Block, env: Environment):
        self.exec_block_in_env(block.body, env)

    def exec_block_in_env(self, stmts: list, env: Environment):
        for stmt in stmts:
            self.exec_statement(stmt, env)

    def exec_statement(self, stmt: Statement, env: Environment):
        self.exec_node(stmt.value, env)

    def exec_node(self, node, env: Environment):
        if isinstance(node, VariableDecl):
            return self.exec_var_decl(node, env)
        if isinstance(node, Assignment):
            return self.exec_assignment(node, env)
        if isinstance(node, FunctionDecl):
            return self.exec_func_decl(node, env)
        if isinstance(node, IfStatement):
            return self.exec_if(node, env)
        if isinstance(node, WhileLoop):
            return self.exec_while(node, env)
        return self.eval_expr(node, env)

    def exec_var_decl(self, node: VariableDecl, env: Environment):
        value = self.eval_expr(node.value, env)
        env.set(node.name, value)

    def exec_assignment(self, node: Assignment, env: Environment):
        value = self.eval_expr(node.value, env)
        env.assign(node.target, value)

    def exec_func_decl(self, node: FunctionDecl, env: Environment):
        fn = OuthonFunction(node.name, node.params, node.body, env)
        env.set(node.name, fn)

    def exec_if(self, node: IfStatement, env: Environment):
        if self._truthy(self.eval_expr(node.condition, env)):
            self.exec_block(node.then_block, Environment(env))
            return
        for (cond, block) in node.elseif_clauses:
            if self._truthy(self.eval_expr(cond, env)):
                self.exec_block(block, Environment(env))
                return
        if node.else_block is not None:
            self.exec_block(node.else_block, Environment(env))

    def exec_while(self, node: WhileLoop, env: Environment):
        while self._truthy(self.eval_expr(node.condition, env)):
            self.exec_block(node.body, Environment(env))

    def eval_expr(self, node, env: Environment):
        if isinstance(node, IntLiteral):
            return node.value

        if isinstance(node, FloatLiteral):
            return node.value

        if isinstance(node, StringLiteral):
            return node.value

        if isinstance(node, BoolLiteral):
            return node.value

        if isinstance(node, VariableGet):
            return env.get(node.name)

        if isinstance(node, BinaryOp):
            return self.eval_binop(node, env)

        if isinstance(node, UnaryOp):
            return self.eval_unop(node, env)

        if isinstance(node, FunctionCall):
            return self.eval_call(node, env)

        report_error(
            f"Unknown expression node: {type(node).__name__}",
            errty.RuntimeError,
            None, None
        )
        return None

    def eval_binop(self, node: BinaryOp, env: Environment):
        left  = self.eval_expr(node.left,  env)
        right = self.eval_expr(node.right, env)
        op    = node.op

        if op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return _builtin_str(left) + _builtin_str(right)
            return left + right
        if op == "-":  return left - right
        if op == "*":  return left * right
        if op == "/":
            if right == 0:
                report_error("Division by zero", errty.RuntimeError, None, None)
                return None
            return left / right
        if op == "%":  return left % right

        if op == "&":  return int(left) & int(right)
        if op == "|":  return int(left) | int(right)
        if op == "^":  return int(left) ^ int(right)
        if op == "<<": return int(left) << int(right)
        if op == ">>": return int(left) >> int(right)

        if op == "==": return left == right
        if op == "!=": return left != right
        if op == ">":  return left > right
        if op == "<":  return left < right
        if op == ">=": return left >= right
        if op == "<=": return left <= right

        if op == "&&": return self._truthy(left) and self._truthy(right)
        if op == "||": return self._truthy(left) or  self._truthy(right)

        report_error(
            f"Unknown binary operator '{op}'",
            errty.RuntimeError,
            None, None
        )
        return None

    def eval_unop(self, node: UnaryOp, env: Environment):
        val = self.eval_expr(node.expr, env)
        if node.op == "-":  return -val
        if node.op == "~":  return ~int(val)
        if node.op == "!":  return not self._truthy(val)

        report_error(
            f"Unknown unary operator '{node.op}'",
            errty.RuntimeError,
            None, None
        )
        return None

    def eval_call(self, node: FunctionCall, env: Environment):
        callee = self.eval_expr(node.callee, env)
        args   = [self.eval_expr(a, env) for a in node.args]

        if callable(callee) and not isinstance(callee, OuthonFunction):
            return callee(*args)

        if isinstance(callee, OuthonFunction):
            if len(args) != len(callee.params):
                report_error(
                    f"'{callee.name}' expects {len(callee.params)} argument(s), "
                    f"got {len(args)}",
                    errty.RuntimeError,
                    None, None
                )
                return None

            call_env = Environment(callee.closure)
            for param, arg in zip(callee.params, args):
                call_env.set(param, arg)

            try:
                self.exec_block(callee.body, call_env)
            except ReturnSignal as ret:
                return ret.value
            return None

        report_error(
            f"'{callee}' is not callable",
            errty.RuntimeError,
            None, None
        )
        return None

    @staticmethod
    def _truthy(value) -> bool:
        if value is None:   return False
        if value is False:  return False
        if isinstance(value, (int, float)) and value == 0:
            return False
        if isinstance(value, str) and value == "":
            return False
        return True

def interpret(program: Program):
    Interpreter().run(program)