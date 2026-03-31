#!/usr/bin/env python3
"""
BaseAgent — Every AONXI agent inherits from this.

Provides:
  - Config loading from .env
  - LLM inference via Ollama (localhost:11434)
  - Metric logging to evals.py
  - Insight sharing via Claw V2
  - Decision proposals via Claw V2
  - Run cycle: execute → evaluate → learn → share
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:latest")


class BaseAgent:
    """Base class for all AONXI agents."""

    NAME = "base"
    AGENT_TYPE = "base"
    METRICS = {}  # Override in subclass: {"metric_name": {"direction": "up", "unit": "count"}}

    def __init__(self):
        self.name = self.NAME
        self.agent_type = self.AGENT_TYPE
        self._load_env()
        self.cycle_count = 0
        self.last_run = None
        self.insights_this_cycle = []

    def _load_env(self):
        """Load config from .env file."""
        env_path = Path(__file__).parent.parent.parent / "config" / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, val = line.partition("=")
                        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

    # ── LLM Inference ──────────────────────────────────────────────

    def llm(self, prompt: str, system: str = "", model: str = None, max_tokens: int = 2048) -> str:
        """Call Ollama for local LLM inference. Returns response text."""
        model = model or OLLAMA_MODEL
        payload = {
            "model": model,
            "messages": [],
            "stream": False,
            "options": {"num_predict": max_tokens}
        }
        if system:
            payload["messages"].append({"role": "system", "content": system})
        payload["messages"].append({"role": "user", "content": prompt})

        try:
            req = urllib.request.Request(
                f"{OLLAMA_URL}/api/chat",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return data.get("message", {}).get("content", "")
        except Exception as e:
            self._log(f"LLM error: {e}")
            return f"[LLM unavailable: {e}]"

    # ── API Helpers ────────────────────────────────────────────────

    def api_get(self, url: str, headers: dict = None) -> dict:
        """GET request to any API. Returns parsed JSON."""
        try:
            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            self._log(f"API GET error ({url}): {e}")
            return {"error": str(e)}

    def api_post(self, url: str, data: dict, headers: dict = None) -> dict:
        """POST request to any API. Returns parsed JSON."""
        h = {"Content-Type": "application/json"}
        h.update(headers or {})
        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=h, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            self._log(f"API POST error ({url}): {e}")
            return {"error": str(e)}

    # ── Evals Integration ──────────────────────────────────────────

    def log_metric(self, metric: str, value: float, experiment_id: str = None):
        """Log a metric to the evals system."""
        try:
            from evals import log_metric
            log_metric(self.agent_type, metric, value, experiment_id)
        except Exception as e:
            self._log(f"Eval log error: {e}")

    def start_experiment(self, description: str) -> str:
        """Start an experiment for this agent."""
        try:
            from evals import experiment_start
            return experiment_start(self.agent_type, description)
        except Exception as e:
            self._log(f"Experiment start error: {e}")
            return ""

    def end_experiment(self, exp_id: str, conclusion: str):
        """End an experiment."""
        try:
            from evals import experiment_end
            experiment_end(exp_id, conclusion)
        except Exception as e:
            self._log(f"Experiment end error: {e}")

    # ── Claw V2 Integration ────────────────────────────────────────

    def propose_action(self, action_type: str, description: str,
                       evidence: dict = None, confidence: float = 0.5) -> tuple:
        """Propose an action through Claw V2 decision engine."""
        try:
            from claw import propose_decision
            return propose_decision(self.agent_type, action_type, description, evidence, confidence)
        except Exception as e:
            self._log(f"Claw propose error: {e}")
            return ("none", "error")

    def share_insight(self, insight: str, evidence: dict = None):
        """Share an insight with other agents via Claw V2."""
        try:
            from claw import share_insight
            share_insight(self.agent_type, insight, evidence)
            self.insights_this_cycle.append(insight)
        except Exception as e:
            self._log(f"Claw insight error: {e}")

    def get_insights(self, limit: int = 10) -> list:
        """Get recent insights from connected agents."""
        try:
            from claw import get_insights_for
            return get_insights_for(self.agent_type, limit)
        except Exception as e:
            self._log(f"Claw insights error: {e}")
            return []

    # ── Core Methods (override in subclass) ────────────────────────

    def execute(self) -> dict:
        """Run the agent's primary function. Override this."""
        raise NotImplementedError

    def evaluate(self, results: dict) -> dict:
        """Log metrics from execution results. Override this."""
        raise NotImplementedError

    def learn(self, results: dict, metrics: dict):
        """Learn from results and share insights. Override this."""
        pass

    # ── Run Cycle ──────────────────────────────────────────────────

    def run_cycle(self) -> dict:
        """Full agent cycle: execute → evaluate → learn → share."""
        self.cycle_count += 1
        self.last_run = datetime.now()
        self.insights_this_cycle = []

        self._log(f"Starting cycle #{self.cycle_count}")

        # 1. Check insights from other agents first
        insights = self.get_insights()
        if insights:
            self._log(f"  Read {len(insights)} insights from connected agents")

        # 2. Execute
        try:
            results = self.execute()
        except Exception as e:
            self._log(f"  Execute failed: {e}")
            return {"error": str(e)}

        # 3. Evaluate
        try:
            metrics = self.evaluate(results)
        except Exception as e:
            self._log(f"  Evaluate failed: {e}")
            metrics = {}

        # 4. Learn and share
        try:
            self.learn(results, metrics)
        except Exception as e:
            self._log(f"  Learn failed: {e}")

        self._log(f"  Cycle complete. {len(self.insights_this_cycle)} insights shared.")
        return {"results": results, "metrics": metrics, "insights": self.insights_this_cycle}

    def status(self) -> dict:
        """Return agent status."""
        return {
            "name": self.name,
            "type": self.agent_type,
            "cycles": self.cycle_count,
            "last_run": str(self.last_run) if self.last_run else "never",
            "metrics": list(self.METRICS.keys()),
        }

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] [{self.name}] {msg}", flush=True)
