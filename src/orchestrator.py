#!/usr/bin/env python3
"""
orchestrator.py — The Aonxi Orchestrator

The engine that makes repos improve each other automatically.
Like Bitcoin miners, but instead of hashing, each Mac Mini M4 agent
delivers an outcome — QC'd by humans before anything ships.

How it works:
1. SCAN — Reads every repo, extracts patterns, detects health
2. CONNECT — Finds cross-repo opportunities (shared code, missing deps)
3. SUGGEST — Generates improvement plans for each repo
4. REPORT — Produces a human-readable improvement report
5. EXECUTE — (Only with human approval) Creates branches + PRs

The orchestrator NEVER pushes code without human QC.
Every improvement goes through a gate.

Usage:
    python orchestrator.py scan          # Full ecosystem scan
    python orchestrator.py improve       # Generate improvement report
    python orchestrator.py crosslink     # Find cross-repo opportunities
    python orchestrator.py dashboard     # Generate HTML dashboard
"""

import os
import sys
import json
import subprocess
import glob as glob_mod
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import the brain
sys.path.insert(0, str(Path(__file__).parent))
from brain import SuperBrain, _load_yaml_simple, REPOS_YAML, HOME


class Orchestrator:
    """The engine that makes repos improve each other."""

    def __init__(self):
        self.brain = SuperBrain()
        self.registry = self.brain.load_registry()
        self.scan_results = {}

    # ── SCAN ─────────────────────────────────────────────────────────────

    def full_scan(self) -> dict:
        """Deep scan every repo and return structured analysis."""
        print("  Scanning ecosystem...")
        results = {}

        for name, meta in self.registry.items():
            path = os.path.expanduser(meta.get("path", ""))
            if not os.path.isdir(path):
                results[name] = {"status": "missing", "path": path}
                continue

            scan = {
                "path": path,
                "category": meta.get("category"),
                "priority": meta.get("priority"),
                "health": self.brain.health_check(name),
            }

            # Deep file analysis
            scan["files"] = self._scan_files(path)
            scan["tech_stack"] = self._detect_tech_stack(path)
            scan["size"] = self._repo_size(path)

            results[name] = scan
            print(f"    scanned {name}")

        self.scan_results = results
        return results

    def _scan_files(self, path: str) -> dict:
        """Count files by type in a repo."""
        counts = {}
        try:
            for root, dirs, files in os.walk(path):
                # Skip hidden dirs and node_modules
                dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != "__pycache__"]
                for f in files:
                    ext = Path(f).suffix.lower()
                    if ext:
                        counts[ext] = counts.get(ext, 0) + 1
        except Exception:
            pass
        return counts

    def _detect_tech_stack(self, path: str) -> list:
        """Detect what technologies a repo uses."""
        stack = []
        indicators = {
            "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "javascript": ["package.json"],
            "typescript": ["tsconfig.json"],
            "rust": ["Cargo.toml"],
            "go": ["go.mod"],
            "docker": ["Dockerfile", "docker-compose.yml"],
            "github-actions": [".github/workflows"],
        }
        for tech, files in indicators.items():
            for f in files:
                if os.path.exists(os.path.join(path, f)):
                    stack.append(tech)
                    break
        return stack

    def _repo_size(self, path: str) -> dict:
        """Get repo size metrics."""
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=path, capture_output=True, text=True, timeout=5,
            )
            commits = int(result.stdout.strip()) if result.returncode == 0 else 0
        except Exception:
            commits = 0

        file_count = 0
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
            file_count += len(files)

        return {"commits": commits, "files": file_count}

    # ── CROSSLINK — Find cross-repo opportunities ────────────────────────

    def crosslink_analysis(self) -> dict:
        """Find opportunities where repos can help each other."""
        if not self.scan_results:
            self.full_scan()

        opportunities = {
            "shared_patterns": [],
            "missing_kernel_adoption": [],
            "duplicate_code": [],
            "test_gaps": [],
            "readme_improvements": [],
            "stale_repos_with_dependents": [],
        }

        # Find agents/GTMs that should use kernel but don't
        for name, meta in self.registry.items():
            cat = meta.get("category", "")
            deps = meta.get("depends_on", [])

            if cat in ("agent", "gtm-engine"):
                missing_kernel = []
                for kernel in ["aonxi-router", "aonxi-safeguard", "aonxi-memcollab"]:
                    if kernel not in deps:
                        missing_kernel.append(kernel)
                if missing_kernel:
                    opportunities["missing_kernel_adoption"].append({
                        "repo": name,
                        "missing": missing_kernel,
                        "benefit": "Shared routing, safety, and memory across agents",
                    })

        # Find stale repos that other repos depend on
        for name, meta in self.registry.items():
            depby = meta.get("depended_by", [])
            if depby and depby != ["*"]:
                scan = self.scan_results.get(name, {})
                health = scan.get("health", {})
                if health.get("overall") in ("stale", "needs-attention"):
                    opportunities["stale_repos_with_dependents"].append({
                        "repo": name,
                        "status": health.get("overall"),
                        "depended_by": depby,
                        "risk": f"{len(depby)} repos depend on this stale repo",
                    })

        # Find repos without tests
        for name, scan in self.scan_results.items():
            if isinstance(scan, dict) and scan.get("health", {}).get("checks", {}).get("has_tests") is False:
                priority = self.registry.get(name, {}).get("priority", "medium")
                if priority in ("critical", "high"):
                    opportunities["test_gaps"].append({
                        "repo": name,
                        "priority": priority,
                        "action": "Add tests — this is a high-priority repo without test coverage",
                    })

        # Detect common tech stacks for shared tooling
        python_repos = []
        js_repos = []
        for name, scan in self.scan_results.items():
            if isinstance(scan, dict):
                stack = scan.get("tech_stack", [])
                if "python" in stack:
                    python_repos.append(name)
                if "javascript" in stack or "typescript" in stack:
                    js_repos.append(name)

        if len(python_repos) > 5:
            opportunities["shared_patterns"].append({
                "pattern": "shared-python-tooling",
                "repos": python_repos[:10],
                "suggestion": f"{len(python_repos)} repos use Python — consider shared linting, testing, CI configs",
            })

        return opportunities

    # ── IMPROVE — Generate improvement plans ─────────────────────────────

    def improvement_report(self) -> str:
        """Generate a human-readable improvement report."""
        if not self.scan_results:
            self.full_scan()

        cross = self.crosslink_analysis()
        ecosystem = self.brain.ecosystem_report()

        lines = []
        lines.append("=" * 70)
        lines.append("  AONXI ECOSYSTEM IMPROVEMENT REPORT")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 70)

        # Health summary
        lines.append("\n  HEALTH SUMMARY")
        lines.append("  " + "-" * 40)
        for status, count in ecosystem["health_summary"].items():
            bar = "#" * count
            lines.append(f"    {status:<18} {count:>3}  {bar}")

        # Critical findings
        lines.append("\n  CRITICAL FINDINGS")
        lines.append("  " + "-" * 40)

        if cross["stale_repos_with_dependents"]:
            lines.append("\n  [!] Stale repos with dependents (fix first):")
            for item in cross["stale_repos_with_dependents"]:
                lines.append(f"      {item['repo']} ({item['status']}) — {item['risk']}")

        if cross["test_gaps"]:
            lines.append("\n  [!] High-priority repos without tests:")
            for item in cross["test_gaps"]:
                lines.append(f"      {item['repo']} (priority: {item['priority']})")

        # Kernel adoption opportunities
        if cross["missing_kernel_adoption"]:
            lines.append("\n  KERNEL ADOPTION OPPORTUNITIES")
            lines.append("  " + "-" * 40)
            for item in cross["missing_kernel_adoption"]:
                missing = ", ".join(item["missing"])
                lines.append(f"    {item['repo']}")
                lines.append(f"      missing: {missing}")

        # Patterns
        lines.append("\n  ECOSYSTEM PATTERNS")
        lines.append("  " + "-" * 40)
        for k, v in ecosystem["patterns"].items():
            lines.append(f"    {k}: {v}")

        # Orphaned
        if ecosystem["orphaned"]:
            lines.append("\n  ORPHANED REPOS (consider connecting or archiving):")
            for o in ecosystem["orphaned"]:
                lines.append(f"    {o}")

        lines.append("\n" + "=" * 70)
        lines.append("  END OF REPORT")
        lines.append("  All improvements require human QC before execution.")
        lines.append("=" * 70)

        return "\n".join(lines)

    # ── DASHBOARD — Generate HTML dashboard ──────────────────────────────

    def generate_dashboard(self) -> str:
        """Generate a dark-mode HTML dashboard of the ecosystem."""
        if not self.scan_results:
            self.full_scan()

        ecosystem = self.brain.ecosystem_report()
        cross = self.crosslink_analysis()

        # Build repo cards
        repo_cards = []
        for name, scan in sorted(self.scan_results.items()):
            if not isinstance(scan, dict) or scan.get("status") == "missing":
                continue
            health = scan.get("health", {})
            overall = health.get("overall", "unknown")
            cat = scan.get("category", "?")
            priority = scan.get("priority", "?")
            commits = scan.get("size", {}).get("commits", 0)
            files = scan.get("size", {}).get("files", 0)
            stack = ", ".join(scan.get("tech_stack", []))
            days = health.get("checks", {}).get("days_since_commit", "?")
            meta = self.registry.get(name, {})
            purpose = meta.get("purpose", "")[:80]
            github = meta.get("github", "")

            color = {"healthy": "#00ff94", "stale": "#ffc312", "needs-attention": "#ff4757"}.get(overall, "#666")

            repo_cards.append(f"""
            <div class="repo-card" style="border-left: 3px solid {color}">
              <div class="repo-header">
                <span class="repo-name">{name}</span>
                <span class="repo-badge" style="color:{color}">{overall}</span>
              </div>
              <div class="repo-meta">{cat} | {priority} | {stack}</div>
              <div class="repo-purpose">{purpose}</div>
              <div class="repo-stats">
                <span>{commits} commits</span>
                <span>{files} files</span>
                <span>{days}d since update</span>
              </div>
            </div>""")

        cards_html = "\n".join(repo_cards)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Super Brain — Ecosystem Dashboard</title>
<style>
  :root {{ --bg:#05060a; --s1:#0a0c12; --s2:#0f1118; --text:#f2f0eb;
           --muted:rgba(242,240,235,0.5); --dim:rgba(242,240,235,0.22);
           --g:#00ff94; --red:#ff4757; --amber:#ffc312; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:var(--bg); color:var(--text); font-family:-apple-system,sans-serif; padding:40px; }}
  h1 {{ color:var(--g); font-size:28px; margin-bottom:8px; }}
  .subtitle {{ color:var(--muted); font-size:14px; margin-bottom:32px; }}
  .stats-row {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:32px; }}
  .stat {{ background:var(--s1); padding:20px; border-radius:8px; }}
  .stat-num {{ font-size:32px; font-weight:800; color:var(--g); }}
  .stat-label {{ font-size:11px; color:var(--dim); margin-top:4px; }}
  .section-title {{ font-size:18px; font-weight:700; margin:24px 0 16px; }}
  .repo-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:12px; }}
  .repo-card {{ background:var(--s1); padding:16px; border-radius:8px; }}
  .repo-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }}
  .repo-name {{ font-weight:700; font-size:14px; }}
  .repo-badge {{ font-size:10px; font-family:monospace; text-transform:uppercase; }}
  .repo-meta {{ font-size:10px; color:var(--dim); font-family:monospace; margin-bottom:6px; }}
  .repo-purpose {{ font-size:12px; color:var(--muted); line-height:1.5; margin-bottom:8px; }}
  .repo-stats {{ display:flex; gap:16px; font-size:10px; color:var(--dim); font-family:monospace; }}
  .findings {{ background:var(--s1); padding:20px; border-radius:8px; margin-bottom:16px; }}
  .finding {{ padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.04); font-size:13px; color:var(--muted); }}
  .finding:last-child {{ border-bottom:none; }}
  .finding strong {{ color:var(--text); }}
</style>
</head>
<body>
  <h1>SUPER BRAIN — Ecosystem Dashboard</h1>
  <div class="subtitle">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | {ecosystem['total_repos']} repos | Aonxi OS</div>

  <div class="stats-row">
    <div class="stat"><div class="stat-num">{ecosystem['total_repos']}</div><div class="stat-label">Total Repos</div></div>
    <div class="stat"><div class="stat-num">{ecosystem['health_summary'].get('healthy', 0)}</div><div class="stat-label">Healthy</div></div>
    <div class="stat"><div class="stat-num">{ecosystem['health_summary'].get('stale', 0)}</div><div class="stat-label">Stale</div></div>
    <div class="stat"><div class="stat-num">{ecosystem['health_summary'].get('needs-attention', 0)}</div><div class="stat-label">Needs Attention</div></div>
    <div class="stat"><div class="stat-num">{ecosystem['patterns'].get('kernel_consumers', 0)}</div><div class="stat-label">Kernel Consumers</div></div>
  </div>

  <div class="section-title">Critical Findings</div>
  <div class="findings">
    {"".join(f'<div class="finding"><strong>{item["repo"]}</strong> — {item["risk"]}</div>' for item in cross.get("stale_repos_with_dependents", [])) or '<div class="finding">No critical findings.</div>'}
  </div>

  <div class="section-title">All Repos</div>
  <div class="repo-grid">
    {cards_html}
  </div>
</body>
</html>"""
        return html


def main():
    if len(sys.argv) < 2:
        print("Aonxi Orchestrator — Makes repos improve each other")
        print()
        print("Commands:")
        print("  scan        Full ecosystem scan")
        print("  improve     Generate improvement report")
        print("  crosslink   Find cross-repo opportunities")
        print("  dashboard   Generate HTML dashboard")
        sys.exit(0)

    cmd = sys.argv[1]
    orch = Orchestrator()

    if cmd == "scan":
        results = orch.full_scan()
        healthy = sum(1 for r in results.values() if isinstance(r, dict) and r.get("health", {}).get("overall") == "healthy")
        print(f"\n  Scanned {len(results)} repos. {healthy} healthy.")

    elif cmd == "improve":
        report = orch.improvement_report()
        print(report)
        # Also save to file
        out_path = os.path.expanduser("~/super-brain/reports")
        os.makedirs(out_path, exist_ok=True)
        filename = f"improvement-report-{datetime.now().strftime('%Y-%m-%d')}.txt"
        with open(os.path.join(out_path, filename), "w") as f:
            f.write(report)
        print(f"\n  Saved to ~/super-brain/reports/{filename}")

    elif cmd == "crosslink":
        orch.full_scan()
        cross = orch.crosslink_analysis()
        print(json.dumps(cross, indent=2))

    elif cmd == "dashboard":
        html = orch.generate_dashboard()
        out_path = os.path.expanduser("~/super-brain/reports")
        os.makedirs(out_path, exist_ok=True)
        filename = f"dashboard-{datetime.now().strftime('%Y-%m-%d')}.html"
        filepath = os.path.join(out_path, filename)
        with open(filepath, "w") as f:
            f.write(html)
        print(f"  Dashboard saved to {filepath}")
        # Try to open in browser
        try:
            subprocess.run(["open", filepath], timeout=5)
        except Exception:
            pass

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
