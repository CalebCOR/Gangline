"""
A simple math expression calculator tool.
Demonstrates how easy it is to add new tools using either BaseTool or @tool.
"""

import math
from .base import tool, ToolResult


# Safe evaluation dictionary
_SAFE_MATH = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log,
    "exp": math.exp,
    "pow": math.pow,
    "pi": math.pi,
    "e": math.e,
    "abs": abs,
    "round": round,
}


@tool(name="calculator", description="Safely evaluate a mathematical expression like '2 + 2', 'sqrt(16)', or '15 * 8'.")
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    clean_expr = expression.strip()
    # Basic check for safety
    disallowed = ["__", "import", "eval", "exec", "open", "os", "sys", "subprocess"]
    for word in disallowed:
        if word in clean_expr:
            return f"Error: Expression contains forbidden keyword '{word}'."

    try:
        # Evaluate within limited mathematical scope
        result = eval(clean_expr, {"__builtins__": {}}, _SAFE_MATH)
        return f"{clean_expr} = {result}"
    except Exception as e:
        return f"Calculation error for '{clean_expr}': {str(e)}"
