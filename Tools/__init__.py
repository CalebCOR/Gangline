"""
Tools package for Gangline Multi-Agent Harness.
"""

from .base import BaseTool, ToolResult, FunctionTool, tool
from .registry import ToolRegistry, default_registry
from .wiki import WikiSearchTool
from .calculator import calculate

# Register default built-in tools
default_registry.register(WikiSearchTool())
default_registry.register(calculate)

__all__ = [
    "BaseTool",
    "ToolResult",
    "FunctionTool",
    "tool",
    "ToolRegistry",
    "default_registry",
    "WikiSearchTool",
    "calculate",
]
