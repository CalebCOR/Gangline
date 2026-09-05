"""
LLM abstraction layer supporting Ollama, Google GenAI, OpenAI, and Mock simulation.
Allows switching backends via environment variables or configuration.
"""

import os
import json
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv("env/.env")
    load_dotenv(".env")
except Exception:
    pass


class BaseLLMProvider(ABC):
    """Abstract LLM provider."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text from prompt and optional system persona."""
        pass


class OllamaProvider(BaseLLMProvider):
    """Provider for local Ollama instances."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma3:1b", timeout: int = 45):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        import requests
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
        except Exception as e:
            raise ConnectionError(f"Ollama request to {url} failed: {e}")


class GoogleGenAIProvider(BaseLLMProvider):
    """Provider using google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize google-genai client: {e}")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        contents = prompt
        config = {}
        if system_prompt:
            config["system_instruction"] = system_prompt
        resp = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config
        )
        return resp.text.strip() if resp.text else ""


class OpenAIProvider(BaseLLMProvider):
    """Provider compatible with OpenAI, LM Studio, vLLM, LocalAI, etc."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini"
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "dummy_key")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.model = model

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        import requests
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
        }
        resp = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=45)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


class MockSimulationProvider(BaseLLMProvider):
    """
    Intelligent simulated character provider for offline testing, demos, and dry runs.
    Accurately demonstrates agent quirks, tool calling syntax, and conditional commentary triggers.
    """

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        system = system_prompt or ""
        agent_name = "Agent"
        for name in ["Huginn", "Muninn", "Freki"]:
            if f"CHARACTER IDENTITY: {name.upper()}" in system or f"You are {name}" in system or f"You are {name}" in prompt:
                agent_name = name
                break

        # Case 1: Peer commentary evaluation
        if "YOUR PEER COMMENTARY CONDITIONS:" in prompt:
            lead_match = re.search(r"LEAD AGENT \((.*?)\)'S RESPONSE:\s*\"\"\"(.*?)\"\"\"", prompt, re.DOTALL)
            lead_name = lead_match.group(1) if lead_match else "Lead"
            lead_text = lead_match.group(2) if lead_match else ""

            if agent_name == "Muninn":
                # Muninn comments if lead was verbose, had poetic fluff, or lacked hard actionable facts
                if any(w in lead_text.lower() for w in ["lore", "wonder", "poetry", "realm", "yggdrasil", "soul"]):
                    return "Hear this, All-Father: The poet speaks in clouds while reality marches on. " \
                           "History is forged not in golden verses, but in iron ledgers, supplies, and verified pacts. " \
                           "Record the dates and strategic consequences; leave the bardic singing for feast halls."
                return "PASS"

            elif agent_name == "Huginn":
                # Huginn comments if lead was too cold, cynical, or omitted historical soul
                if any(w in lead_text.lower() for w in ["ledger", "iron", "strategic", "tactical", "risk", "cold"]):
                    return "Ah, brother Muninn weighs the world in lead, yet forgets what makes men bleed to defend it! " \
                           "Look beneath the stone of the chronicle: every treaty was penned by living hands, " \
                           "and every empire was born from an unyielding dream. Do not let numbers obscure the living song of Midgard."
                return "PASS"

            elif agent_name == "Freki":
                # Freki comments if agents are overthinking, philosophizing, or missing immediate action
                if len(lead_text) > 250 or "wisdom" in lead_text.lower() or "consider" in lead_text.lower():
                    return "Hah! The ravens perch high and caw while the prey walks free! " \
                           "Enough talk of treaties and songs. What are our orders? Point us to the target and let our teeth do the deciding!"
                return "PASS"

            return "PASS"

        # Case 2: Tool interpretation synthesis
        if "YOUR TOOL INTERPRETATION RULES:" in prompt and "RAW TOOL OUTPUT:" in prompt:
            tool_output_match = re.search(r"RAW TOOL OUTPUT:\s*\"\"\"(.*?)\"\"\"", prompt, re.DOTALL)
            raw = tool_output_match.group(1) if tool_output_match else ""

            if agent_name == "Huginn":
                return f"By Odin's gaze, the knowledge reveals deep currents of history!\n\n" \
                       f"Upon soaring through the archives, I discovered:\n{raw}\n\n" \
                       f"Behold how the threads of fate weave through this! It is more than mere ink; " \
                       f"it is a testament to how knowledge shapes the destinies of mortals and gods alike across the ages."

            elif agent_name == "Muninn":
                return f"The record has been retrieved and verified.\n\n" \
                       f"Core Intel:\n{raw}\n\n" \
                       f"Strategic assessment: The facts are established. Proceed with tactical awareness, and commit these details to permanent memory."

            elif agent_name == "Freki":
                return f"The trail is fresh! Here is the meat of it:\n\n{raw}\n\n" \
                       f"Bottom line: We have our quarry's location and traits. No more sniffing around—time to strike and put this knowledge to use!"

            return f"Processed tool output:\n{raw}"

        # Case 3: Initial lead generation - deciding whether to call a tool
        prompt_lower = prompt.lower()
        if any(term in prompt_lower for term in ["who is", "what is", "tell me about", "look up", "search", "wiki", "history", "information", "ragnarok", "odin", "valhalla", "ai"]):
            # Extract candidate topic
            topic = "Odin"
            for candidate in ["valhalla", "ragnarok", "huginn and muninn", "odin", "artificial intelligence"]:
                if candidate in prompt_lower:
                    topic = candidate
                    break
            else:
                m = re.search(r"(?:about|search for|look up|who is|what is)\s+([a-zA-Z0-9_\s]+)", prompt_lower)
                if m:
                    topic = m.group(1).strip().rstrip("?.!")

            return f"I shall dispatch my sight across the realms to gather verified knowledge.\n" \
                   f"```tool_call\n" \
                   f"{{\"tool\": \"wiki_search\", \"args\": {{\"topic\": \"{topic}\"}}}}\n" \
                   f"```"

        # Case 4: Standard lead response without tools
        if agent_name == "Huginn":
            return "From the heights of Hlidskjalf, I have watched this question unfold across the ages. " \
                   "Every thought begins with a spark of wonder. Let us explore the deeper patterns that connect this to the cosmos!"
        elif agent_name == "Muninn":
            return "Observation recorded. The matter is straightforward: maintain discipline, assess the operational factors, and execute methodically."
        elif agent_name == "Freki":
            return "Clear the way! We do not sit and ponder when there is territory to claim. Let's attack the problem head-on."

        return "Objective received. Proceeding with focused resolution."


def get_llm_provider(
    provider_name: Optional[str] = None,
    allow_mock_fallback: bool = True
) -> BaseLLMProvider:
    """
    Factory to retrieve an LLM provider based on environment configuration.
    Defaults to Ollama if set, or Mock simulation if no live server responds.
    """
    name = (provider_name or os.environ.get("LLM_PROVIDER", "ollama")).lower()

    if name == "mock" or name == "simulation":
        return MockSimulationProvider()

    if name == "gemini" or name == "google":
        api_key = os.environ.get("GEMINI_API_KEY")
        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        if api_key:
            try:
                return GoogleGenAIProvider(api_key=api_key, model=model)
            except Exception as e:
                if not allow_mock_fallback:
                    raise
                print(f"[Warning] Failed to start Google GenAI provider: {e}. Falling back to Mock.")
        elif not allow_mock_fallback:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")

    if name == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            return OpenAIProvider(api_key=api_key)
        elif not allow_mock_fallback:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")

    if name == "ollama":
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.environ.get("OLLAMA_MODEL", "gemma3:1b")
        ollama = OllamaProvider(base_url=base_url, model=model)
        # Check connectivity if fallback allowed
        if allow_mock_fallback:
            try:
                import requests
                r = requests.get(f"{base_url}/api/tags", timeout=1.5)
                if r.status_code == 200:
                    return ollama
            except Exception:
                # Local Ollama server is offline; fall back cleanly to Mock
                return MockSimulationProvider()
        return ollama

    # Fallback to MockSimulationProvider
    return MockSimulationProvider()
