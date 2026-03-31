#!/usr/bin/env python3
"""
local_brain.py — Local memory layer using MemoryMesh

Works offline. No cloud. Runs on Mac Mini M4.
This is the local twin of the Mem0 cloud brain.

The hierarchy:
  memorymesh (local SQLite) → aonxi-memcollab (cross-agent) → Mem0 cloud (super-brain)

Usage:
    from local_brain import LocalBrain
    lb = LocalBrain()
    lb.remember("nova-gtm learned that healthcare leads convert 3x on Tuesdays")
    lb.recall("healthcare lead patterns")
    lb.sync_to_cloud()  # push local learnings to Mem0
"""

import sys
from pathlib import Path

# Try to import memorymesh
try:
    from memorymesh import MemoryMesh
except ImportError:
    # Fallback: add the local memorymesh path
    sys.path.insert(0, str(Path.home() / "memorymesh"))
    try:
        from memorymesh import MemoryMesh
    except ImportError:
        print("memorymesh not found. Install with: pip install memorymesh")
        print("Or ensure ~/memorymesh exists.")
        sys.exit(1)

from brain import SuperBrain


class LocalBrain:
    """Local-first memory that syncs to cloud when needed."""

    def __init__(self, namespace: str = "super-brain"):
        self.mesh = MemoryMesh(namespace=namespace)
        self._cloud = None

    @property
    def cloud(self):
        if self._cloud is None:
            try:
                self._cloud = SuperBrain()
            except ValueError:
                pass
        return self._cloud

    def remember(self, content: str, tags: list = None, source: str = "local") -> str:
        """Store a memory locally."""
        return self.mesh.remember(content, tags=tags or [], source=source)

    def recall(self, query: str, limit: int = 5) -> list:
        """Search local memory."""
        return self.mesh.recall(query, limit=limit)

    def context_for(self, query: str, limit: int = 5) -> str:
        """Get context string to inject into any LLM prompt."""
        return self.mesh.as_context(query, limit=limit)

    def remember_repo_state(self, repo_name: str, state: dict) -> str:
        """Store a repo's current state as a memory."""
        content = f"Repo {repo_name}: {state}"
        return self.remember(content, tags=["repo-state", repo_name], source="orchestrator")

    def sync_to_cloud(self, since_hours: int = 24) -> dict:
        """Push recent local memories to Mem0 cloud."""
        if not self.cloud:
            return {"error": "MEM0_API_KEY not set — cloud sync unavailable"}

        recent = self.mesh.recall("*", limit=50)
        pushed = 0
        for mem in recent:
            try:
                content = mem.get("content", "")
                tags = mem.get("tags", [])
                category = tags[0] if tags else "local-sync"
                self.cloud.push(content, category=category, source="local-brain")
                pushed += 1
            except Exception:
                pass

        return {"synced": pushed, "total_found": len(recent)}

    def hybrid_search(self, query: str, top_k: int = 5) -> list:
        """Search both local and cloud, merge results."""
        local_results = self.recall(query, limit=top_k)

        cloud_results = []
        if self.cloud:
            try:
                cloud_results = self.cloud.search(query, top_k=top_k)
            except Exception:
                pass

        # Merge: local first, then cloud (deduplicated)
        seen_content = set()
        merged = []

        for r in local_results:
            content = r.get("content", "")[:100]
            if content not in seen_content:
                seen_content.add(content)
                merged.append({"source": "local", **r})

        for r in cloud_results:
            content = r.get("memory", "")[:100]
            if content not in seen_content:
                seen_content.add(content)
                merged.append({"source": "cloud", **r})

        return merged[:top_k]


if __name__ == "__main__":
    lb = LocalBrain()

    if len(sys.argv) < 2:
        print("LocalBrain — Offline-first memory")
        print("  remember <text>    Store a memory locally")
        print("  recall <query>     Search local memories")
        print("  sync               Push to Mem0 cloud")
        print("  hybrid <query>     Search local + cloud")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "remember":
        text = " ".join(sys.argv[2:])
        mid = lb.remember(text)
        print(f"  Stored: {mid}")

    elif cmd == "recall":
        query = " ".join(sys.argv[2:])
        results = lb.recall(query)
        for r in results:
            print(f"  [{r.get('source', '?')}] {r.get('content', '')[:100]}")

    elif cmd == "sync":
        result = lb.sync_to_cloud()
        print(f"  Synced {result.get('synced', 0)} memories to cloud")

    elif cmd == "hybrid":
        query = " ".join(sys.argv[2:])
        results = lb.hybrid_search(query)
        for r in results:
            src = r.get("source", "?")
            content = r.get("content", r.get("memory", ""))[:100]
            print(f"  [{src}] {content}")
