from __future__ import annotations

import ast
import operator
import re

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluate an arithmetic expression such as '199 * 12' and return the number.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "The arithmetic expression to evaluate."}
            },
            "required": ["expression"],
        },
    },
}


def _eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported expression")


def evaluate(expression: str) -> float | None:
    expr = re.sub(r"[^0-9+\-*/(). ]", "", expression).strip()
    if not expr:
        return None
    try:
        return round(_eval(ast.parse(expr, mode="eval").body), 4)
    except Exception:
        return None


def looks_like_math(query: str) -> bool:
    expr = re.sub(r"[^0-9+\-*/(). ]", "", query)
    return bool(re.search(r"\d\s*[+\-*/]\s*\d", expr))
