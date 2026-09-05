"""
Base classes and utilities for the Gangline Tool system.
Provides BaseTool, ToolResult, and a @tool decorator for rapid tool creation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, get_type_hints
import inspect
import json


@dataclass
class ToolResult:
    """Represents the outcome of a tool execution."""
    success: bool
    output: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "metadata": self.metadata,
            "error": self.error,
        }

    def __str__(self) -> str:
        return self.output if self.success else f"Error: {self.error or self.output}"


class BaseTool(ABC):
    """Abstract base class for all tools."""

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given keyword arguments."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return the JSON schema representation for LLM function calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters or {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }


def _python_type_to_json_type(py_type: Any) -> str:
    """Map common Python types to JSON Schema types."""
    if py_type in (str, Optional[str]):
        return "string"
    elif py_type in (int, Optional[int]):
        return "integer"
    elif py_type in (float, Optional[float]):
        return "number"
    elif py_type in (bool, Optional[bool]):
        return "boolean"
    elif py_type in (list, Optional[list]):
        return "array"
    elif py_type in (dict, Optional[dict]):
        return "object"
    return "string"


class FunctionTool(BaseTool):
    """A tool wrapper around an arbitrary Python function."""

    def __init__(self, func: Callable, name: Optional[str] = None, description: Optional[str] = None):
        self.func = func
        self.name = name or func.__name__
        self.description = description or (inspect.getdoc(func) or f"Execute {self.name}").strip()
        self.parameters = self._infer_parameters(func)

    def _infer_parameters(self, func: Callable) -> Dict[str, Any]:
        sig = inspect.signature(func)
        try:
            type_hints = get_type_hints(func)
        except Exception:
            type_hints = {}

        properties: Dict[str, Any] = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue
            py_type = type_hints.get(param_name, str)
            json_type = _python_type_to_json_type(py_type)
            param_meta: Dict[str, Any] = {"type": json_type}

            if param.default is inspect.Parameter.empty:
                required.append(param_name)
            else:
                param_meta["default"] = param.default

            properties[param_name] = param_meta

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    def execute(self, **kwargs) -> ToolResult:
        try:
            res = self.func(**kwargs)
            if isinstance(res, ToolResult):
                return res
            elif isinstance(res, (dict, list)):
                return ToolResult(success=True, output=json.dumps(res, indent=2))
            return ToolResult(success=True, output=str(res))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Tool execution failed: {str(e)}")


def tool(name_or_func: Any = None, *, name: Optional[str] = None, description: Optional[str] = None):
    """
    Decorator to convert a Python function into a BaseTool instance.
    Usage:
        @tool
        def my_tool(topic: str) -> str:
            '''Search for a topic.'''
            ...

        @tool(name="custom_name", description="Custom desc")
        def another_tool(x: int) -> int:
            ...
    """
    if callable(name_or_func):
        return FunctionTool(name_or_func)

    def decorator(func: Callable) -> FunctionTool:
        tool_name = name or (name_or_func if isinstance(name_or_func, str) else None)
        return FunctionTool(func, name=tool_name, description=description)

    return decorator
