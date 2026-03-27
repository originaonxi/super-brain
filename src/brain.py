#!/usr/bin/env python3
"""
brain.py — Python SDK for Super Brain

Programmatic access to the Mem0 super brain.
Use from any Python script, agent, or notebook.

Usage:
    from brain import SuperBrain
    brain = SuperBrain()
    brain.push("learned something new", category="research")
    results = brain.search("what projects use Kafka?")
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional


class SuperBrain:
    """Python interface to the Mem0 super brain."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: str = "anmol-super-brain",
        base_url: str = "https://api.mem0.ai/v1",
    ):
        self.api_key = api_key or os.environ.get("MEM0_API_KEY")
        if not self.api_key:
            raise ValueError("MEM0_API_KEY not set. Export it or pass api_key parameter.")
        self.user_id = user_id
        self.base_url = base_url

    def _request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        """Make an API request to Mem0."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise RuntimeError(f"Mem0 API error {e.code}: {error_body}")

    def push(self, content: str, category: str = "auto", source: str = "python-sdk") -> dict:
        """Push a memory to the super brain."""
        return self._request("POST", "/memories/", {
            "messages": [{"role": "user", "content": content}],
            "user_id": self.user_id,
            "metadata": {
                "category": category,
                "owner": "anmol",
                "source": source,
                "timestamp": datetime.now().isoformat(),
            },
        })

    def search(self, query: str, top_k: int = 5) -> list:
        """Search the super brain. Returns list of memories with scores."""
        result = self._request("POST", "/memories/search/", {
            "query": query,
            "user_id": self.user_id,
            "top_k": top_k,
        })
        return result if isinstance(result, list) else result.get("results", [])

    def get_all(self) -> list:
        """Get all memories in the super brain."""
        result = self._request("GET", f"/memories/?user_id={self.user_id}")
        return result if isinstance(result, list) else result.get("results", [])

    def stats(self) -> dict:
        """Get brain statistics."""
        memories = self.get_all()
        categories = {}
        for m in memories:
            cat = m.get("metadata", {}).get("category", "uncategorized")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_memories": len(memories),
            "categories": categories,
            "user_id": self.user_id,
            "oldest": min((m["created_at"] for m in memories), default=None),
            "newest": max((m["updated_at"] for m in memories), default=None),
        }

    def delete(self, memory_id: str) -> dict:
        """Delete a specific memory."""
        return self._request("DELETE", f"/memories/{memory_id}/")

    def update(self, memory_id: str, content: str) -> dict:
        """Update an existing memory."""
        return self._request("PUT", f"/memories/{memory_id}/", {
            "messages": [{"role": "user", "content": content}],
        })


def main():
    """CLI interface for brain.py"""
    import sys

    brain = SuperBrain()

    if len(sys.argv) < 2:
        print("Usage: brain.py <command> [args]")
        print("Commands: search, push, stats, list")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "search":
        query = " ".join(sys.argv[2:])
        results = brain.search(query)
        for i, r in enumerate(results, 1):
            score = r.get("score", "?")
            cat = r.get("metadata", {}).get("category", "?")
            print(f"  {i}. [{cat}] (score: {score})")
            print(f"     {r['memory']}")
            print()

    elif cmd == "push":
        content = " ".join(sys.argv[2:])
        result = brain.push(content)
        print(f"Pushed: {result}")

    elif cmd == "stats":
        s = brain.stats()
        print(f"Total memories: {s['total_memories']}")
        print(f"Categories:")
        for cat, count in sorted(s["categories"].items()):
            print(f"  {cat}: {count}")

    elif cmd == "list":
        memories = brain.get_all()
        for m in memories:
            cat = m.get("metadata", {}).get("category", "?")
            print(f"[{cat}] {m['memory'][:100]}")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
