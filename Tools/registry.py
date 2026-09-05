"""
ToolRegistry for managing, discovering, and executing tools in the Gangline harness.
"""

from typing import Dict, List, Optional, Any
from .base import BaseTool, ToolResult, FunctionTool


class ToolRegistry:
    """Registry that holds available tools and provides lookup and execution."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool_item: Any) -> BaseTool:
        """Register a BaseTool or callable into the registry."""
        if isinstance(tool_item, BaseTool):
            tool_obj = tool_item
        elif callable(tool_item):
            tool_obj = FunctionTool(tool_item)
        else:
            raise TypeError(f"Cannot register object of type {type(tool_item)} as a tool.")

        self._tools[tool_obj.name] = tool_obj
        return tool_obj

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Return JSON schemas of all registered tools for LLM tool calling."""
        return [t.get_schema() for t in self._tools.values()]

    def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name with the provided arguments."""
        tool_obj = self._tools.get(name)
        if not tool_obj:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{name}' is not registered. Available tools: {list(self._tools.keys())}"
            )
        return tool_obj.execute(**kwargs)

    def describe_tools_text(self) -> str:
        """Provide a clean text description of all available tools for prompt injection."""
        if not self._tools:
            return "No tools available."

        lines = ["Available Tools:"]
        for tool_obj in self._tools.values():
            params = tool_obj.parameters.get("properties", {})
            param_desc = ", ".join(f"{p}: {v.get('type', 'any')}" for p, v in params.items())
            lines.append(f"- {tool_obj.name}({param_desc}): {tool_obj.description}")
        return "\n".join(lines)


# Global default registry
default_registry = ToolRegistry()
