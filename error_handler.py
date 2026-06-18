"""
Houston, we have a problem. No worries! The Outhon error handler is here.
"""

from enum import Enum as enum
from logging import error

class errty(enum):
    SyntaxErr = 0,
    ExpectationError = 1

    def __str__(self):
        match self:
            case errty.SyntaxErr: return "SyntaxError"
            case errty.ExpectationError: return "ExpectationError"

_currenterr = None

def report_error(msg: str, ty: errty, line: int, char: int):
    global _currenterr
    _currenterr = (msg, ty, line, char)

def clear_error():
    global _currenterr
    _currenterr = None

def has_error() -> bool:
    return _currenterr is not None

def print_error():
    msg, ty, line, char = _currenterr
    error(f"At {line}, character {char}:\n [{str(ty)}]: {msg}")