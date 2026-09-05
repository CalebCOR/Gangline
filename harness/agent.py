"""
Agent profile parsing and prompt construction for the Gangline harness.
Loads agent characters from Markdown (.md) files and structures their persona,
quirks, tool interpretation habits, and commentary triggers.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, Optional, List


AGENT_COLORS = {
    "Huginn": "bright_cyan",
    "Muninn": "bright_yellow",
    "Freki": "bright_red",
    "Geri": "bright_magenta",
    "Default": "bright_white",
}


@dataclass
class AgentProfile:
    """Represents an agent character loaded from an Agent_name.md file."""
    name: str
    role_backstory: str
    quirks: str
    tool_guidelines: str
    commentary_conditions: str
    raw_text: str
    color: str = "cyan"
    metadata: Dict[str, str] = field(default_factory=dict)

    def get_system_persona(self, system_memory: str = "") -> str:
        """Combine global system memory with the agent's character definition."""
        sections = []
        if system_memory.strip():
            sections.append(f"### GLOBAL LAWS & MEMORY\n{system_memory.strip()}")

        sections.append(f"### CHARACTER IDENTITY: {self.name.upper()}\n{self.role_backstory.strip()}")

        if self.quirks.strip():
            sections.append(f"### QUIRKS, TENDENCIES & SPEECH\n{self.quirks.strip()}")

        if self.tool_guidelines.strip():
            sections.append(f"### HOW YOU INTERPRET TOOLS\n{self.tool_guidelines.strip()}")

        return "\n\n".join(sections)

    def build_lead_prompt(self, objective: str, tool_descriptions: str, conversation_history: str = "") -> str:
        """Construct the prompt for when this agent leads the objective."""
        prompt = f"""You are leading the response for the following objective.

OBJECTIVE:
{objective}

{tool_descriptions}

INSTRUCTIONS FOR THE LEAD AGENT:
1. Stay strictly in character as {self.name}. Embody your voice, quirks, and mannerisms.
2. If you need factual information or external execution to solve this objective, you may invoke a tool using this exact JSON block on a line by itself:
```tool_call
{{"tool": "<tool_name>", "args": {{"<arg_key>": "<arg_value>"}}}}
```
3. If no tool is needed or after reviewing tool output, deliver your complete, high-quality, in-character response to resolve the objective.
"""
        if conversation_history:
            prompt = f"PREVIOUS CONVERSATION:\n{conversation_history}\n\n" + prompt
        return prompt

    def build_tool_interpretation_prompt(self, tool_name: str, tool_args: dict, raw_output: str) -> str:
        """Instruct agent to interpret tool output using their unique lens."""
        return f"""You called the tool '{tool_name}' with arguments {tool_args}.
RAW TOOL OUTPUT:
\"\"\"
{raw_output}
\"\"\"

YOUR TOOL INTERPRETATION RULES:
{self.tool_guidelines}

Task: Synthesize this raw output through your personal character lens and incorporate it into your final solution for the objective. Embody your quirks and speech patterns."""

    def build_commentary_prompt(
        self,
        objective: str,
        lead_name: str,
        lead_response: str,
        tool_activity: str = ""
    ) -> str:
        """Construct the evaluation prompt for peer review."""
        tools_str = f"\nTOOL ACTIVITY:\n{tool_activity}\n" if tool_activity else ""
        return f"""You are {self.name}. Your peer {lead_name} was the designated lead for this objective and just gave their response.

OBJECTIVE:
{objective}
{tools_str}
LEAD AGENT ({lead_name})'S RESPONSE:
\"\"\"
{lead_response}
\"\"\"

YOUR PEER COMMENTARY CONDITIONS:
{self.commentary_conditions}

CRITICAL RULES:
- Carefully evaluate whether the lead's response triggers any of your specific commentary conditions.
- If and ONLY IF your conditions are met, provide your in-character critique, perspective, warning, or additional counsel.
- If your conditions are NOT met (for example, the lead's response is already sound or does not provoke your triggers), you MUST reply with exactly the single word:
PASS
- Do not apologize or explain why you are passing. If passing, write only 'PASS'."""


def parse_agent_markdown(filepath: str) -> AgentProfile:
    """Parse an Agent_name.md markdown file into an AgentProfile."""
    name = os.path.splitext(os.path.basename(filepath))[0]
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract sections using header matching
    def extract_section(headers: List[str], text: str) -> str:
        pattern = r"(?:^|\n)##?\s+(?:" + "|".join(re.escape(h) for h in headers) + r")[^\n]*\n(.*?)(?=(?:\n##?\s+)|$)"
        match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    role = extract_section(["Role & Backstory", "Role", "Backstory", "Identity"], content)
    quirks = extract_section(["Quirks & Tendencies", "Quirks", "Tendencies", "Personality"], content)
    tool_rules = extract_section(["Tool Interpretation Guidelines", "Tool Interpretation", "Tools"], content)
    comment_triggers = extract_section(["Peer Commentary Conditions", "Commentary Conditions", "Triggers", "Comments"], content)

    # Fallback if unsectioned text
    if not role and not quirks:
        role = content.strip()

    color = AGENT_COLORS.get(name, AGENT_COLORS.get("Default", "cyan"))

    return AgentProfile(
        name=name,
        role_backstory=role or f"You are {name}.",
        quirks=quirks or "Distinct personal quirks.",
        tool_guidelines=tool_rules or "Analyze tools objectively.",
        commentary_conditions=comment_triggers or "Comment when you have valuable insight.",
        raw_text=content,
        color=color
    )


def load_all_agents(agents_dir: str) -> Dict[str, AgentProfile]:
    """Load all agent markdown files from the Agents directory."""
    if not os.path.exists(agents_dir):
        os.makedirs(agents_dir, exist_ok=True)

    agents = {}
    for fname in os.listdir(agents_dir):
        if fname.endswith(".md"):
            path = os.path.join(agents_dir, fname)
            profile = parse_agent_markdown(path)
            agents[profile.name] = profile

    return agents
