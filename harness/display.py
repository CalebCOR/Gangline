"""
Console display and rendering utilities for the Gangline agent harness.
Uses Rich to produce sleek character badges, tool execution cards,
and multi-agent discussion transcripts with full word-wrapping.
"""

import sys
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text

# Configure UTF-8 for Windows consoles if supported
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure soft_wrap=False so all words wrap nicely inside terminals and panels without truncation
console = Console(highlight=False, soft_wrap=False)

AGENT_STYLES = {
    "Huginn": {"color": "cyan", "title": "[Huginn - Thought & Lore]", "border": "bright_cyan"},
    "Muninn": {"color": "yellow", "title": "[Muninn - Memory & Strategy]", "border": "bright_yellow"},
    "Freki": {"color": "red", "title": "[Freki - Instinct & Action]", "border": "bright_red"},
    "System": {"color": "magenta", "title": "[System Harness]", "border": "magenta"},
    "Tool": {"color": "green", "title": "[Tool Execution]", "border": "green"},
}


def get_agent_style(agent_name: str) -> Dict[str, str]:
    return AGENT_STYLES.get(agent_name, {
        "color": "white",
        "title": f"[{agent_name}]",
        "border": "bright_white"
    })


def print_banner():
    """Print the Gangline harness welcome banner."""
    banner_text = Text()
    banner_text.append("=============================================================\n", style="dim")
    banner_text.append("             * GANGLINE MULTI-AGENT HARNESS *\n", style="bold bright_cyan")
    banner_text.append("       Character-Driven Multi-Agent Collaborative System       \n", style="italic")
    banner_text.append("=============================================================", style="dim")
    console.print(Panel(banner_text, border_style="bright_blue", expand=True))


def print_agent_roster(agents: Dict[str, Any]):
    """Display the loaded agent roster table with word-wrapping."""
    table = Table(title="Active Agents in Roster", border_style="dim", expand=True)
    table.add_column("Name", style="bold", no_wrap=True, width=12)
    table.add_column("Character Role", style="italic")
    table.add_column("Key Tendencies / Quirks", style="dim")

    for name, agent in agents.items():
        style_info = get_agent_style(name)
        role_text = agent.role_backstory.strip().replace("\n", " ")
        quirk_text = agent.quirks.strip().replace("\n", " ")
        table.add_row(f"[{style_info['color']}]{name}[/]", role_text, quirk_text)

    console.print(table)


def print_objective_start(objective: str, lead_agent: str, mention_detected: bool):
    """Print the objective kickoff announcement."""
    style_info = get_agent_style(lead_agent)
    reason = "Targeted via Query Mention" if mention_detected else "Designated Lead"
    console.print()
    console.print(Panel(
        f"[bold]Objective:[/bold] {objective}\n[bold]Lead Assigned:[/bold] [{style_info['color']}]{lead_agent}[/] ([dim]{reason}[/dim])",
        title="[Objective Kickoff]",
        border_style="bright_magenta",
        expand=True
    ))


def print_tool_call(agent_name: str, tool_name: str, tool_args: Dict[str, Any]):
    """Render a tool call invocation card."""
    arg_strs = [f"{k}={repr(v)}" for k, v in tool_args.items()]
    console.print(Panel(
        f"[bold cyan]{agent_name}[/] invoked [bold green]{tool_name}[/]([yellow]{', '.join(arg_strs)}[/yellow])",
        title="[Tool Call Dispatched]",
        border_style="green",
        padding=(0, 1),
        expand=True
    ))


def print_tool_result(tool_name: str, output: str, success: bool = True):
    """Render the tool output card with full text wrapping."""
    status_tag = "[OK]" if success else "[ERROR]"
    console.print(Panel(
        Text(output.strip(), style="dim"),
        title=f"{status_tag} Tool Result: {tool_name}",
        border_style="dim green" if success else "red",
        padding=(0, 1),
        expand=True
    ))


def print_lead_response(lead_name: str, response: str):
    """Render the lead agent's synthesized response with full text and word wrapping."""
    style_info = get_agent_style(lead_name)
    console.print()
    console.print(Panel(
        Markdown(response.strip()),
        title=f"{style_info['title']} [bold]LEAD RESPONSE[/bold]",
        border_style=style_info["border"],
        padding=(1, 2),
        expand=True
    ))


def print_peer_commentary(agent_name: str, comment: str):
    """Render a peer agent's conditional commentary with full text and word wrapping."""
    style_info = get_agent_style(agent_name)
    console.print(Panel(
        Markdown(comment.strip()),
        title=f"{style_info['title']} [bold italic]PEER COMMENTARY (Condition Triggered)[/bold italic]",
        border_style=style_info["border"],
        padding=(1, 2),
        expand=True
    ))


def print_peer_pass(agent_name: str):
    """Render when a peer evaluates triggers and decides to pass."""
    style_info = get_agent_style(agent_name)
    console.print(f"[{style_info['color']}]- {agent_name}:[/] [dim]Conditions not triggered -- passed silently.[/dim]")
