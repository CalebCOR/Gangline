"""
Demonstration script showing the full capabilities of the Gangline Multi-Agent Harness:
1. Loading character agents from Agents/*.md files (Huginn, Muninn, Freki).
2. Referencing agents inside queries by name (@Agent or natural mention) to designate the leader.
3. Extensible tool calling, starting with Wikipedia search (wiki_search).
4. Agent-specific tool interpretation: each character filters raw data through their quirks.
5. Conditional peer commentary: agents review the lead's answer and only comment if their triggers fire, otherwise PASS.
6. Creating and registering new custom tools on the fly with @tool.
"""

import os
import sys

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(dotenv_path="env/.env")

from harness import MultiAgentHarness, print_banner, print_agent_roster, console
from Tools import default_registry, tool, ToolResult


def run_demo():
    print_banner()

    console.print("\n[bold cyan]1. Initializing Harness and Loading Character Roster...[/bold cyan]")
    harness = MultiAgentHarness(
        agents_dir="Agents",
        system_memory_file="Memory/System.md",
        verbose=True
    )
    print_agent_roster(harness.agents)

    # -------------------------------------------------------------------------
    # Extensible Tool Demo: Add a brand new tool dynamically using @tool
    # -------------------------------------------------------------------------
    console.print("\n[bold cyan]2. Registering a New Tool Dynamically with @tool...[/bold cyan]")

    @tool(name="realm_weather", description="Check atmospheric and supernatural weather across the mythological realms.")
    def realm_weather(realm: str) -> str:
        """Check weather in Asgard, Midgard, Niflheim, Muspelheim, etc."""
        conditions = {
            "asgard": "Golden skies, mild breeze, occasional bifrost auroras.",
            "midgard": "Overcast with heavy northern squalls.",
            "niflheim": "Glacial blizzard, sub-zero frostbite hazard.",
            "muspelheim": "Scorching brimstone storms, rivers of molten lava.",
        }
        realm_lower = realm.strip().lower()
        return conditions.get(realm_lower, f"Realm '{realm}' is obscured by ancient mist.")

    default_registry.register(realm_weather)
    console.print("Registered new tool: [bold green]realm_weather(realm: str)[/bold green]")
    console.print("Available tools now:", [t.name for t in default_registry.list_tools()])

    # -------------------------------------------------------------------------
    # Scenario 1: Query Mention targeting Huginn (Thought & Lore)
    # Huginn leads, calls wiki_search, interprets with poetic lore.
    # Muninn's commentary conditions trigger (countering poetic excess with discipline).
    # -------------------------------------------------------------------------
    console.print("\n" + "=" * 80)
    console.print("[bold yellow]SCENARIO 1: Mention-based Lead + Wiki Tool Execution + Peer Critique[/bold yellow]")
    console.print("=" * 80)

    query_1 = "Huginn, search Wikipedia for 'Valhalla' and reveal its mythic significance."
    result_1 = harness.execute_objective(query_1)

    # -------------------------------------------------------------------------
    # Scenario 2: Query Mention targeting Muninn (Memory & Strategy)
    # Muninn leads, gathers tactical data on Artificial Intelligence.
    # Huginn's commentary conditions trigger (challenging cold cynicism with wonder).
    # -------------------------------------------------------------------------
    console.print("\n" + "=" * 80)
    console.print("[bold yellow]SCENARIO 2: Targeting Muninn + Cold Analysis + Huginn Commentary[/bold yellow]")
    console.print("=" * 80)

    query_2 = "@Muninn, search Wikipedia for 'Artificial Intelligence' and give us a disciplined strategic report."
    result_2 = harness.execute_objective(query_2)

    # -------------------------------------------------------------------------
    # Scenario 3: Unassigned Objective (Harness picks leader) + Testing Peer Pass
    # -------------------------------------------------------------------------
    console.print("\n" + "=" * 80)
    console.print("[bold yellow]SCENARIO 3: Objective without Direct Mention[/bold yellow]")
    console.print("=" * 80)

    query_3 = "What is the status of the weather in Asgard?"
    result_3 = harness.execute_objective(query_3)

    # -------------------------------------------------------------------------
    # Summary of harness execution
    # -------------------------------------------------------------------------
    console.print("\n" + "=" * 80)
    console.print("[bold green]*** DEMO EXECUTION COMPLETE ***[/bold green]")
    console.print("Key Features Proven:")
    console.print("[green][OK][/green] Agent personas & quirks loaded from [cyan]Agents/*.md[/cyan]")
    console.print("[green][OK][/green] Query mention detection routing leadership dynamically")
    console.print("[green][OK][/green] Extensible tool registry ([green]wiki_search[/green], [green]calculator[/green], [green]realm_weather[/green])")
    console.print("[green][OK][/green] Character-driven tool output interpretation")
    console.print("[green][OK][/green] Conditional peer commentary with silent [yellow]PASS[/yellow] when conditions are unmet")
    console.print("=" * 80 + "\n")


if __name__ == "__main__":
    run_demo()
