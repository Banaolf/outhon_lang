"""
Lexing needs to be done? No problem-o. The Outhon Lexer is here!
"""
from globals import KEYWORDS
from error_handler import *
from enum import Enum as enum
from typing import Iterator

ESCAPE_MAP = {
'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f',
'v': '\v', 'a': '\a', '0': '\x00', '"': '"', "'": "'", '\\': '\\'
}

def process_escape(current_char: str, position: list[int, int], stream_iterator: Iterator[str]) -> str:
	try:
		escape_char = next(stream_iterator)
	except StopIteration:
		report_error("Unexpected EOF inside escape sequence", errty.SyntaxErr, position[0], position[1])
		return ""

	if escape_char in ESCAPE_MAP:
		return ESCAPE_MAP[escape_char]

	if escape_char == 'x':
		try:
			h1 = next(stream_iterator)
			h2 = next(stream_iterator)
		except StopIteration:
			report_error("Unexpected EOF inside \\x hex escape", errty.SyntaxErr, position[0], position[1])
			return ""

		try:
			return chr(int(h1 + h2, 16))
		except ValueError:
			report_error(f"Invalid hex escape sequence: \\x{h1}{h2}", errty.SyntaxErr, position[0], position[1])
			return ""

	if '0' <= escape_char <= '7':
		octal_digits = [escape_char]

		for _ in range(2):
			try:
				next_char = next(stream_iterator)
				if '0' <= next_char <= '7':
					octal_digits.append(next_char)
				else:
					report_error("Requires lookahead to not lose non-octal char", errty.SyntaxErr, position[0], position[1])
					return ""
			except StopIteration:
				break

		octal_str = "".join(octal_digits)
		char_val = int(octal_str, 8)

		if char_val > 255:
			report_error("Octal escapes out of range (0-255)", errty.SyntaxErr, position[0], position[1])
			return ""

		return chr(char_val)

	report_error(f"Invalid escape sequence: \\{escape_char}", errty.SyntaxErr, position[0], position[1])

class TokType(enum):
	Identifier = 0,
	Newline = 1,
	Int = 2,
	Float = 3,
	Keyword = 4,
	Boolean = 5,
	Equals = 6,
	Operator = 7,
	CompOperator = 8,
	BinOperator = 9,
	CompBinOperator = 10,
	GRT = 11,
	LOT = 12,
	ComparisonEqu = 13,
	Parenthesis = 14,
	Squared = 15,
	Curly = 16,
	EOF = 17,
	Comma = 18,
	Dot = 19,
	Semicolon = 20,
	Colon = 21,
	String = 22,
	RString = 23,
	Backslash = 24,
	Modulo = 25,
	Root = 26

	def __str__(self):
		match self:
			case TokType.Identifier: return "Identifier"
			case TokType.Newline: return "Newline"
			case TokType.Int: return "Integer"
			case TokType.Float: return "Float"
			case TokType.Keyword: return "Keyword"
			case TokType.Boolean: return "Boolean"
			case TokType.Equals: return "Equals"
			case TokType.Operator: return "Operator"
			case TokType.CompOperator: return "Compound Operator"
			case TokType.BinOperator: return "Binary Operator"
			case TokType.CompBinOperator: return "Compound Binary Operator"
			case TokType.GRT: return "Greater Than"
			case TokType.LOT: return "Lower Than"
			case TokType.ComparisonEqu: return "Equal to"
			case TokType.Parenthesis: return "Parenthesis"
			case TokType.Squared: return "Squared Brackets"
			case TokType.Curly: return "Curly Brackets"
			case TokType.EOF: return "End of line"
			case TokType.Comma: return "Comma"
			case TokType.Dot: return "Dot"
			case TokType.Colon: return "Colon"
			case TokType.Semicolon: return "Semicolon"
			case TokType.String: return "String"
			case TokType.RString: return "Raw String"
			case TokType.Backslash: return "Backslash"
			case TokType.Modulo: return "Modulo"
			case TokType.Root: return "Root"

class Tok:
	def __init__(self, contents:str, ttype:TokType, startline: int, startchar: int):
		self._ty = ttype
		self._val = contents
		self._sl = startline
		self._sc = startchar

	@property
	def ty(self) -> TokType:
		return self._ty

	@property
	def value(self) -> str:
		return self._val

	@property
	def line(self) -> int:
		return self._sl

	@property
	def char(self) -> int:
		return self._sc

	def __eq__(self, o:object) -> bool:
		if isinstance(o, TokType):
			return self._ty == o
		elif isinstance(o, str):
			return self._val == o
		elif isinstance(o, Tok):
			return self is o
		else:
			raise NotImplementedError(o)

	def change(self, contents: str|None=None, ttype: TokType|None=None):
		if contents is not None:
			self._val = contents
		if ttype is not None:
			self._ty = ttype

	def __getitem__(self, key: str):
		if key == "type":
			return self._ty
		elif key == "contents" or key == "value":
			return self._val
		elif key == "startline":
			return self._sl
		elif key == "startchar":
			return self._sc

	def __str__(self):
		return f"Token of type {str(self._ty)} and contents {self._val} at line {self._sl}, character {self._sc}"

	def __repr__(self):
		return f"Tok[{str(self._ty)}, {self._val}, {str(self._sl)}, {str(self._sc)}]"

def lex(to_lex: str) -> list[Tok]:
	stream: list[Tok] = []
	i = 0
	pos = 1
	line = 1

	while i < len(to_lex):
		char = to_lex[i]

		if char.isspace():
			if char == '\n':
				stream.append(Tok('\n', TokType.Newline, line, pos))
				line += 1
				pos = 1
			else:
				pos += 1
			i += 1
			continue

		if char.isalpha() or char == "_":
			buf = ""
			startpos = pos

			while i < len(to_lex) and (to_lex[i].isalnum() or to_lex[i] == "_"):
				buf += to_lex[i]
				i += 1
				pos += 1

			if buf in KEYWORDS:
				stream.append(Tok(buf, TokType.Keyword, line, startpos))
			elif buf.lower() in ("true", "false"):
				stream.append(Tok(buf, TokType.Boolean, line, startpos))
			else:
				stream.append(Tok(buf, TokType.Identifier, line, startpos))
			continue

		if char == '"':
			buf = ""
			startpos = pos
			i += 1
			pos += 1

			while i < len(to_lex) and to_lex[i] != '"':
				if to_lex[i] == "\\":
					esc_iter = iter(to_lex[i + 1:])
					buf += process_escape("\\", (line, startpos), esc_iter)
					i += 2
					pos += 2
				else:
					buf += to_lex[i]
					i += 1
					pos += 1

			if i >= len(to_lex):
				report_error("Unterminated string", errty.SyntaxErr, line, startpos)
				break

			i += 1
			pos += 1
			stream.append(Tok(buf, TokType.String, line, startpos))
			continue

		if char == "'":
			buf = ""
			startpos = pos
			i += 1
			pos += 1

			while i < len(to_lex) and to_lex[i] != "'":
				buf += to_lex[i]
				i += 1
				pos += 1

			if i >= len(to_lex):
				report_error("Unterminated raw string", errty.SyntaxErr, line, startpos)
				break

			i += 1
			pos += 1
			stream.append(Tok(buf, TokType.RString, line, startpos))
			continue

		if char.isdigit():
			buf = ""
			startpos = pos

			while i < len(to_lex) and (to_lex[i].isdigit() or to_lex[i] == "."):
				buf += to_lex[i]
				i += 1
				pos += 1

			parts = buf.split(".")
			if len(parts) == 1:
				stream.append(Tok(buf, TokType.Int, line, startpos))
			elif len(parts) == 2:
				stream.append(Tok(buf, TokType.Float, line, startpos))
			else:
				report_error("Cannot have multiple dots in a float.", errty.SyntaxErr, line, startpos)
			continue

		startpos = pos
		next_char = to_lex[i + 1] if i + 1 < len(to_lex) else None

		if char == "=":
			if next_char == "=":
				stream.append(Tok("==", TokType.ComparisonEqu, line, startpos))
				i += 2
				pos += 2
			else:
				stream.append(Tok("=", TokType.Equals, line, startpos))
				i += 1
				pos += 1
			continue

		if char in "+/*-":
			if next_char == "=":
				stream.append(Tok(char + "=", TokType.CompOperator, line, startpos))
				i += 2
				pos += 2
			else:
				stream.append(Tok(char, TokType.Operator, line, startpos))
				i += 1
				pos += 1
			continue

		if char in "<>":
			if next_char == char:
				third = to_lex[i + 2] if i + 2 < len(to_lex) else None

				if third == "=":
					stream.append(Tok(char * 2 + "=", TokType.CompBinOperator, line, startpos))
					i += 3
					pos += 3
				else:
					stream.append(Tok(char * 2, TokType.BinOperator, line, startpos))
					i += 2
					pos += 2
			else:
				stream.append(Tok(char, TokType.GRT if char == ">" else TokType.LOT, line, startpos))
				i += 1
				pos += 1
			continue

		if char in "&~":
			if next_char == "=":
				stream.append(Tok(char + "=", TokType.CompBinOperator, line, startpos))
				i += 2
				pos += 2
			else:
				stream.append(Tok(char, TokType.BinOperator, line, startpos))
				i += 1
				pos += 1
			continue

		if char in "()":
			stream.append(Tok(char, TokType.Parenthesis, line, startpos))
		elif char in "[]":
			stream.append(Tok(char, TokType.Squared, line, startpos))
		elif char in "{}":
			stream.append(Tok(char, TokType.Curly, line, startpos))
		elif char == ".":
			stream.append(Tok(char, TokType.Dot, line, startpos))
		elif char == ",":
			stream.append(Tok(char, TokType.Comma, line, startpos))
		elif char == ";":
			stream.append(Tok(char, TokType.Semicolon, line, startpos))
		elif char == ":":
			stream.append(Tok(char, TokType.Colon, line, startpos))
		elif char == "\\":
			stream.append(Tok(char, TokType.Backslash, line, startpos))
		elif char == "%":
			stream.append(Tok(char, TokType.Modulo, line, startpos))
		else:
			report_error("Unknown character", errty.SyntaxErr, line, startpos)

		i += 1
		pos += 1

	stream.append(Tok("\0", TokType.EOF, line, pos))
	return stream