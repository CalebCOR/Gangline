# Gangline Multi-Agent Collaboration Harness

A character-driven multi-agent AI framework where distinct agent personalities collaborate to solve objectives, dynamically dispatch tools, interpret data through unique narrative lenses, and provide conditional peer review.

---

## Key Features

1. **Character-Centric Agents (`Agents/*.md`)**:
   - Each agent is defined in a standard Markdown file containing their role, backstory, quirks, tendencies, tool interpretation rules, and peer commentary triggers.
   - Built-in characters include:
     - **Huginn** (*Thought & Lore*): Poetic, verbose, fascinated by history and symbolism.
     - **Muninn** (*Memory & Strategy*): Terse, disciplined royal advisor who checks tactical risks and hard facts.
     - **Freki** (*Instinct & Action*): Direct, impatient warrior wolf who demands immediate, kinetic action.

2. **Query Mentions & Dynamic Leadership**:
   - Refer to agents directly in your query by name (`@Huginn`, `Muninn, analyze this`, `Ask Freki`) to designate that agent as the team lead.
   - If no agent is explicitly mentioned, the harness designates the best-suited agent.

3. **Character-Specific Tool Interpretation**:
   - When tools are executed, raw outputs are fed back to the lead agent through their specific *Tool Interpretation Guidelines*.
   - A historian sees folklore and origins; a strategist filters for risks and dates; a warrior looks for immediate leverage and weapons.

4. **Conditional Peer Commentary**:
   - After the lead agent delivers their solution, peers inspect the objective, tool executions, and response against their *Peer Commentary Conditions*.
   - If conditions fire, the peer chimes in with in-character advice or critiques.
   - If conditions are not met, the peer replies `PASS` and remains silent.

5. **Extensible Tool Framework**:
   - Built-in `wiki_search` tool: Queries Wikipedia REST API with offline fallbacks.
   - Built-in `calculator` tool: Evaluates mathematical expressions safely.
   - Define new tools in seconds using the `@tool` decorator or `BaseTool` class.

6. **Flexible Model Providers**:
   - Configurable via `env/.env`:
     - **Google Gemini**: Uses `google-genai` with `GEMINI_API_KEY` and `GEMINI_MODEL`.
     - **Ollama**: Connects to a local Ollama instance (`gemma3:1b`, `llama3`, etc.).
     - **OpenAI-compatible**: Connects to OpenAI, LM Studio, vLLM, or LocalAI.
     - **Mock Simulation**: Built-in zero-dependency simulation provider for offline demos and testing.

---

## Directory Layout

```
Gangline/
├── Agents/                  # Character definition markdown files
│   ├── Huginn.md            # Thought & Lore
│   ├── Muninn.md            # Memory & Strategy
│   └── Freki.md             # Instinct & Action
├── Tools/                   # Extensible Tool System
│   ├── __init__.py          # Default exports and global registry
│   ├── base.py              # BaseTool, ToolResult, @tool decorator
│   ├── registry.py          # ToolRegistry class
│   ├── wiki.py              # Wikipedia search tool
│   └── calculator.py        # Safe math evaluation tool
├── Memory/                  # Long-term shared instructions and memory
│   └── System.md            # Shared principles across all agents
├── harness/                 # Core harness logic
│   ├── agent.py             # Markdown parser and prompt construction
│   ├── llm.py               # Provider layer (Gemini, Ollama, OpenAI, Mock)
│   ├── orchestrator.py      # MultiAgentHarness execution loop
│   └── display.py           # Rich terminal UI & styling
├── Examples/
│   └── demo_harness.py      # Comprehensive demonstration script
├── env/
│   └── .env                 # Environment variables and API keys
├── main.py                  # Interactive CLI REPL
└── requirements.txt         # Dependencies
```

---

## Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Your LLM in `env/.env`
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
*(Or set `LLM_PROVIDER=ollama` for local Ollama, or `LLM_PROVIDER=mock` for offline testing).*

### 3. Run the Demonstration
```bash
python Examples/demo_harness.py
```

### 4. Start the Interactive Chat
```bash
python main.py
```

Inside the interactive console:
- `@Huginn search Wikipedia for Ragnarok and tell us what it means`
- `Muninn, what are the primary threats of artificial intelligence?`
- `Freki, plan a raid on the frost giants`
- Commands: `/agents`, `/tools`, `/reload`, `/clear`, `/exit`

---

## Creating New Agents

Add a new Markdown file in `Agents/<AgentName>.md`:

```markdown
# AgentName

## Role & Backstory
Who your character is, their history, and their perspective on the world.

## Quirks & Tendencies
- Speaking style, mannerisms, and biases.
- Recurring phrases or worldview.

## Tool Interpretation Guidelines
How this character interprets data returned from external tools (e.g. what they notice vs ignore).

## Peer Commentary Conditions
Conditions under which this agent chimes in on other agents' work.
If conditions are not met, the agent must output ONLY:
PASS
```

Reload profiles at runtime with `/reload` or call `harness.reload_agents()`.

---

## Creating New Tools

Use the `@tool` decorator anywhere in your code:

```python
from Tools import tool, default_registry

@tool(name="weather", description="Get weather conditions for a realm or city.")
def get_weather(location: str) -> str:
    # Tool logic here
    return f"Weather in {location}: Clear skies, 22°C"

# Register the tool
default_registry.register(get_weather)
```
