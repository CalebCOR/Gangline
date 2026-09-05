"""
Multi-agent collaboration orchestrator for the Gangline harness.
Manages agent mentions, lead selection, tool invocation loops,
character-specific tool output interpretation, and conditional peer commentary.
"""

import os
import re
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from .agent import AgentProfile, load_all_agents
from .llm import BaseLLMProvider, get_llm_provider
from .display import (
    print_objective_start,
    print_tool_call,
    print_tool_result,
    print_lead_response,
    print_peer_commentary,
    print_peer_pass
)
from Tools.registry import ToolRegistry, default_registry


@dataclass
class ToolExecutionRecord:
    tool_name: str
    args: Dict[str, Any]
    output: str
    success: bool


@dataclass
class ObjectiveResult:
    """The complete outcome of a collaborative multi-agent run."""
    objective: str
    lead_agent: str
    lead_response: str
    tool_executions: List[ToolExecutionRecord] = field(default_factory=list)
    peer_comments: Dict[str, str] = field(default_factory=dict)
    peers_passed: List[str] = field(default_factory=list)

    def summary_text(self) -> str:
        lines = [
            f"=== OBJECTIVE RESOLUTION ===",
            f"Objective: {self.objective}",
            f"Lead Agent: {self.lead_agent}",
            f"\nLead Response:\n{self.lead_response}\n"
        ]
        if self.tool_executions:
            lines.append("Tools Used:")
            for t in self.tool_executions:
                lines.append(f"- {t.tool_name}({t.args}) -> Success: {t.success}")
        if self.peer_comments:
            lines.append("\nPeer Commentary:")
            for agent, comment in self.peer_comments.items():
                lines.append(f"[{agent}]: {comment}")
        if self.peers_passed:
            lines.append(f"\nPeers Passed (Conditions Not Met): {', '.join(self.peers_passed)}")
        return "\n".join(lines)


class MultiAgentHarness:
    """The central multi-agent coordination harness."""

    def __init__(
        self,
        agents_dir: str = "Agents",
        system_memory_file: Optional[str] = "Memory/System.md",
        tool_registry: Optional[ToolRegistry] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        verbose: bool = True
    ):
        self.agents_dir = agents_dir
        self.agents: Dict[str, AgentProfile] = load_all_agents(agents_dir)
        self.system_memory = self._load_system_memory(system_memory_file)
        self.tools = tool_registry or default_registry
        self.llm = llm_provider or get_llm_provider()
        self.verbose = verbose
        self._conversation_history: List[str] = []

    def reload_agents(self):
        """Reload agent markdown profiles from disk."""
        self.agents = load_all_agents(self.agents_dir)

    def _load_system_memory(self, filepath: Optional[str]) -> str:
        if filepath and os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""

    def detect_mentioned_agent(self, query: str) -> Optional[str]:
        """
        Detect if an agent is referred to inside the query by name.
        Supports:
        - Exact name mention: 'Huginn, what do you think...'
        - At-mentions: '@Muninn'
        - Targeted directives: 'Ask Freki to ...'
        """
        for name in self.agents.keys():
            # Check @Mention
            if f"@{name.lower()}" in query.lower():
                return name
            # Check boundary match for name
            pattern = rf"\b{re.escape(name)}\b"
            if re.search(pattern, query, re.IGNORECASE):
                return name
        return None

    def select_lead_agent(self, query: str) -> tuple[str, bool]:
        """
        Choose the lead agent. If an agent is mentioned in the query,
        they lead the response. Otherwise, choose the best-suited or default agent.
        """
        mentioned = self.detect_mentioned_agent(query)
        if mentioned:
            return mentioned, True

        # If not mentioned, pick first available or round-robin
        agent_names = list(self.agents.keys())
        if not agent_names:
            raise RuntimeError("No agents found in Agents directory!")

        # Default fallback: pick first agent or suit to query
        lead = agent_names[0]
        return lead, False

    def _extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract ```tool_call { ... } ``` blocks from LLM response."""
        pattern = r"```tool_call\s*(\{.*?\})\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                if "tool" in data:
                    return data
            except json.JSONDecodeError:
                pass
        return None

    def execute_objective(self, objective: str, designated_lead: Optional[str] = None) -> ObjectiveResult:
        """
        Execute an objective collaboratively:
        1. Designate lead agent (via mention, explicit argument, or default).
        2. Lead agent analyzes objective, optionally calls tools, and interprets output in character.
        3. Peer agents evaluate commentary conditions; chime in if triggered, or pass silently.
        """
        self.reload_agents()

        if designated_lead and designated_lead in self.agents:
            lead_name = designated_lead
            mention_detected = True
        else:
            lead_name, mention_detected = self.select_lead_agent(objective)

        lead_agent = self.agents[lead_name]

        if self.verbose:
            print_objective_start(objective, lead_name, mention_detected)

        # 1. Prepare lead prompt
        system_persona = lead_agent.get_system_persona(self.system_memory)
        tool_desc = self.tools.describe_tools_text()
        history_text = "\n".join(self._conversation_history[-3:]) if self._conversation_history else ""
        lead_prompt = lead_agent.build_lead_prompt(objective, tool_desc, history_text)

        # Generate lead thought / initial response
        initial_lead_output = self.llm.generate(lead_prompt, system_prompt=system_persona)

        # 2. Check if a tool was requested
        tool_records: List[ToolExecutionRecord] = []
        tool_call_data = self._extract_tool_call(initial_lead_output)
        final_lead_response = initial_lead_output

        if tool_call_data:
            tool_name = tool_call_data.get("tool", "")
            tool_args = tool_call_data.get("args", {})

            if self.verbose:
                print_tool_call(lead_name, tool_name, tool_args)

            # Execute tool
            tool_result = self.tools.execute(tool_name, **tool_args)
            record = ToolExecutionRecord(
                tool_name=tool_name,
                args=tool_args,
                output=tool_result.output,
                success=tool_result.success
            )
            tool_records.append(record)

            if self.verbose:
                print_tool_result(tool_name, tool_result.output, tool_result.success)

            # Instruct lead agent to interpret the tool output through their personality lens
            interpret_prompt = lead_agent.build_tool_interpretation_prompt(
                tool_name=tool_name,
                tool_args=tool_args,
                raw_output=tool_result.output
            )
            final_lead_response = self.llm.generate(interpret_prompt, system_prompt=system_persona)
        else:
            # Clean any leftover markdown blocks if any
            final_lead_response = re.sub(r"```tool_call.*?```", "", final_lead_response, flags=re.DOTALL).strip()

        if self.verbose:
            print_lead_response(lead_name, final_lead_response)

        # 3. Peer Commentary Stage
        peer_comments: Dict[str, str] = {}
        peers_passed: List[str] = []

        tool_activity_summary = ""
        if tool_records:
            tool_activity_summary = "\n".join(
                f"- Used tool '{t.tool_name}' with args {t.args}. Result snippet: {t.output[:180]}..."
                for t in tool_records
            )

        # Iterate through peers
        for peer_name, peer_agent in self.agents.items():
            if peer_name == lead_name:
                continue

            peer_system = peer_agent.get_system_persona(self.system_memory)
            peer_prompt = peer_agent.build_commentary_prompt(
                objective=objective,
                lead_name=lead_name,
                lead_response=final_lead_response,
                tool_activity=tool_activity_summary
            )

            peer_response = self.llm.generate(peer_prompt, system_prompt=peer_system).strip()

            # Check if peer decided to PASS
            clean_check = peer_response.strip().upper()
            if clean_check == "PASS" or clean_check.startswith("PASS.") or not peer_response:
                peers_passed.append(peer_name)
                if self.verbose:
                    print_peer_pass(peer_name)
            else:
                peer_comments[peer_name] = peer_response
                if self.verbose:
                    print_peer_commentary(peer_name, peer_response)

        # Record conversation context
        self._conversation_history.append(f"User Objective: {objective}")
        self._conversation_history.append(f"{lead_name} (Lead): {final_lead_response}")
        for p_name, p_comment in peer_comments.items():
            self._conversation_history.append(f"{p_name} (Comment): {p_comment}")

        return ObjectiveResult(
            objective=objective,
            lead_agent=lead_name,
            lead_response=final_lead_response,
            tool_executions=tool_records,
            peer_comments=peer_comments,
            peers_passed=peers_passed
        )
