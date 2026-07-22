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


def _eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported expression")


def maybe_calculate(query: str) -> float | None:
    expr = re.sub(r"[^0-9+\-*/(). ]", "", query)
    if not re.search(r"\d\s*[+\-*/]\s*\d", expr):
        return None
    try:
        return round(_eval(ast.parse(expr, mode="eval").body), 4)
    except Exception:
        return None
