"""Excel-compatible formula engine for Clice Sheets."""

from __future__ import annotations

import ast
import math
import operator
import re
from typing import Any, Callable

CELL_REF_RE = re.compile(r"\b([A-Za-z]+)([0-9]+)\b")
RANGE_RE = re.compile(r"\b([A-Za-z]+)([0-9]+):([A-Za-z]+)([0-9]+)\b")


def col_letters_to_index(letters: str) -> int:
    """Convert Excel column letters (A -> 0, B -> 1, AA -> 26)."""
    idx = 0
    for ch in letters.upper():
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def index_to_col_letters(index: int) -> str:
    """Convert 0-based column index to Excel column letters (0 -> A, 26 -> AA)."""
    letters = []
    n = index + 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        letters.append(chr(ord("A") + rem))
    return "".join(reversed(letters))


def parse_cell_ref(ref: str) -> tuple[int, int]:
    """Parse 'B3' -> (row=2, col=1)."""
    m = re.fullmatch(r"([A-Za-z]+)([0-9]+)", ref.strip())
    if not m:
        raise ValueError(f"Invalid cell reference: {ref}")
    col = col_letters_to_index(m.group(1))
    row = int(m.group(2)) - 1
    return row, col


def expand_range(start_col: str, start_row: str, end_col: str, end_row: str) -> list[tuple[int, int]]:
    """Expand A1:B2 into [(0,0), (0,1), (1,0), (1,1)]."""
    c1, r1 = col_letters_to_index(start_col), int(start_row) - 1
    c2, r2 = col_letters_to_index(end_col), int(end_row) - 1
    r_lo, r_hi = min(r1, r2), max(r1, r2)
    c_lo, c_hi = min(c1, c2), max(c1, c2)
    return [(r, c) for r in range(r_lo, r_hi + 1) for c in range(c_lo, c_hi + 1)]


def _to_number(val: Any) -> float | None:
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _flatten_numbers(args: tuple[Any, ...]) -> list[float]:
    nums: list[float] = []
    for a in args:
        if isinstance(a, list):
            for item in a:
                n = _to_number(item)
                if n is not None:
                    nums.append(n)
        else:
            n = _to_number(a)
            if n is not None:
                nums.append(n)
    return nums


def _flatten_all(args: tuple[Any, ...]) -> list[Any]:
    out: list[Any] = []
    for a in args:
        if isinstance(a, list):
            out.extend(a)
        else:
            out.append(a)
    return out


_SAFE_BINOPS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_SAFE_UNARYOPS: dict[type[ast.unaryop], Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_SAFE_CMPOPS: dict[type[ast.cmpop], Callable[[Any, Any], bool]] = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}


def _build_functions() -> dict[str, Callable[..., Any]]:
    def fn_sum(*args: Any) -> float:
        return sum(_flatten_numbers(args))

    def fn_avg(*args: Any) -> float:
        nums = _flatten_numbers(args)
        return sum(nums) / len(nums) if nums else 0.0

    def fn_min(*args: Any) -> float:
        nums = _flatten_numbers(args)
        return min(nums) if nums else 0.0

    def fn_max(*args: Any) -> float:
        nums = _flatten_numbers(args)
        return max(nums) if nums else 0.0

    def fn_count(*args: Any) -> int:
        return len(_flatten_numbers(args))

    def fn_counta(*args: Any) -> int:
        return sum(1 for x in _flatten_all(args) if str(x).strip() != "")

    def fn_if(cond: Any, true_val: Any, false_val: Any = "") -> Any:
        return true_val if cond else false_val

    def fn_round(val: Any, digits: int = 0) -> float:
        return round(float(val), int(digits))

    def fn_abs(val: Any) -> float:
        return abs(float(val))

    def fn_sqrt(val: Any) -> float:
        return math.sqrt(float(val))

    def fn_power(base: Any, exp: Any) -> float:
        return math.pow(float(base), float(exp))

    def fn_concat(*args: Any) -> str:
        return "".join(str(x) for x in _flatten_all(args))

    def fn_median(*args: Any) -> float:
        nums = sorted(_flatten_numbers(args))
        if not nums:
            return 0.0
        mid = len(nums) // 2
        return nums[mid] if len(nums) % 2 else (nums[mid - 1] + nums[mid]) / 2.0

    def fn_stdev(*args: Any) -> float:
        nums = _flatten_numbers(args)
        if len(nums) < 2:
            return 0.0
        mean = sum(nums) / len(nums)
        return math.sqrt(sum((x - mean) ** 2 for x in nums) / (len(nums) - 1))

    def fn_product(*args: Any) -> float:
        nums = _flatten_numbers(args)
        res = 1.0
        for n in nums:
            res *= n
        return res if nums else 0.0

    def fn_upper(val: Any) -> str:
        return str(val).upper()

    def fn_lower(val: Any) -> str:
        return str(val).lower()

    def fn_trim(val: Any) -> str:
        return str(val).strip()

    def fn_len(val: Any) -> int:
        return len(str(val))

    def fn_left(val: Any, n: Any = 1) -> str:
        return str(val)[: int(n)]

    def fn_right(val: Any, n: Any = 1) -> str:
        k = int(n)
        return str(val)[-k:] if k > 0 else ""

    def fn_mod(a: Any, b: Any) -> float:
        return float(a) % float(b)

    def fn_int(val: Any) -> int:
        return int(math.floor(float(val)))

    def fn_ceil(val: Any) -> int:
        return int(math.ceil(float(val)))

    def fn_floor(val: Any) -> int:
        return int(math.floor(float(val)))

    def fn_today() -> str:
        from datetime import date
        return date.today().isoformat()

    def fn_now() -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    return {
        "SUM": fn_sum,
        "AVG": fn_avg,
        "AVERAGE": fn_avg,
        "MIN": fn_min,
        "MAX": fn_max,
        "COUNT": fn_count,
        "COUNTA": fn_counta,
        "IF": fn_if,
        "ROUND": fn_round,
        "ABS": fn_abs,
        "SQRT": fn_sqrt,
        "POWER": fn_power,
        "CONCAT": fn_concat,
        "MEDIAN": fn_median,
        "STDEV": fn_stdev,
        "PRODUCT": fn_product,
        "UPPER": fn_upper,
        "LOWER": fn_lower,
        "TRIM": fn_trim,
        "LEN": fn_len,
        "LEFT": fn_left,
        "RIGHT": fn_right,
        "MOD": fn_mod,
        "INT": fn_int,
        "CEIL": fn_ceil,
        "FLOOR": fn_floor,
        "TODAY": fn_today,
        "NOW": fn_now,
    }


FUNCTIONS = _build_functions()


def _format_result(val: Any) -> str:
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return f"{val:.6g}"
    return str(val)


def evaluate_cell(
    raw: str,
    grid: list[list[str]],
    visited: set[tuple[int, int]] | None = None,
) -> str:
    """Evaluate a raw cell string against `grid`. Non-formulas return as-is."""
    if not isinstance(raw, str) or not raw.startswith("="):
        return "" if raw is None else str(raw)

    expr = raw[1:].strip()
    if not expr:
        return ""

    visited = visited or set()

    def get_val(r: int, c: int) -> Any:
        if (r, c) in visited:
            raise ValueError("Circular reference")
        if r < 0 or c < 0 or r >= len(grid) or c >= len(grid[r]):
            return 0.0
        cell_raw = grid[r][c]
        if isinstance(cell_raw, str) and cell_raw.startswith("="):
            res = evaluate_cell(cell_raw, grid, visited | {(r, c)})
            n = _to_number(res)
            return n if n is not None else res
        n = _to_number(cell_raw)
        return n if n is not None else cell_raw

    # Replace ranges A1:B3 with internal tokens __RANGE_0__
    range_values: dict[str, list[Any]] = {}

    def _replace_range(match: re.Match[str]) -> str:
        coords = expand_range(match.group(1), match.group(2), match.group(3), match.group(4))
        key = f"__RANGE_{len(range_values)}__"
        range_values[key] = [get_val(r, c) for r, c in coords]
        return key

    cell_values: dict[str, Any] = {}

    def _replace_cell(match: re.Match[str]) -> str:
        end = match.end()
        if end < len(expr) and expr[end] == "(":
            return match.group(0)
        letters, row_s = match.group(1), match.group(2)
        if letters.upper() in FUNCTIONS:
            return match.group(0)
        r = int(row_s) - 1
        c = col_letters_to_index(letters)
        key = f"__CELL_{len(cell_values)}__"
        cell_values[key] = get_val(r, c)
        return key

    try:
        expr = RANGE_RE.sub(_replace_range, expr)
        expr = CELL_REF_RE.sub(_replace_cell, expr)
        # Support Excel ^ for exponentiation
        expr = expr.replace("^", "**")

        env: dict[str, Any] = {}
        env.update(range_values)
        env.update(cell_values)

        def _eval_node(node: ast.AST) -> Any:
            if isinstance(node, ast.Expression):
                return _eval_node(node.body)
            if isinstance(node, ast.Constant):
                return node.value
            if isinstance(node, ast.Name):
                if node.id in env:
                    return env[node.id]
                upper = node.id.upper()
                if upper == "TRUE":
                    return True
                if upper == "FALSE":
                    return False
                if upper == "PI":
                    return math.pi
                raise ValueError(f"Unknown name: {node.id}")
            if isinstance(node, ast.BinOp):
                op = _SAFE_BINOPS.get(type(node.op))
                if op is None:
                    raise ValueError("Unsupported operator")
                return op(_eval_node(node.left), _eval_node(node.right))
            if isinstance(node, ast.UnaryOp):
                op = _SAFE_UNARYOPS.get(type(node.op))
                if op is None:
                    raise ValueError("Unsupported unary operator")
                return op(_eval_node(node.operand))
            if isinstance(node, ast.Compare):
                left = _eval_node(node.left)
                for cmp_op, comparator in zip(node.ops, node.comparators):
                    fn = _SAFE_CMPOPS.get(type(cmp_op))
                    if fn is None:
                        raise ValueError("Unsupported comparison")
                    right = _eval_node(comparator)
                    if not fn(left, right):
                        return False
                    left = right
                return True
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name):
                    raise ValueError("Unsupported call")
                fn_name = node.func.id.upper()
                fn = FUNCTIONS.get(fn_name)
                if fn is None:
                    raise ValueError(f"Unknown function: {fn_name}")
                args = [_eval_node(a) for a in node.args]
                return fn(*args)
            raise ValueError(f"Unsupported expression: {type(node).__name__}")

        tree = ast.parse(expr, mode="eval")
        result = _eval_node(tree)
        return _format_result(result)
    except ZeroDivisionError:
        return "#DIV/0!"
    except Exception:
        return "#ERR!"
