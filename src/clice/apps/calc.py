"""Clice Calc — Scientific Calculator & Programmer Base Converter."""

from __future__ import annotations

import ast
import math
import operator
from typing import Any, Callable

from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical
from textual.widgets import Button, Input, Static

_OPS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_FUNCS: dict[str, Callable[..., Any]] = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log10,
    "ln": math.log,
    "abs": abs,
    "round": round,
}


def safe_calc(expr: str) -> float:
    expr = expr.replace("^", "**").strip()
    tree = ast.parse(expr, mode="eval")

    def _eval(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id.lower() == "pi":
                return math.pi
            if node.id.lower() == "e":
                return math.e
            raise ValueError(f"Unknown symbol: {node.id}")
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                return -_eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +_eval(node.operand)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fn = _FUNCS.get(node.func.id.lower())
            if fn is None:
                raise ValueError(f"Unknown function: {node.func.id}")
            return fn(*[_eval(a) for a in node.args])
        raise ValueError("Unsupported expression")

    return float(_eval(tree))


class CalcApp(Vertical):
    """GUI-like Scientific Calculator with Programmer HEX/DEC/OCT/BIN converter."""

    def __init__(self) -> None:
        super().__init__()
        self.expr = ""
        self.history: list[str] = []

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #06b6d4]🧮 Clice Calculator[/b #06b6d4]", classes="app-title")
            yield Static("[dim]Scientific • History • Programmer Base Converter[/dim]")

        yield Static("0", id="calc-display")

        with Horizontal(classes="toolbar"):
            yield Input(placeholder="Type expression (e.g. sqrt(144) + 2^8)...", id="calc-input")
            yield Button("=", variant="primary", id="calc-eval")
            yield Button("Clear", variant="warning", id="calc-clear")

        with Horizontal():
            with Grid(id="calc-keypad"):
                keys = [
                    "7", "8", "9", "/", "sqrt(",
                    "4", "5", "6", "*", "^",
                    "1", "2", "3", "-", "(",
                    "0", ".", "pi", "+", ")",
                ]
                for k in keys:
                    safe_id = k.replace(".", "dot").replace("/", "div").replace("*", "mul").replace("-", "sub").replace("+", "add").replace("(", "lp").replace(")", "rp").replace("^", "pow")
                    yield Button(k, id=f"ckey-{safe_id}", name=k)

            with Vertical(classes="metric-box"):
                yield Static("[b]🔢 Programmer Base Converter[/b]")
                yield Input(value="255", placeholder="Integer (e.g. 255, 0xff, 0b1010)", id="base-input")
                yield Button("Convert", variant="success", id="base-convert")
                yield Static("DEC: 255\nHEX: 0xFF\nOCT: 0o377\nBIN: 0b11111111", id="base-output")
                yield Static("\n[b]📜 History[/b]\n[dim](empty)[/dim]", id="calc-history")

    def _evaluate(self, expression: str) -> None:
        display = self.query_one("#calc-display", Static)
        try:
            res = safe_calc(expression)
            res_str = str(int(res)) if res.is_integer() else f"{res:.10g}"
            display.update(f"[b #06b6d4]{res_str}[/b #06b6d4]")
            self.history.insert(0, f"{expression} = {res_str}")
            self.history = self.history[:8]
            self.query_one("#calc-history", Static).update(
                "\n[b]📜 History[/b]\n" + "\n".join(self.history)
            )
            self.expr = res_str
            self.query_one("#calc-input", Input).value = res_str
        except Exception as exc:
            display.update(f"[red]Error: {exc}[/red]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "calc-input":
            self._evaluate(event.value)
        elif event.input.id == "base-input":
            self._convert_base(event.value)

    def _convert_base(self, raw: str) -> None:
        out = self.query_one("#base-output", Static)
        try:
            val = int(raw.strip(), 0)
            out.update(
                f"DEC: {val}\nHEX: {hex(val).upper().replace('0X', '0x')}\n"
                f"OCT: {oct(val)}\nBIN: {bin(val)}"
            )
        except Exception as exc:
            out.update(f"[red]Invalid integer: {exc}[/red]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "calc-eval":
            self._evaluate(self.query_one("#calc-input", Input).value)
        elif bid == "calc-clear":
            self.expr = ""
            self.query_one("#calc-input", Input).value = ""
            self.query_one("#calc-display", Static).update("0")
        elif bid == "base-convert":
            self._convert_base(self.query_one("#base-input", Input).value)
        elif bid.startswith("ckey-"):
            inp = self.query_one("#calc-input", Input)
            inp.value = inp.value + (event.button.name or "")
            self.query_one("#calc-display", Static).update(inp.value or "0")
