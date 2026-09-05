"""
Main interactive CLI entry point for the Gangline Multi-Agent Harness.
Allows users to pose objectives, mention specific agents to lead, invoke tools,
and watch character-driven collaboration and conditional peer review unfold in real time.
"""

import sys
import os

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv("env/.env")
load_dotenv(".env")

from harness import (
    MultiAgentHarness,
    print_banner,
    print_agent_roster,
    console
)
from Tools import default_registry


def interactive_loop():
    print_banner()

    console.print("[dim]Initializing Gangline Multi-Agent Harness...[/dim]")
    try:
        harness = MultiAgentHarness(
            agents_dir="Agents",
            system_memory_file="Memory/System.md",
            verbose=True
        )
    except Exception as e:
        console.print(f"[bold red]Failed to initialize harness:[/bold red] {e}")
        return

    print_agent_roster(harness.agents)

    console.print("\n[bold cyan]How to interact with the team:[/bold cyan]")
    console.print("  - [green]Target an agent:[/green] Mention their name (e.g. '@Huginn', 'Muninn, analyze this', 'Ask Freki')")
    console.print("  - [green]General objective:[/green] Type any objective and the harness will designate a leader.")
    console.print("  - [green]Commands:[/green] '/agents' (view profiles), '/tools' (view tools), '/reload' (reload .md files), '/exit'")
    console.print("-" * 65)

    while True:
        try:
            user_input = console.input("\n[bold bright_green]Objective / Query > [/bold bright_green]").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("/exit", "/quit", "exit", "quit"):
            break

        elif cmd == "/agents":
            print_agent_roster(harness.agents)
            continue

        elif cmd == "/tools":
            console.print("\n[bold green]Registered Tools in Harness:[/bold green]")
            for t in default_registry.list_tools():
                console.print(f"  - [bold yellow]{t.name}[/bold yellow]: {t.description}")
            continue

        elif cmd == "/reload":
            harness.reload_agents()
            console.print("[green]Agent character profiles reloaded from Agents/ directory![/green]")
            print_agent_roster(harness.agents)
            continue

        elif cmd == "/clear":
            os.system("cls" if os.name == "nt" else "clear")
            print_banner()
            continue

        # Execute objective collaboratively
        try:
            harness.execute_objective(user_input)
        except Exception as e:
            console.print(f"[bold red]Execution error:[/bold red] {e}")

    console.print("\n[bold cyan]Till we meet again across the nine realms.[/bold cyan]")


if __name__ == "__main__":
    interactive_loop()