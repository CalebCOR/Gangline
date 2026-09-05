"""
Gangline Multi-Agent Harness Package.
"""

from .agent import AgentProfile, load_all_agents, parse_agent_markdown
from .llm import (
    BaseLLMProvider,
    OllamaProvider,
    GoogleGenAIProvider,
    OpenAIProvider,
    MockSimulationProvider,
    get_llm_provider
)
from .orchestrator import MultiAgentHarness, ObjectiveResult, ToolExecutionRecord
from .display import console, print_banner, print_agent_roster

__all__ = [
    "AgentProfile",
    "load_all_agents",
    "parse_agent_markdown",
    "BaseLLMProvider",
    "OllamaProvider",
    "GoogleGenAIProvider",
    "OpenAIProvider",
    "MockSimulationProvider",
    "get_llm_provider",
    "MultiAgentHarness",
    "ObjectiveResult",
    "ToolExecutionRecord",
    "console",
    "print_banner",
    "print_agent_roster",
]
