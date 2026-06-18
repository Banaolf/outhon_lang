from sys import argv
from lexer import lex
from parser import parse_tokens
from interpreter import interpret
from error_handler import *

argc = len(argv)

def main():
    if argc <= 1: print("Usage:python outhon.py <flags (currently none)> <filepath>"); return
    fileContent = None
    try:
        with open(argv[-1], "r") as f:
            fileContent = f.read()
    except Exception as e:
        print(f"Unhandled exception: {e}")
        return

    tokens = lex(fileContent)
    if has_error(): print_error(); return

    program = parse_tokens(tokens)
    if has_error(): print_error(); return

    interpret(program)
    if has_error(): print_error()

if __name__ == "__main__":
    main()