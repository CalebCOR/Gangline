"""
Wikipedia search tool for the Gangline agent harness.
Fetches concise article summaries and facts from Wikipedia.
If direct lookup fails, it automatically finds and queries the closest
relevant Wikipedia article using MediaWiki's relevance and suggestion search engine.
"""

from typing import Dict, Any, Optional, List
import urllib.parse
import urllib.request
import json
from .base import BaseTool, ToolResult


class WikiSearchTool(BaseTool):
    """Tool that searches Wikipedia for a topic and returns a text summary."""

    name: str = "wiki_search"
    description: str = (
        "Search Wikipedia for a topic, person, event, or concept and return a factual summary. "
        "If an exact match is not found, it automatically retrieves the closest relevant article."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The topic, title, or search term to look up on Wikipedia."
            }
        },
        "required": ["topic"]
    }

    _HEADERS = {
        "User-Agent": "GanglineAgentHarness/1.0 (https://github.com/CalebCOR/Gangline; contact@gangline.dev)"
    }

    # Offline backup summaries for core demonstration / offline environments
    _OFFLINE_KNOWLEDGE = {
        "odin": "In Norse mythology, Odin is the All-Father, god of wisdom, poetry, death, divination, and magic. He is accompanied by his ravens Huginn (thought) and Muninn (memory), who fly across Midgard to bring him tidings.",
        "huginn and muninn": "Huginn and Muninn are a pair of ravens that fly all over the world, Midgard, and bring information to the god Odin. In the Poetic Edda, Odin expresses fear that Huginn may not return, but worries more for Muninn.",
        "valhalla": "In Norse mythology, Valhalla (Old Norse: Valholl 'hall of the slain') is an enormous, majestic hall located in Asgard, ruled over by the god Odin.",
        "ragnarok": "In Norse mythology, Ragnarok is a series of catastrophic events, including a great battle, resulting in the death of many gods (including Odin, Thor, and Loki), natural disasters, and the rebirth of a new, fertile world.",
        "mjolnir": "In Norse mythology, Mjolnir is the hammer of Thor, the Norse god associated with thunder. Mjolnir is depicted in Norse mythology as one of the most fearsome and powerful weapons in existence, capable of leveling mountains.",
        "artificial intelligence": "Artificial intelligence (AI) is the intelligence of machines or software, as opposed to the intelligence of living beings, primarily of humans. It is also the field of study in computer science that develops and studies intelligent machines."
    }

    def _fetch_summary(self, title: str) -> Optional[Dict[str, Any]]:
        """Fetch REST API summary for a specific article title."""
        encoded_title = urllib.parse.quote(title.strip().replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"

        try:
            req = urllib.request.Request(url, headers=self._HEADERS)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("extract"):
                        return data
        except Exception:
            pass
        return None

    def _search_closest_titles(self, query: str, limit: int = 5) -> List[str]:
        """Search Wikipedia's full-text and suggestion index for closest matching titles."""
        candidate_titles: List[str] = []

        # 1. MediaWiki full-text search API with suggestion detection
        try:
            search_url = (
                f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch="
                f"{urllib.parse.quote(query)}&srinfo=suggestion&utf8=&format=json&srlimit={limit}"
            )
            req = urllib.request.Request(search_url, headers=self._HEADERS)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    query_data = data.get("query", {})

                    # If MediaWiki suggested a spelling or closer semantic query, check it first
                    suggestion = query_data.get("searchinfo", {}).get("suggestion")
                    if suggestion:
                        try:
                            s_url = (
                                f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch="
                                f"{urllib.parse.quote(suggestion)}&utf8=&format=json&srlimit={limit}"
                            )
                            with urllib.request.urlopen(urllib.request.Request(s_url, headers=self._HEADERS), timeout=5) as s_resp:
                                if s_resp.status == 200:
                                    s_data = json.loads(s_resp.read().decode("utf-8"))
                                    for item in s_data.get("query", {}).get("search", []):
                                        title = item.get("title")
                                        if title and title not in candidate_titles:
                                            candidate_titles.append(title)
                        except Exception:
                            pass

                    # Add search results from the original query
                    for item in query_data.get("search", []):
                        title = item.get("title")
                        if title and title not in candidate_titles:
                            candidate_titles.append(title)
        except Exception:
            pass

        # 2. OpenSearch prefix/autocomplete API as secondary candidate source
        try:
            opensearch_url = (
                f"https://en.wikipedia.org/w/api.php?action=opensearch&search="
                f"{urllib.parse.quote(query)}&limit={limit}&namespace=0&format=json"
            )
            req = urllib.request.Request(opensearch_url, headers=self._HEADERS)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if len(data) > 1 and isinstance(data[1], list):
                        for title in data[1]:
                            if title and title not in candidate_titles:
                                candidate_titles.append(title)
        except Exception:
            pass

        return candidate_titles

    def execute(self, topic: str, **kwargs) -> ToolResult:
        topic_clean = topic.strip()
        if not topic_clean:
            return ToolResult(success=False, output="Empty topic provided.", error="No topic specified.")

        # 1. First attempt: Direct lookup by exact topic name
        summary_data = self._fetch_summary(topic_clean)
        if summary_data:
            title = summary_data.get("title", topic_clean)
            extract = summary_data.get("extract", "")
            description = summary_data.get("description", "")
            page_url = summary_data.get("content_urls", {}).get("desktop", {}).get("page", "")

            formatted = f"Wikipedia: {title}\n"
            if description:
                formatted += f"Description: {description}\n"
            formatted += f"Summary:\n{extract}\n"
            if page_url:
                formatted += f"Source URL: {page_url}"

            return ToolResult(
                success=True,
                output=formatted.strip(),
                metadata={"title": title, "url": page_url, "match": "exact"}
            )

        # 2. Second attempt: Find and try the closest relevant articles
        closest_titles = self._search_closest_titles(topic_clean, limit=5)

        for candidate in closest_titles:
            candidate_summary = self._fetch_summary(candidate)
            if candidate_summary:
                title = candidate_summary.get("title", candidate)
                extract = candidate_summary.get("extract", "")
                description = candidate_summary.get("description", "")
                page_url = candidate_summary.get("content_urls", {}).get("desktop", {}).get("page", "")

                formatted = (
                    f"Wikipedia: {title} (Closest relevant match for '{topic_clean}')\n"
                )
                if description:
                    formatted += f"Description: {description}\n"
                formatted += f"Summary:\n{extract}\n"
                if page_url:
                    formatted += f"Source URL: {page_url}\n"
                formatted += f"Note: Direct article for '{topic_clean}' was not found; automatically retrieved the closest relevant article '{title}'."

                return ToolResult(
                    success=True,
                    output=formatted.strip(),
                    metadata={
                        "title": title,
                        "url": page_url,
                        "query": topic_clean,
                        "match": "closest_relevant"
                    }
                )

        # 3. Third attempt: Try individual primary keywords if topic is a multi-word phrase
        words = [w for w in topic_clean.split() if len(w) > 3]
        if len(words) > 1:
            for word in words:
                keyword_candidates = self._search_closest_titles(word, limit=3)
                for candidate in keyword_candidates:
                    candidate_summary = self._fetch_summary(candidate)
                    if candidate_summary:
                        title = candidate_summary.get("title", candidate)
                        extract = candidate_summary.get("extract", "")
                        description = candidate_summary.get("description", "")
                        page_url = candidate_summary.get("content_urls", {}).get("desktop", {}).get("page", "")

                        formatted = (
                            f"Wikipedia: {title} (Closest relevant match for '{topic_clean}')\n"
                        )
                        if description:
                            formatted += f"Description: {description}\n"
                        formatted += f"Summary:\n{extract}\n"
                        if page_url:
                            formatted += f"Source URL: {page_url}\n"
                        formatted += f"Note: Retrieved via closest keyword match '{word}'."

                        return ToolResult(
                            success=True,
                            output=formatted.strip(),
                            metadata={
                                "title": title,
                                "url": page_url,
                                "query": topic_clean,
                                "match": "keyword_fallback"
                            }
                        )

        # 4. Fourth attempt: Offline fallback for known topics or resilient simulation
        lower_topic = topic_clean.lower()
        for key, snippet in self._OFFLINE_KNOWLEDGE.items():
            if key in lower_topic or any(w in key for w in lower_topic.split()):
                return ToolResult(
                    success=True,
                    output=f"Wikipedia (Offline Knowledge): {key.title()} (Closest match for '{topic_clean}')\nSummary:\n{snippet}",
                    metadata={"topic": key, "match": "offline_closest"}
                )

        # 5. Final fallback if all attempts fail
        candidate_note = f" (Attempted matches: {', '.join(closest_titles[:3])})" if closest_titles else ""
        return ToolResult(
            success=False,
            output=f"Could not find a Wikipedia page or relevant match for '{topic_clean}'{candidate_note}.",
            error="No relevant Wikipedia article found"
        )
