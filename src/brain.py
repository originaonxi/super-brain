#!/usr/bin/env python3
"""
brain.py — Super Brain V2: The Orchestrator

The central nervous system for the entire Aonxi ecosystem.
V1 stored memories. V2 understands relationships, detects patterns,
and orchestrates cross-repo improvements.

Usage:
    from brain import SuperBrain
    brain = SuperBrain()

    # V1 — Memory
    brain.push("learned something new", category="research")
    results = brain.search("what projects use Kafka?")

    # V2 — Orchestration
    registry = brain.load_registry()
    graph = brain.dependency_graph()
    health = brain.health_check("aros-agent")
    patterns = brain.detect_patterns()
    improvements = brain.suggest_improvements("nova-gtm")
"""

import os
import sys
import json
import glob
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


BRAIN_ROOT = Path(__file__).parent.parent
REPOS_YAML = BRAIN_ROOT / "config" / "repos.yaml"
HOME = Path.home()


def _load_yaml_simple(path: str) -> dict:
    """Minimal YAML parser for our repos.yaml format. No PyYAML dependency."""
    repos = {}
    current_repo = None
    current_key = None

    with open(path) as f:
        for line in f:
            stripped = line.rstrip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(line.lstrip())

            if indent == 0 and stripped.endswith(":"):
                current_repo = stripped[:-1]
                repos[current_repo] = {}
                current_key = None
                continue

            if indent >= 2 and current_repo and ":" in stripped:
                key, _, val = stripped.strip().partition(":")
                key = key.strip()
                val = val.strip()

                if val.startswith("[") and val.endswith("]"):
                    inner = val[1:-1]
                    if inner:
                        items = [v.strip().strip('"').strip("'") for v in inner.split(",")]
                        repos[current_repo][key] = items
                    else:
                        repos[current_repo][key] = []
                elif val.startswith('"') and val.endswith('"'):
                    repos[current_repo][key] = val[1:-1]
                elif val.startswith("'") and val.endswith("'"):
                    repos[current_repo][key] = val[1:-1]
                else:
                    repos[current_repo][key] = val

    return repos


class SuperBrain:
    """Python interface to the Mem0 super brain + V2 orchestration layer."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: str = "anmol-super-brain",
        base_url: str = "https://api.mem0.ai/v1",
    ):
        self.api_key = api_key or os.environ.get("MEM0_API_KEY")
        self.user_id = user_id
        self.base_url = base_url
        self._registry = None

    def _require_api_key(self):
        if not self.api_key:
            raise ValueError("MEM0_API_KEY not set. Export it or pass api_key parameter.")

    # ── V1: Memory Layer ─────────────────────────────────────────────────

    def _request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        self._require_api_key()
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
        result = self._request("POST", "/memories/search/", {
            "query": query,
            "user_id": self.user_id,
            "top_k": top_k,
        })
        return result if isinstance(result, list) else result.get("results", [])

    def get_all(self) -> list:
        result = self._request("GET", f"/memories/?user_id={self.user_id}")
        return result if isinstance(result, list) else result.get("results", [])

    def stats(self) -> dict:
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
        return self._request("DELETE", f"/memories/{memory_id}/")

    def update(self, memory_id: str, content: str) -> dict:
        return self._request("PUT", f"/memories/{memory_id}/", {
            "messages": [{"role": "user", "content": content}],
        })

    # ── V2: Registry & Dependency Graph ──────────────────────────────────

    def load_registry(self) -> dict:
        """Load the complete repo registry from repos.yaml."""
        if self._registry is None:
            self._registry = _load_yaml_simple(str(REPOS_YAML))
        return self._registry

    def get_repo(self, name: str) -> Optional[dict]:
        """Get a single repo's metadata."""
        registry = self.load_registry()
        return registry.get(name)

    def repos_by_category(self, category: str) -> dict:
        """Get all repos in a category."""
        registry = self.load_registry()
        return {k: v for k, v in registry.items() if v.get("category") == category}

    def dependency_graph(self) -> dict:
        """Build the full dependency graph. Returns {repo: {depends_on: [], depended_by: []}}."""
        registry = self.load_registry()
        graph = {}
        for name, meta in registry.items():
            graph[name] = {
                "depends_on": meta.get("depends_on", []),
                "depended_by": meta.get("depended_by", []),
                "category": meta.get("category", "unknown"),
                "priority": meta.get("priority", "medium"),
            }
        return graph

    def downstream_repos(self, repo_name: str) -> list:
        """Find all repos that depend on this one (direct + transitive)."""
        registry = self.load_registry()
        visited = set()
        queue = [repo_name]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            meta = registry.get(current, {})
            for dep in meta.get("depended_by", []):
                if dep != "*":
                    queue.append(dep)
        visited.discard(repo_name)
        return list(visited)

    def upstream_repos(self, repo_name: str) -> list:
        """Find all repos this one depends on (direct + transitive)."""
        registry = self.load_registry()
        visited = set()
        queue = [repo_name]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            meta = registry.get(current, {})
            for dep in meta.get("depends_on", []):
                queue.append(dep)
        visited.discard(repo_name)
        return list(visited)

    # ── V2: Health Checks ────────────────────────────────────────────────

    def health_check(self, repo_name: str) -> dict:
        """Run health check on a single repo."""
        registry = self.load_registry()
        meta = registry.get(repo_name)
        if not meta:
            return {"repo": repo_name, "error": "not found in registry"}

        path = os.path.expanduser(meta.get("path", ""))
        health = {
            "repo": repo_name,
            "category": meta.get("category"),
            "priority": meta.get("priority"),
            "checks": {},
        }

        # Check 1: Directory exists
        health["checks"]["directory_exists"] = os.path.isdir(path)

        if not health["checks"]["directory_exists"]:
            health["checks"]["git_initialized"] = False
            health["overall"] = "missing"
            return health

        # Check 2: Git repo
        health["checks"]["git_initialized"] = os.path.isdir(os.path.join(path, ".git"))

        # Check 3: Has README
        health["checks"]["has_readme"] = os.path.isfile(os.path.join(path, "README.md"))

        # Check 4: Last commit age
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ci"],
                cwd=path, capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                last_commit = result.stdout.strip()
                health["checks"]["last_commit"] = last_commit
                # Parse date to check staleness
                date_str = last_commit.split(" ")[0]
                last_date = datetime.strptime(date_str, "%Y-%m-%d")
                days_old = (datetime.now() - last_date).days
                health["checks"]["days_since_commit"] = days_old
                health["checks"]["stale"] = days_old > 30
        except Exception:
            health["checks"]["last_commit"] = "unknown"

        # Check 5: Uncommitted changes
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=path, capture_output=True, text=True, timeout=5,
            )
            dirty_files = len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
            health["checks"]["uncommitted_changes"] = dirty_files
        except Exception:
            health["checks"]["uncommitted_changes"] = "unknown"

        # Check 6: Has tests
        has_tests = (
            os.path.isdir(os.path.join(path, "tests"))
            or os.path.isdir(os.path.join(path, "test"))
            or any(glob.glob(os.path.join(path, "**/test_*.py"), recursive=True))
        )
        health["checks"]["has_tests"] = has_tests

        # Check 7: Has .env (should not be committed)
        health["checks"]["has_env_file"] = os.path.isfile(os.path.join(path, ".env"))

        # Check 8: Has .gitignore
        health["checks"]["has_gitignore"] = os.path.isfile(os.path.join(path, ".gitignore"))

        # Overall score
        critical_pass = all([
            health["checks"]["directory_exists"],
            health["checks"]["git_initialized"],
            health["checks"]["has_readme"],
            health["checks"]["has_gitignore"],
        ])
        stale = health["checks"].get("stale", False)

        if critical_pass and not stale:
            health["overall"] = "healthy"
        elif critical_pass and stale:
            health["overall"] = "stale"
        else:
            health["overall"] = "needs-attention"

        return health

    def health_check_all(self) -> dict:
        """Run health checks on every repo in the registry."""
        registry = self.load_registry()
        results = {}
        for name in registry:
            results[name] = self.health_check(name)
        return results

    # ── V2: Pattern Detection ────────────────────────────────────────────

    def detect_patterns(self) -> dict:
        """Detect cross-repo patterns and shared code opportunities."""
        registry = self.load_registry()
        patterns = {
            "shared_kernel": [],
            "gtm_template_users": [],
            "daily_email_fleet": [],
            "research_to_product": [],
            "trust_safety_chain": [],
            "orphaned_repos": [],
            "high_impact_dependencies": [],
        }

        for name, meta in registry.items():
            cat = meta.get("category", "")
            deps = meta.get("depends_on", [])
            depby = meta.get("depended_by", [])

            # Kernel consumers
            kernel_deps = [d for d in deps if d.startswith("aonxi-")]
            if kernel_deps:
                patterns["shared_kernel"].append({
                    "repo": name, "uses": kernel_deps
                })

            # GTM engines
            if cat == "gtm-engine":
                patterns["gtm_template_users"].append(name)

            # Daily email fleet
            if meta.get("cron") or meta.get("role") == "daily-email":
                patterns["daily_email_fleet"].append({
                    "repo": name, "cron": meta.get("cron", "unknown")
                })

            # Orphaned (no deps and no one depends on them)
            if not deps and not depby and cat not in ("profile", "utility"):
                patterns["orphaned_repos"].append(name)

            # High-impact: many downstream dependents
            if len(depby) >= 3 and depby != ["*"]:
                patterns["high_impact_dependencies"].append({
                    "repo": name, "depended_by_count": len(depby), "depended_by": depby
                })

        # Research → Product pipeline detection
        research_repos = self.repos_by_category("research")
        agent_repos = self.repos_by_category("agent")
        for rname, rmeta in research_repos.items():
            for dep in rmeta.get("depended_by", []):
                if dep in agent_repos or dep in self.repos_by_category("aonxi-core"):
                    patterns["research_to_product"].append({
                        "research": rname, "feeds_into": dep
                    })

        return patterns

    # ── V2: Improvement Suggestions ──────────────────────────────────────

    def suggest_improvements(self, repo_name: str) -> list:
        """Generate improvement suggestions for a repo based on ecosystem context."""
        health = self.health_check(repo_name)
        meta = self.get_repo(repo_name)
        suggestions = []

        if not meta:
            return [{"type": "error", "message": f"{repo_name} not in registry"}]

        checks = health.get("checks", {})

        if not checks.get("has_readme"):
            suggestions.append({
                "type": "missing-readme",
                "priority": "high",
                "action": f"Create README.md for {repo_name}",
            })

        if not checks.get("has_gitignore"):
            suggestions.append({
                "type": "missing-gitignore",
                "priority": "high",
                "action": f"Add .gitignore to {repo_name}",
            })

        if not checks.get("has_tests"):
            suggestions.append({
                "type": "missing-tests",
                "priority": "medium",
                "action": f"Add tests/ directory to {repo_name}",
            })

        if checks.get("stale"):
            days = checks.get("days_since_commit", "?")
            suggestions.append({
                "type": "stale",
                "priority": "low",
                "action": f"{repo_name} has not been updated in {days} days",
            })

        if checks.get("has_env_file"):
            suggestions.append({
                "type": "security",
                "priority": "critical",
                "action": f"Ensure .env is in .gitignore for {repo_name}",
            })

        # Check if repo could benefit from kernel modules it doesn't use
        category = meta.get("category")
        current_deps = meta.get("depends_on", [])
        if category in ("agent", "gtm-engine") and "aonxi-memcollab" not in current_deps:
            suggestions.append({
                "type": "kernel-adoption",
                "priority": "medium",
                "action": f"{repo_name} could benefit from aonxi-memcollab for shared memory",
            })
        if category in ("agent", "gtm-engine") and "aonxi-safeguard" not in current_deps:
            suggestions.append({
                "type": "kernel-adoption",
                "priority": "medium",
                "action": f"{repo_name} could benefit from aonxi-safeguard for safety checks",
            })

        # Check if upstream deps are healthy
        for dep in current_deps:
            dep_health = self.health_check(dep)
            if dep_health.get("overall") in ("needs-attention", "missing"):
                suggestions.append({
                    "type": "upstream-unhealthy",
                    "priority": "high",
                    "action": f"Upstream dependency {dep} is {dep_health['overall']} — fix it first",
                })

        return suggestions

    # ── V2: Ecosystem Report ─────────────────────────────────────────────

    def ecosystem_report(self) -> dict:
        """Generate a full ecosystem health report."""
        registry = self.load_registry()
        health_all = self.health_check_all()
        patterns = self.detect_patterns()

        categories = {}
        for name, meta in registry.items():
            cat = meta.get("category", "unknown")
            categories.setdefault(cat, []).append(name)

        overall_health = {"healthy": 0, "stale": 0, "needs-attention": 0, "missing": 0}
        for name, h in health_all.items():
            status = h.get("overall", "unknown")
            overall_health[status] = overall_health.get(status, 0) + 1

        return {
            "timestamp": datetime.now().isoformat(),
            "total_repos": len(registry),
            "categories": {k: len(v) for k, v in categories.items()},
            "health_summary": overall_health,
            "patterns": {
                "kernel_consumers": len(patterns["shared_kernel"]),
                "gtm_engines": len(patterns["gtm_template_users"]),
                "daily_agents": len(patterns["daily_email_fleet"]),
                "research_to_product_links": len(patterns["research_to_product"]),
                "orphaned_repos": len(patterns["orphaned_repos"]),
            },
            "orphaned": patterns["orphaned_repos"],
            "high_impact": patterns["high_impact_dependencies"],
        }

    # ── V2: Cross-Repo Learning ──────────────────────────────────────────

    def learn_from_repo(self, repo_name: str) -> dict:
        """Extract learnings from a repo and push them to the brain."""
        meta = self.get_repo(repo_name)
        if not meta:
            return {"error": f"{repo_name} not in registry"}

        path = os.path.expanduser(meta.get("path", ""))
        learnings = []

        # Extract from recent git commits
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                cwd=path, capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                commits = result.stdout.strip()
                learning = f"{repo_name} recent activity:\n{commits}"
                learnings.append(learning)
        except Exception:
            pass

        # Push learnings to brain
        pushed = 0
        for l in learnings:
            try:
                self.push(l, category=meta.get("category", "auto"), source=f"learn-{repo_name}")
                pushed += 1
            except Exception as e:
                pass

        return {"repo": repo_name, "learnings_found": len(learnings), "pushed": pushed}

    def sync_all_to_brain(self) -> dict:
        """Sync learnings from every repo to the brain."""
        registry = self.load_registry()
        results = {}
        for name in registry:
            results[name] = self.learn_from_repo(name)
        return results


def main():
    """CLI interface for Super Brain V2."""
    brain = SuperBrain()

    if len(sys.argv) < 2:
        print("Super Brain V2 — The Orchestrator")
        print()
        print("Memory commands:")
        print("  search <query>       Search the brain")
        print("  push <text>          Push a memory")
        print("  stats                Brain statistics")
        print("  list                 List all memories")
        print()
        print("Orchestration commands:")
        print("  registry             Show all registered repos")
        print("  graph <repo>         Show dependency graph for a repo")
        print("  health <repo>        Health check a repo")
        print("  health-all           Health check every repo")
        print("  patterns             Detect cross-repo patterns")
        print("  suggest <repo>       Suggest improvements for a repo")
        print("  report               Full ecosystem report")
        print("  learn <repo>         Extract learnings from a repo")
        print("  sync-all             Sync all repos to brain")
        sys.exit(0)

    cmd = sys.argv[1]

    # ── Memory commands ──
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
        print("Categories:")
        for cat, count in sorted(s["categories"].items()):
            print(f"  {cat}: {count}")

    elif cmd == "list":
        memories = brain.get_all()
        for m in memories:
            cat = m.get("metadata", {}).get("category", "?")
            print(f"[{cat}] {m['memory'][:100]}")

    # ── Orchestration commands ──
    elif cmd == "registry":
        registry = brain.load_registry()
        categories = {}
        for name, meta in registry.items():
            cat = meta.get("category", "unknown")
            categories.setdefault(cat, []).append((name, meta))

        for cat, repos in sorted(categories.items()):
            print(f"\n{'=' * 60}")
            print(f"  {cat.upper()} ({len(repos)} repos)")
            print(f"{'=' * 60}")
            for name, meta in repos:
                status = meta.get("status", "?")
                priority = meta.get("priority", "?")
                purpose = meta.get("purpose", "")[:70]
                print(f"  [{priority:>8}] {name:<30} {purpose}")

    elif cmd == "graph":
        repo = sys.argv[2] if len(sys.argv) > 2 else None
        if not repo:
            print("Usage: brain.py graph <repo-name>")
            sys.exit(1)
        upstream = brain.upstream_repos(repo)
        downstream = brain.downstream_repos(repo)
        meta = brain.get_repo(repo)
        print(f"\n  {repo}")
        print(f"  Category: {meta.get('category', '?')}")
        print(f"  Purpose: {meta.get('purpose', '?')}")
        print(f"\n  Upstream (depends on):")
        for u in upstream:
            print(f"    <- {u}")
        if not upstream:
            print(f"    (none)")
        print(f"\n  Downstream (depended by):")
        for d in downstream:
            print(f"    -> {d}")
        if not downstream:
            print(f"    (none)")

    elif cmd == "health":
        repo = sys.argv[2] if len(sys.argv) > 2 else None
        if not repo:
            print("Usage: brain.py health <repo-name>")
            sys.exit(1)
        h = brain.health_check(repo)
        print(f"\n  {repo}: {h.get('overall', '?').upper()}")
        for k, v in h.get("checks", {}).items():
            icon = "pass" if v is True else ("FAIL" if v is False else str(v))
            print(f"    {k}: {icon}")

    elif cmd == "health-all":
        results = brain.health_check_all()
        summary = {"healthy": [], "stale": [], "needs-attention": [], "missing": []}
        for name, h in sorted(results.items()):
            status = h.get("overall", "unknown")
            summary.setdefault(status, []).append(name)

        for status in ["healthy", "stale", "needs-attention", "missing"]:
            repos = summary.get(status, [])
            if repos:
                print(f"\n  {status.upper()} ({len(repos)}):")
                for r in repos:
                    print(f"    {r}")

    elif cmd == "patterns":
        patterns = brain.detect_patterns()
        print("\n  ECOSYSTEM PATTERNS")
        print("  " + "=" * 50)

        print(f"\n  Kernel Consumers ({len(patterns['shared_kernel'])}):")
        for p in patterns["shared_kernel"]:
            print(f"    {p['repo']} uses {', '.join(p['uses'])}")

        print(f"\n  GTM Engines ({len(patterns['gtm_template_users'])}):")
        for g in patterns["gtm_template_users"]:
            print(f"    {g}")

        print(f"\n  Daily Email Fleet ({len(patterns['daily_email_fleet'])}):")
        for d in patterns["daily_email_fleet"]:
            print(f"    {d['repo']} @ {d['cron']}")

        print(f"\n  Research -> Product ({len(patterns['research_to_product'])}):")
        for r in patterns["research_to_product"]:
            print(f"    {r['research']} -> {r['feeds_into']}")

        print(f"\n  Orphaned ({len(patterns['orphaned_repos'])}):")
        for o in patterns["orphaned_repos"]:
            print(f"    {o}")

        print(f"\n  High-Impact Dependencies ({len(patterns['high_impact_dependencies'])}):")
        for h in patterns["high_impact_dependencies"]:
            print(f"    {h['repo']} ({h['depended_by_count']} downstream)")

    elif cmd == "suggest":
        repo = sys.argv[2] if len(sys.argv) > 2 else None
        if not repo:
            print("Usage: brain.py suggest <repo-name>")
            sys.exit(1)
        suggestions = brain.suggest_improvements(repo)
        if not suggestions:
            print(f"  {repo}: No improvements needed!")
        else:
            print(f"\n  Suggestions for {repo}:")
            for s in suggestions:
                print(f"    [{s['priority']:>8}] {s['action']}")

    elif cmd == "report":
        report = brain.ecosystem_report()
        print(f"\n  AONXI ECOSYSTEM REPORT")
        print(f"  {report['timestamp']}")
        print(f"  {'=' * 50}")
        print(f"  Total repos: {report['total_repos']}")
        print(f"\n  Categories:")
        for cat, count in sorted(report["categories"].items()):
            print(f"    {cat}: {count}")
        print(f"\n  Health:")
        for status, count in report["health_summary"].items():
            print(f"    {status}: {count}")
        print(f"\n  Patterns:")
        for k, v in report["patterns"].items():
            print(f"    {k}: {v}")
        if report["orphaned"]:
            print(f"\n  Orphaned repos (no connections):")
            for o in report["orphaned"]:
                print(f"    {o}")

    elif cmd == "learn":
        repo = sys.argv[2] if len(sys.argv) > 2 else None
        if not repo:
            print("Usage: brain.py learn <repo-name>")
            sys.exit(1)
        result = brain.learn_from_repo(repo)
        print(f"  Learned from {repo}: {result['learnings_found']} found, {result['pushed']} pushed")

    elif cmd == "sync-all":
        print("  Syncing all repos to brain...")
        results = brain.sync_all_to_brain()
        total = sum(r.get("pushed", 0) for r in results.values())
        print(f"  Done. {total} learnings pushed from {len(results)} repos.")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
