#!/usr/bin/env python3
from __future__ import annotations
"""
AONXI OS — Agent Evaluation & Experiment Attribution Engine
============================================================

Superior to Benchspan. Here's why:
  Benchspan benchmarks models in a lab. We benchmark OUTCOMES in production.
  They measure "which model is better." We measure "which CHANGE made the
  agent generate more revenue per dollar spent."

The ONE metric that matters:
  RPDC = Revenue Per Dollar of Cost
       = Revenue Attributed to Agent / (Inference Cost + Human QC Time Cost)
  Everything else is a leading indicator to this.

What this system does:
  1. EXPERIMENTS — Every change to an agent is an experiment. Before/after.
     You know EXACTLY which change drove which improvement.
  2. ATTRIBUTION — From code change → metric movement → revenue impact.
     Fully traceable. No vague correlations.
  3. CROSS-AGENT CAUSALITY — When outreach improves, did sales improve too?
     Measured, timestamped, attributed.
  4. COMPOUND INTELLIGENCE SCORE — One number that tells you if the whole
     system is getting smarter or dumber. Updated daily.

Usage:
    python3 evals.py experiment start <agent> "<description>"
    python3 evals.py experiment end <experiment_id> "<conclusion>"
    python3 evals.py log <agent> <metric> <value> [--experiment <id>]
    python3 evals.py rpdc [<agent>]
    python3 evals.py trend <agent> [--days N]
    python3 evals.py dashboard
    python3 evals.py attribution <experiment_id>
    python3 evals.py leaderboard
    python3 evals.py compound-score [--weeks N]
    python3 evals.py report [--weeks N]
    python3 evals.py agents
    python3 evals.py experiments [--agent <name>]
"""

import json
import os
import sqlite3
import statistics
import sys
import textwrap
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

DB_PATH = Path.home() / "super-brain" / "data" / "evals.db"

# Canonical agent definitions
# direction: "up" = higher is better, "down" = lower is better
AGENT_METRICS: dict[str, dict[str, dict]] = {
    "outreach": {
        "leads_found":       {"direction": "up",   "unit": "count", "revenue_weight": 0.15},
        "emails_sent":       {"direction": "up",   "unit": "count", "revenue_weight": 0.05},
        "reply_rate":        {"direction": "up",   "unit": "%",     "revenue_weight": 0.20},
        "meetings_booked":   {"direction": "up",   "unit": "count", "revenue_weight": 0.35},
        "revenue_generated": {"direction": "up",   "unit": "$",     "revenue_weight": 1.00},
        "cost_per_lead":     {"direction": "down", "unit": "$",     "revenue_weight": 0.10},
        "human_qc_minutes":  {"direction": "down", "unit": "min",   "revenue_weight": 0.05},
    },
    "hr": {
        "resumes_screened":      {"direction": "up",   "unit": "count", "revenue_weight": 0.10},
        "time_per_hire":         {"direction": "down", "unit": "days",  "revenue_weight": 0.30},
        "offer_acceptance_rate": {"direction": "up",   "unit": "%",     "revenue_weight": 0.25},
        "cost_per_hire":         {"direction": "down", "unit": "$",     "revenue_weight": 0.20},
        "human_qc_minutes":      {"direction": "down", "unit": "min",   "revenue_weight": 0.05},
    },
    "it_helpdesk": {
        "tickets_resolved":    {"direction": "up",   "unit": "count", "revenue_weight": 0.15},
        "auto_resolve_rate":   {"direction": "up",   "unit": "%",     "revenue_weight": 0.35},
        "avg_resolution_time": {"direction": "down", "unit": "min",   "revenue_weight": 0.25},
        "escalation_rate":     {"direction": "down", "unit": "%",     "revenue_weight": 0.15},
        "human_qc_minutes":    {"direction": "down", "unit": "min",   "revenue_weight": 0.05},
    },
    "sales": {
        "pipeline_value":    {"direction": "up",   "unit": "$",     "revenue_weight": 0.30},
        "close_rate":        {"direction": "up",   "unit": "%",     "revenue_weight": 0.35},
        "avg_deal_size":     {"direction": "up",   "unit": "$",     "revenue_weight": 0.20},
        "cycle_time_days":   {"direction": "down", "unit": "days",  "revenue_weight": 0.10},
        "human_qc_minutes":  {"direction": "down", "unit": "min",   "revenue_weight": 0.05},
    },
    "support": {
        "response_time_seconds": {"direction": "down", "unit": "sec",  "revenue_weight": 0.15},
        "resolution_rate":       {"direction": "up",   "unit": "%",    "revenue_weight": 0.30},
        "csat_score":            {"direction": "up",   "unit": "/10",  "revenue_weight": 0.35},
        "churn_prevented":       {"direction": "up",   "unit": "count","revenue_weight": 0.15},
        "human_qc_minutes":      {"direction": "down", "unit": "min",  "revenue_weight": 0.05},
    },
    "finance": {
        "invoices_processed":  {"direction": "up",   "unit": "count", "revenue_weight": 0.15},
        "forecast_accuracy":   {"direction": "up",   "unit": "%",     "revenue_weight": 0.40},
        "anomalies_detected":  {"direction": "up",   "unit": "count", "revenue_weight": 0.25},
        "time_saved_hours":    {"direction": "up",   "unit": "hrs",   "revenue_weight": 0.15},
        "human_qc_minutes":    {"direction": "down", "unit": "min",   "revenue_weight": 0.05},
    },
    "daily_fleet": {
        "emails_delivered": {"direction": "up", "unit": "count", "revenue_weight": 0.20},
        "open_rate":        {"direction": "up", "unit": "%",     "revenue_weight": 0.40},
        "click_rate":       {"direction": "up", "unit": "%",     "revenue_weight": 0.30},
        "unsubscribe_rate": {"direction": "down","unit": "%",    "revenue_weight": 0.10},
    },
    "qa": {
        "tests_generated":     {"direction": "up",   "unit": "count", "revenue_weight": 0.15},
        "tests_passed":        {"direction": "up",   "unit": "count", "revenue_weight": 0.20},
        "bugs_found":          {"direction": "up",   "unit": "count", "revenue_weight": 0.30},
        "false_positive_rate": {"direction": "down", "unit": "%",     "revenue_weight": 0.25},
        "regression_catch_rate":{"direction": "up",  "unit": "%",     "revenue_weight": 0.10},
    },
    "brain": {
        "memories_count":               {"direction": "up", "unit": "count", "revenue_weight": 0.15},
        "search_relevance_avg":         {"direction": "up", "unit": "/1.0",  "revenue_weight": 0.40},
        "cross_repo_patterns_detected": {"direction": "up", "unit": "count", "revenue_weight": 0.25},
        "cross_agent_insights_shared":  {"direction": "up", "unit": "count", "revenue_weight": 0.20},
    },
}

# Causal links: when source improves, we expect target to improve
# This is the FAMILY EFFECT — agents teaching agents
CAUSAL_LINKS = [
    ("outreach", "leads_found",        "sales",       "pipeline_value",   "More leads → bigger pipeline"),
    ("outreach", "meetings_booked",    "sales",       "close_rate",       "Better meetings → higher close rate"),
    ("outreach", "reply_rate",         "sales",       "avg_deal_size",    "Better replies → more qualified deals"),
    ("qa",       "bugs_found",         "support",     "resolution_rate",  "Fewer bugs → easier support"),
    ("qa",       "tests_passed",       "it_helpdesk", "auto_resolve_rate","Better QA → fewer real issues"),
    ("brain",    "search_relevance_avg","outreach",   "reply_rate",       "Better memory → better personalization"),
    ("brain",    "cross_agent_insights_shared", "outreach", "meetings_booked", "Shared insights → better outreach"),
    ("brain",    "cross_repo_patterns_detected","qa",  "regression_catch_rate","Pattern detection → better testing"),
    ("hr",       "time_per_hire",       "it_helpdesk", "tickets_resolved", "Faster hiring → less IT backlog"),
    ("daily_fleet","open_rate",         "outreach",    "reply_rate",       "Audience engaged → warmer leads"),
    ("finance",  "forecast_accuracy",  "sales",       "pipeline_value",   "Better forecasts → better targeting"),
    ("support",  "csat_score",         "sales",       "close_rate",       "Happy clients → referral closes"),
    ("support",  "churn_prevented",    "finance",     "forecast_accuracy","Less churn → better predictions"),
]

# Cost assumptions (for RPDC calculation)
DEFAULT_INFERENCE_COST_PER_QUERY = 0.0001   # $0.0001 per local query (electricity)
DEFAULT_HUMAN_HOUR_COST = 50.0              # $50/hr for human QC time


# ─────────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS metric_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            agent         TEXT    NOT NULL,
            metric        TEXT    NOT NULL,
            value         REAL    NOT NULL,
            experiment_id TEXT,
            ts            TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime')),
            week_iso      TEXT    NOT NULL DEFAULT (strftime('%Y-W%W','now','localtime'))
        );

        CREATE INDEX IF NOT EXISTS idx_agent_metric_ts
        ON metric_logs (agent, metric, ts);

        CREATE INDEX IF NOT EXISTS idx_experiment
        ON metric_logs (experiment_id);

        CREATE TABLE IF NOT EXISTS experiments (
            id            TEXT    PRIMARY KEY,
            agent         TEXT    NOT NULL,
            description   TEXT    NOT NULL,
            hypothesis    TEXT    DEFAULT '',
            status        TEXT    NOT NULL DEFAULT 'running',
            started_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime')),
            ended_at      TEXT,
            conclusion    TEXT,
            metrics_before TEXT   DEFAULT '{}',
            metrics_after  TEXT   DEFAULT '{}',
            rpdc_before   REAL   DEFAULT 0,
            rpdc_after    REAL   DEFAULT 0,
            rpdc_delta    REAL   DEFAULT 0,
            revenue_impact REAL  DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS daily_snapshots (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            agent         TEXT    NOT NULL,
            date          TEXT    NOT NULL,
            metrics_json  TEXT    NOT NULL DEFAULT '{}',
            rpdc          REAL    DEFAULT 0,
            cis           REAL    DEFAULT 0,
            UNIQUE(agent, date)
        );

        CREATE TABLE IF NOT EXISTS rpdc_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            agent         TEXT    NOT NULL,
            revenue       REAL    DEFAULT 0,
            inference_cost REAL   DEFAULT 0,
            human_cost    REAL    DEFAULT 0,
            rpdc          REAL    DEFAULT 0,
            period        TEXT    NOT NULL,
            ts            TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
        );
    """)
    conn.commit()
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# Experiments — the core innovation
# ─────────────────────────────────────────────────────────────────────────────

def experiment_start(agent: str, description: str, hypothesis: str = "") -> str:
    """Start an experiment. Snapshots current metrics as 'before'."""
    agent = _normalize(agent)
    _validate_agent(agent)

    conn = _get_conn()
    exp_id = f"exp-{agent[:3]}-{datetime.now().strftime('%m%d')}-{uuid.uuid4().hex[:6]}"

    # Snapshot current metrics as baseline
    before = _snapshot_metrics(conn, agent)

    conn.execute("""
        INSERT INTO experiments (id, agent, description, hypothesis, metrics_before)
        VALUES (?, ?, ?, ?, ?)
    """, (exp_id, agent, description, hypothesis, json.dumps(before)))
    conn.commit()
    conn.close()

    print(f"\n  EXPERIMENT STARTED")
    print(f"  {'='*60}")
    print(f"  ID:          {exp_id}")
    print(f"  Agent:       {agent}")
    print(f"  Change:      {description}")
    if hypothesis:
        print(f"  Hypothesis:  {hypothesis}")
    print(f"  Baseline:    {len(before)} metrics captured")
    for k, v in sorted(before.items()):
        print(f"    {k:<35s} {v:>10.2f}")
    print(f"\n  Log metrics with: evals.py log {agent} <metric> <value> --experiment {exp_id}")
    print(f"  End with:         evals.py experiment end {exp_id} \"<conclusion>\"")
    print(f"  {'='*60}\n")
    return exp_id


def experiment_end(exp_id: str, conclusion: str = "") -> None:
    """End an experiment. Snapshots current metrics as 'after'. Calculates attribution."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,)).fetchone()
    if not row:
        _die(f"Experiment '{exp_id}' not found.")
    if row["status"] == "completed":
        _die(f"Experiment '{exp_id}' already completed.")

    agent = row["agent"]
    before = json.loads(row["metrics_before"])
    after = _snapshot_metrics(conn, agent)

    # Calculate deltas
    deltas = {}
    for metric in set(list(before.keys()) + list(after.keys())):
        b = before.get(metric, 0)
        a = after.get(metric, 0)
        if b != 0:
            pct = ((a - b) / abs(b)) * 100
            meta = AGENT_METRICS.get(agent, {}).get(metric, {})
            if meta.get("direction") == "down":
                pct = -pct  # flip so positive = improvement
            deltas[metric] = {"before": b, "after": a, "change_pct": pct}

    # Calculate RPDC before and after
    rpdc_before = _calc_rpdc(conn, agent, before=True, exp_started=row["started_at"])
    rpdc_after = _calc_rpdc(conn, agent, before=False, exp_started=row["started_at"])
    rpdc_delta = rpdc_after - rpdc_before

    # Revenue impact estimation
    rev_before = before.get("revenue_generated", 0)
    rev_after = after.get("revenue_generated", rev_before)
    revenue_impact = rev_after - rev_before

    conn.execute("""
        UPDATE experiments SET
            status = 'completed', ended_at = ?, conclusion = ?,
            metrics_after = ?, rpdc_before = ?, rpdc_after = ?,
            rpdc_delta = ?, revenue_impact = ?
        WHERE id = ?
    """, (
        datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), conclusion,
        json.dumps(after), rpdc_before, rpdc_after,
        rpdc_delta, revenue_impact, exp_id
    ))
    conn.commit()

    # Print results
    print(f"\n  EXPERIMENT COMPLETED")
    print(f"  {'='*60}")
    print(f"  ID:          {exp_id}")
    print(f"  Agent:       {agent}")
    print(f"  Change:      {row['description']}")
    print(f"  Duration:    {row['started_at']} -> {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if conclusion:
        print(f"  Conclusion:  {conclusion}")
    print(f"\n  METRIC CHANGES:")
    for metric, d in sorted(deltas.items()):
        arrow = _arrow(d["change_pct"], "up")
        print(f"    {metric:<30s} {d['before']:>10.2f} -> {d['after']:>10.2f}  ({d['change_pct']:+.1f}% {arrow})")

    print(f"\n  RPDC (Revenue Per Dollar of Cost):")
    print(f"    Before:  {rpdc_before:>10.2f}x")
    print(f"    After:   {rpdc_after:>10.2f}x")
    print(f"    Delta:   {rpdc_delta:+.2f}x {'^^' if rpdc_delta > 0 else 'vv'}")

    if revenue_impact != 0:
        print(f"\n  REVENUE IMPACT: ${revenue_impact:+,.2f}")

    # Cross-agent ripple effect
    print(f"\n  CROSS-AGENT RIPPLE:")
    _show_ripple(conn, agent, deltas)

    print(f"  {'='*60}\n")
    conn.close()


def show_attribution(exp_id: str) -> None:
    """Show full attribution chain for a completed experiment."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,)).fetchone()
    if not row:
        _die(f"Experiment '{exp_id}' not found.")

    before = json.loads(row["metrics_before"])
    after = json.loads(row["metrics_after"])

    print(f"\n  FULL ATTRIBUTION: {exp_id}")
    print(f"  {'='*60}")
    print(f"  Agent:       {row['agent']}")
    print(f"  Change:      {row['description']}")
    print(f"  Status:      {row['status']}")
    print(f"  Started:     {row['started_at']}")
    if row['ended_at']:
        print(f"  Ended:       {row['ended_at']}")
    if row['conclusion']:
        print(f"  Conclusion:  {row['conclusion']}")

    print(f"\n  ATTRIBUTION CHAIN:")
    print(f"    Code change: \"{row['description']}\"")
    print(f"         |")

    # Show metric movements
    improved = []
    regressed = []
    for metric in sorted(set(list(before.keys()) + list(after.keys()))):
        b = before.get(metric, 0)
        a = after.get(metric, 0)
        if b != 0:
            pct = ((a - b) / abs(b)) * 100
            meta = AGENT_METRICS.get(row['agent'], {}).get(metric, {})
            if meta.get("direction") == "down":
                pct = -pct
            if pct > 0:
                improved.append((metric, pct, b, a))
            elif pct < 0:
                regressed.append((metric, pct, b, a))

    if improved:
        for m, p, b, a in improved:
            print(f"         +-> {m}: {b:.1f} -> {a:.1f} ({p:+.1f}%)")
    if regressed:
        for m, p, b, a in regressed:
            print(f"         !-> {m}: {b:.1f} -> {a:.1f} ({p:+.1f}%)")

    print(f"         |")
    print(f"         v")
    print(f"    RPDC: {row['rpdc_before']:.2f}x -> {row['rpdc_after']:.2f}x ({row['rpdc_delta']:+.2f}x)")

    if row['revenue_impact'] != 0:
        print(f"         |")
        print(f"         v")
        print(f"    Revenue impact: ${row['revenue_impact']:+,.2f}")

    # Show which experiments on this agent were correlated
    other_exps = conn.execute("""
        SELECT * FROM experiments
        WHERE agent = ? AND id != ? AND status = 'completed'
        ORDER BY started_at DESC LIMIT 5
    """, (row['agent'], exp_id)).fetchall()

    if other_exps:
        print(f"\n  COMPARISON WITH OTHER EXPERIMENTS ON {row['agent'].upper()}:")
        for e in other_exps:
            print(f"    {e['id']}: RPDC {e['rpdc_delta']:+.2f}x | \"{e['description'][:50]}\"")

    print(f"  {'='*60}\n")
    conn.close()


def list_experiments(agent: str = None) -> None:
    """List all experiments, optionally filtered by agent."""
    conn = _get_conn()
    if agent:
        agent = _normalize(agent)
        rows = conn.execute(
            "SELECT * FROM experiments WHERE agent = ? ORDER BY started_at DESC", (agent,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM experiments ORDER BY started_at DESC").fetchall()
    conn.close()

    if not rows:
        print("  No experiments found.")
        return

    print(f"\n  EXPERIMENTS ({len(rows)} total)")
    print(f"  {'='*80}")
    print(f"  {'ID':<26s} {'Agent':<12s} {'Status':<10s} {'RPDC Delta':>10s}  Description")
    print(f"  {'-'*26} {'-'*12} {'-'*10} {'-'*10}  {'-'*30}")
    for r in rows:
        rpdc = f"{r['rpdc_delta']:+.2f}x" if r['status'] == 'completed' else '--'
        desc = r['description'][:40]
        print(f"  {r['id']:<26s} {r['agent']:<12s} {r['status']:<10s} {rpdc:>10s}  {desc}")
    print(f"  {'='*80}\n")


# ─────────────────────────────────────────────────────────────────────────────
# RPDC — The ONE Metric
# ─────────────────────────────────────────────────────────────────────────────

def show_rpdc(agent: str = None) -> None:
    """Show Revenue Per Dollar of Cost for each agent."""
    conn = _get_conn()

    print(f"\n  RPDC — Revenue Per Dollar of Cost")
    print(f"  {'='*60}")
    print(f"  Formula: Revenue / (Inference Cost + Human QC Cost)")
    print(f"  Target: > 10x (every $1 spent generates $10+ revenue)")
    print()

    agents = [agent] if agent else sorted(AGENT_METRICS.keys())
    for ag in agents:
        ag = _normalize(ag)
        if ag not in AGENT_METRICS:
            continue

        # Get latest metrics
        latest = _snapshot_metrics(conn, ag)
        revenue = latest.get("revenue_generated", 0)
        if revenue == 0:
            # Estimate revenue from other metrics
            revenue = _estimate_revenue(ag, latest)

        # Cost: inference (near zero for local) + human QC time
        human_mins = latest.get("human_qc_minutes", 0)
        human_cost = (human_mins / 60) * DEFAULT_HUMAN_HOUR_COST
        # Estimate inference cost from volume
        queries = latest.get("emails_sent", 0) + latest.get("tickets_resolved", 0) + \
                  latest.get("resumes_screened", 0) + latest.get("tests_generated", 0) + 1
        inference_cost = queries * DEFAULT_INFERENCE_COST_PER_QUERY

        total_cost = inference_cost + human_cost
        rpdc = revenue / total_cost if total_cost > 0 else 0

        # Trend
        prev = conn.execute("""
            SELECT rpdc FROM rpdc_log WHERE agent = ? ORDER BY ts DESC LIMIT 1
        """, (ag,)).fetchone()
        prev_rpdc = prev["rpdc"] if prev else 0
        delta = rpdc - prev_rpdc

        # Save to log
        period = datetime.now().strftime("%Y-W%W")
        conn.execute("""
            INSERT INTO rpdc_log (agent, revenue, inference_cost, human_cost, rpdc, period)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ag, revenue, inference_cost, human_cost, rpdc, period))

        bar = _bar(min(rpdc, 100), width=30)
        arrow = "^^" if delta > 1 else "^" if delta > 0 else "--" if delta == 0 else "v" if delta > -1 else "vv"
        print(f"  {ag:<16s} RPDC: {rpdc:>8.1f}x  (delta: {delta:+.1f}x {arrow})  {bar}")
        print(f"    Revenue: ${revenue:>10,.2f}  Cost: ${total_cost:>8.4f}  (inference: ${inference_cost:.4f} + human: ${human_cost:.2f})")

    conn.commit()
    conn.close()
    print(f"\n  {'='*60}\n")


def show_leaderboard() -> None:
    """Show which experiments drove the most improvement."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT * FROM experiments
        WHERE status = 'completed'
        ORDER BY rpdc_delta DESC
        LIMIT 20
    """).fetchall()
    conn.close()

    if not rows:
        print("  No completed experiments yet.")
        return

    print(f"\n  EXPERIMENT LEADERBOARD — Which Changes Actually Worked")
    print(f"  {'='*80}")
    print(f"  {'Rank':<5s} {'RPDC Delta':>10s} {'Agent':<12s} {'Change':<50s}")
    print(f"  {'-'*5} {'-'*10} {'-'*12} {'-'*50}")
    for i, r in enumerate(rows, 1):
        medal = {1: ">>", 2: " >", 3: "  "}.get(i, "  ")
        desc = r['description'][:48]
        print(f"  {medal}{i:<3d} {r['rpdc_delta']:+8.2f}x  {r['agent']:<12s} {desc}")
    print(f"  {'='*80}\n")


# ─────────────────────────────────────────────────────────────────────────────
# Core metric operations
# ─────────────────────────────────────────────────────────────────────────────

def log_metric(agent: str, metric: str, value: float, experiment_id: str = None) -> None:
    agent = _normalize(agent)
    metric = _normalize(metric)
    _validate_agent(agent)

    if metric not in AGENT_METRICS[agent]:
        valid = ", ".join(sorted(AGENT_METRICS[agent]))
        _die(f"Unknown metric '{metric}' for '{agent}'. Valid: {valid}")

    conn = _get_conn()
    now = datetime.now()

    # Validate experiment exists if provided
    if experiment_id:
        exp = conn.execute("SELECT status FROM experiments WHERE id = ?", (experiment_id,)).fetchone()
        if not exp:
            _die(f"Experiment '{experiment_id}' not found.")
        if exp["status"] != "running":
            _die(f"Experiment '{experiment_id}' is not running (status: {exp['status']}).")

    conn.execute(
        "INSERT INTO metric_logs (agent, metric, value, experiment_id, ts, week_iso) VALUES (?,?,?,?,?,?)",
        (agent, metric, value, experiment_id, now.strftime("%Y-%m-%dT%H:%M:%S"), now.strftime("%Y-W%W")),
    )
    conn.commit()
    conn.close()

    meta = AGENT_METRICS[agent][metric]
    exp_str = f" [experiment: {experiment_id}]" if experiment_id else ""
    print(f"  Logged  {agent}.{metric} = {value} {meta['unit']}{exp_str}")


def show_trend(agent: str, days: int = 30) -> None:
    agent = _normalize(agent)
    _validate_agent(agent)
    conn = _get_conn()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")
    rows = conn.execute(
        "SELECT metric, ts, value FROM metric_logs WHERE agent = ? AND ts >= ? ORDER BY ts",
        (agent, cutoff),
    ).fetchall()
    conn.close()

    if not rows:
        print(f"  No data for '{agent}' in the last {days} days.")
        return

    result: dict[str, list] = {}
    for r in rows:
        result.setdefault(r["metric"], []).append(r["value"])

    print(f"\n  Trend for '{agent}' (last {days} days)")
    print(f"  {'='*60}")
    for metric, values in sorted(result.items()):
        meta = AGENT_METRICS.get(agent, {}).get(metric, {})
        direction = meta.get("direction", "up")
        unit = meta.get("unit", "")
        first, current = values[0], values[-1]
        change_pct = _safe_pct(first, current)
        arrow = _arrow(change_pct, direction)
        spark = _sparkline(values)

        print(f"\n  {metric} ({unit}, want {direction})")
        print(f"    {spark}")
        print(f"    Start: {first:>10.2f}  Current: {current:>10.2f}  Change: {change_pct:+.1f}% {arrow}")
    print()


def show_dashboard() -> None:
    conn = _get_conn()
    now = datetime.now()
    this_week = now.strftime("%Y-W%W")
    prev_week = (now - timedelta(weeks=1)).strftime("%Y-W%W")

    print(f"\n  {'='*72}")
    print(f"  AONXI OS  Agent Performance Dashboard       {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"  {'='*72}")

    any_data = False
    for agent in sorted(AGENT_METRICS):
        scores = []
        for metric, meta in AGENT_METRICS[agent].items():
            curr = conn.execute(
                "SELECT AVG(value) as v FROM metric_logs WHERE agent=? AND metric=? AND week_iso=?",
                (agent, metric, this_week)).fetchone()
            prev = conn.execute(
                "SELECT AVG(value) as v FROM metric_logs WHERE agent=? AND metric=? AND week_iso=?",
                (agent, metric, prev_week)).fetchone()
            cv, pv = curr["v"], prev["v"]
            if cv is not None and pv is not None and pv != 0:
                pct = ((cv - pv) / abs(pv)) * 100
                if meta["direction"] == "down":
                    pct = -pct
                scores.append(pct)

        if not scores:
            continue
        any_data = True
        avg = statistics.mean(scores)
        bar = _bar(avg, width=30)
        print(f"\n  {agent:<16s} {avg:+6.1f}% WoW  {_arrow(avg,'up')}  {bar}")
        for metric, meta in sorted(AGENT_METRICS[agent].items()):
            cv = conn.execute(
                "SELECT AVG(value) as v FROM metric_logs WHERE agent=? AND metric=? AND week_iso=?",
                (agent, metric, this_week)).fetchone()["v"]
            if cv is not None:
                print(f"    {metric:<35s} {cv:>10.2f} {meta['unit']}")

    # Active experiments
    active = conn.execute("SELECT * FROM experiments WHERE status = 'running'").fetchall()
    if active:
        print(f"\n  ACTIVE EXPERIMENTS ({len(active)}):")
        for e in active:
            print(f"    [{e['id']}] {e['agent']}: {e['description'][:50]}")

    conn.close()
    if not any_data:
        print("\n  No week-over-week data yet. Log metrics for at least 2 weeks.")
    print(f"\n  {'='*72}\n")


def compound_score(weeks: int = 4) -> None:
    """
    Compound Intelligence Score (CIS) — One number for the whole system.

    Components:
      1. Individual agent improvement (35%)
      2. Cross-agent causal lift (25%)
      3. Experiment velocity (20%) — are we running more successful experiments?
      4. Memory compound rate (20%)
    """
    conn = _get_conn()
    now = datetime.now()
    week_labels = [(now - timedelta(weeks=i)).strftime("%Y-W%W") for i in range(weeks + 1)]
    week_labels.reverse()

    print(f"\n  {'='*72}")
    print(f"  AONXI OS  Compound Intelligence Score (CIS)")
    print(f"  Period: last {weeks} weeks ending {now.strftime('%Y-%m-%d')}")
    print(f"  {'='*72}")

    # 1. Individual improvement
    agent_scores: dict[str, float] = {}
    for agent, metrics in AGENT_METRICS.items():
        changes = []
        for metric, meta in metrics.items():
            ch = _metric_change(conn, agent, metric, week_labels, meta["direction"])
            if ch is not None:
                changes.append(ch * meta.get("revenue_weight", 1.0))
        if changes:
            agent_scores[agent] = sum(changes) / sum(
                AGENT_METRICS[agent][m].get("revenue_weight", 1.0)
                for m in AGENT_METRICS[agent]
            ) * len(changes)

    individual = _clamp(statistics.mean(agent_scores.values()), -100, 100) if agent_scores else 0

    print(f"\n  1. Individual Agent Improvement (35%)")
    if agent_scores:
        for ag in sorted(agent_scores):
            print(f"     {ag:<16s} {agent_scores[ag]:+6.1f}%  {_arrow(agent_scores[ag],'up')}")
        print(f"     {'Weighted mean':<16s} {individual:+6.1f}%")
    else:
        print("     No data.")

    # 2. Cross-agent causal lift
    cross = []
    print(f"\n  2. Cross-Agent Causal Lift (25%)")
    for src_ag, src_m, tgt_ag, tgt_m, reason in CAUSAL_LINKS:
        src_meta = AGENT_METRICS.get(src_ag, {}).get(src_m, {})
        tgt_meta = AGENT_METRICS.get(tgt_ag, {}).get(tgt_m, {})
        src_ch = _metric_change(conn, src_ag, src_m, week_labels, src_meta.get("direction", "up"))
        tgt_ch = _metric_change(conn, tgt_ag, tgt_m, week_labels, tgt_meta.get("direction", "up"))
        if src_ch is not None and tgt_ch is not None:
            lift = min(src_ch, tgt_ch) if (src_ch > 0 and tgt_ch > 0) else (tgt_ch * 0.5 if src_ch > 0 else 0)
            cross.append(lift)
            print(f"     {src_ag}.{src_m} -> {tgt_ag}.{tgt_m}")
            print(f"       {reason}: {lift:+.1f}% {_arrow(lift,'up')}")

    cross_score = _clamp(statistics.mean(cross), -100, 100) if cross else 0
    if not cross:
        print("     No cross-agent data yet.")
    print(f"     Cross-agent score: {cross_score:+.1f}%")

    # 3. Experiment velocity
    total_exp = conn.execute("SELECT COUNT(*) as n FROM experiments WHERE status='completed'").fetchone()["n"]
    positive_exp = conn.execute("SELECT COUNT(*) as n FROM experiments WHERE status='completed' AND rpdc_delta > 0").fetchone()["n"]
    exp_rate = (positive_exp / total_exp * 100) if total_exp > 0 else 0
    exp_score = _clamp(exp_rate - 50, -100, 100)  # 50% success = neutral

    print(f"\n  3. Experiment Velocity (20%)")
    print(f"     Total experiments:    {total_exp}")
    print(f"     Positive RPDC delta:  {positive_exp}")
    print(f"     Success rate:         {exp_rate:.0f}%")
    print(f"     Experiment score:     {exp_score:+.1f}")

    # 4. Memory compound rate
    brain_changes = []
    print(f"\n  4. Memory Compound Rate (20%)")
    for metric in AGENT_METRICS.get("brain", {}):
        meta = AGENT_METRICS["brain"][metric]
        ch = _metric_change(conn, "brain", metric, week_labels, meta["direction"])
        if ch is not None:
            brain_changes.append(ch)
            print(f"     {metric:<40s} {ch:+.1f}% {_arrow(ch,'up')}")

    memory_score = _clamp(statistics.mean(brain_changes), -100, 100) if brain_changes else 0
    if not brain_changes:
        print("     No brain data yet.")
    print(f"     Memory score: {memory_score:+.1f}%")

    conn.close()

    # Final CIS
    cis = (0.35 * individual + 0.25 * cross_score + 0.20 * exp_score + 0.20 * memory_score)
    cis = _clamp(cis, -100, 100)

    print(f"\n  {'='*72}")
    print(f"  COMPOUND INTELLIGENCE SCORE (CIS)")
    print(f"  {'='*72}")
    print(f"    Individual improvement (35%):   {individual:+6.1f}")
    print(f"    Cross-agent lift       (25%):   {cross_score:+6.1f}")
    print(f"    Experiment velocity    (20%):   {exp_score:+6.1f}")
    print(f"    Memory compound rate   (20%):   {memory_score:+6.1f}")
    print(f"    {'':34s} ------")
    print(f"    CIS                          =  {cis:+6.1f}")
    print()
    print(f"    {_cis_rating(cis)}")
    print(f"  {'='*72}\n")


def generate_report(weeks: int = 1) -> None:
    conn = _get_conn()
    now = datetime.now()
    week_labels = [(now - timedelta(weeks=i)).strftime("%Y-W%W") for i in range(weeks + 1)]
    week_labels.reverse()

    print(f"\n  {'='*72}")
    print(f"  AONXI OS  Weekly Improvement Report")
    print(f"  Generated: {now.strftime('%Y-%m-%d %H:%M')}    Period: last {weeks} week(s)")
    print(f"  {'='*72}")

    for agent in sorted(AGENT_METRICS):
        improvements, regressions = [], []
        for metric, meta in AGENT_METRICS[agent].items():
            vals = []
            for wk in week_labels:
                r = conn.execute(
                    "SELECT AVG(value) as v FROM metric_logs WHERE agent=? AND metric=? AND week_iso=?",
                    (agent, metric, wk)).fetchone()
                vals.append(r["v"])
            populated = [v for v in vals if v is not None]
            if len(populated) >= 2 and populated[0] != 0:
                pct = ((populated[-1] - populated[0]) / abs(populated[0])) * 100
                if meta["direction"] == "down":
                    pct = -pct
                (improvements if pct >= 0 else regressions).append((metric, pct))

        if not improvements and not regressions:
            continue

        print(f"\n  --- {agent.upper()} ---")
        for m, p in sorted(improvements, key=lambda x: -x[1]):
            print(f"    [+] {m:<35s} {p:+.1f}%")
        for m, p in sorted(regressions, key=lambda x: x[1]):
            print(f"    [-] {m:<35s} {p:+.1f}%")

    # Recent experiments
    recent = conn.execute("""
        SELECT * FROM experiments WHERE status = 'completed'
        ORDER BY ended_at DESC LIMIT 5
    """).fetchall()
    if recent:
        print(f"\n  --- RECENT EXPERIMENTS ---")
        for e in recent:
            sign = "+" if e['rpdc_delta'] >= 0 else ""
            print(f"    [{e['id']}] RPDC {sign}{e['rpdc_delta']:.2f}x | {e['description'][:50]}")

    conn.close()
    print(f"\n  {'='*72}\n")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(s: str) -> str:
    return s.lower().replace("-", "_").strip()

def _validate_agent(agent: str) -> None:
    if agent not in AGENT_METRICS:
        _die(f"Unknown agent '{agent}'. Valid: {', '.join(sorted(AGENT_METRICS))}")

def _snapshot_metrics(conn: sqlite3.Connection, agent: str) -> dict:
    """Get latest value for each metric of an agent."""
    snap = {}
    for metric in AGENT_METRICS.get(agent, {}):
        row = conn.execute(
            "SELECT value FROM metric_logs WHERE agent=? AND metric=? ORDER BY ts DESC LIMIT 1",
            (agent, metric)
        ).fetchone()
        if row:
            snap[metric] = row["value"]
    return snap

def _calc_rpdc(conn, agent, before=False, exp_started="") -> float:
    """Calculate RPDC for an agent."""
    if before:
        rows = conn.execute(
            "SELECT metric, AVG(value) as v FROM metric_logs WHERE agent=? AND ts < ? GROUP BY metric",
            (agent, exp_started)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT metric, AVG(value) as v FROM metric_logs WHERE agent=? AND ts >= ? GROUP BY metric",
            (agent, exp_started)
        ).fetchall()

    latest = {r["metric"]: r["v"] for r in rows}
    revenue = latest.get("revenue_generated", _estimate_revenue(agent, latest))
    human_mins = latest.get("human_qc_minutes", 10)
    human_cost = (human_mins / 60) * DEFAULT_HUMAN_HOUR_COST
    queries = sum(v for k, v in latest.items() if k in ("emails_sent", "tickets_resolved", "resumes_screened", "tests_generated"))
    inference_cost = max(queries, 1) * DEFAULT_INFERENCE_COST_PER_QUERY
    total_cost = inference_cost + human_cost
    return revenue / total_cost if total_cost > 0 else 0

def _estimate_revenue(agent: str, metrics: dict) -> float:
    """Estimate revenue contribution for agents that don't directly generate revenue."""
    if agent == "outreach":
        return metrics.get("revenue_generated", metrics.get("meetings_booked", 0) * 500)
    elif agent == "sales":
        return metrics.get("pipeline_value", 0) * metrics.get("close_rate", 0) / 100
    elif agent == "hr":
        return metrics.get("resumes_screened", 0) * 50  # $50 value per screen
    elif agent == "it_helpdesk":
        return metrics.get("tickets_resolved", 0) * 25   # $25 per ticket
    elif agent == "support":
        return metrics.get("churn_prevented", 0) * 2000  # $2000 per retained client
    elif agent == "finance":
        return metrics.get("invoices_processed", 0) * 10  # $10 per invoice
    elif agent == "qa":
        return metrics.get("bugs_found", 0) * 200         # $200 per bug caught early
    elif agent == "daily_fleet":
        return metrics.get("emails_delivered", 0) * 0.10   # $0.10 per delivered
    return 0

def _show_ripple(conn, agent: str, deltas: dict) -> None:
    """Show cross-agent ripple effect from an experiment."""
    found = False
    for src_ag, src_m, tgt_ag, tgt_m, reason in CAUSAL_LINKS:
        if src_ag == agent and src_m in deltas:
            d = deltas[src_m]
            if d["change_pct"] > 0:
                found = True
                print(f"    {agent}.{src_m} ({d['change_pct']:+.1f}%) -> expect {tgt_ag}.{tgt_m} to improve")
                print(f"      Reason: {reason}")
    if not found:
        print("    No measurable cross-agent ripple from this experiment.")

def _metric_change(conn, agent, metric, week_labels, direction) -> float | None:
    vals = []
    for wk in week_labels:
        r = conn.execute(
            "SELECT AVG(value) as v FROM metric_logs WHERE agent=? AND metric=? AND week_iso=?",
            (agent, metric, wk)).fetchone()
        if r["v"] is not None:
            vals.append(r["v"])
    if len(vals) < 2 or vals[0] == 0:
        return None
    pct = ((vals[-1] - vals[0]) / abs(vals[0])) * 100
    return -pct if direction == "down" else pct

def _safe_pct(old, new):
    return ((new - old) / abs(old)) * 100 if old != 0 else 0

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))

def _arrow(value, direction):
    if direction == "down":
        value = -value
    if value > 5: return "^^"
    elif value > 0: return "^"
    elif value == 0: return "--"
    elif value > -5: return "v"
    else: return "vv"

def _sparkline(values):
    if not values: return ""
    blocks = " _.:oO#@"
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1.0
    step = max(1, len(values) // 40)
    return "".join(blocks[int((v-mn)/rng*(len(blocks)-1))] for v in values[::step])

def _bar(pct, width=30):
    clamped = _clamp(pct, -100, 100)
    mid = width // 2
    fill = int(abs(clamped) / 100 * mid)
    if clamped >= 0:
        return f"[{' '*mid}|{'#'*fill}{' '*(mid-fill)}]"
    else:
        return f"[{' '*(mid-fill)}{'#'*fill}|{' '*mid}]"

def _cis_rating(score):
    if score >= 20: return "Rating: ACCELERATING -- agents are compounding each other's intelligence."
    elif score >= 5: return "Rating: IMPROVING -- steady gains across the board."
    elif score >= -5: return "Rating: STABLE -- no significant change."
    elif score >= -20: return "Rating: DECLINING -- investigate regressions."
    else: return "Rating: CRITICAL -- major regressions detected."


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

USAGE = textwrap.dedent("""\
    AONXI OS — Agent Evaluation & Experiment Attribution Engine

    Commands:
      experiment start <agent> "<description>"    Start an experiment (snapshots baseline)
      experiment end <exp_id> "<conclusion>"       End experiment (calculate attribution)
      experiments [--agent <name>]                 List all experiments
      attribution <exp_id>                         Full attribution chain for experiment
      leaderboard                                  Rank experiments by RPDC impact

      log <agent> <metric> <value> [--experiment <id>]   Log a metric
      rpdc [<agent>]                               Revenue Per Dollar of Cost
      trend <agent> [--days N]                     Metric trends with sparklines
      dashboard                                    Week-over-week dashboard
      compound-score [--weeks N]                   Compound Intelligence Score (CIS)
      report [--weeks N]                           Weekly improvement report
      agents                                       List all agents and metrics

    The ONE metric: RPDC = Revenue / (Inference Cost + Human QC Cost)
    Superior to Benchspan: we benchmark OUTCOMES, not models.
""")


def _parse_opt(args, flag, default):
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            try: return type(default)(args[idx + 1])
            except: _die(f"Invalid value for {flag}")
        else: _die(f"{flag} requires a value")
    return default

def _die(msg):
    print(f"  ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if not args:
        print(USAGE)
        sys.exit(0)

    cmd = args[0].lower()

    if cmd == "experiment":
        if len(args) < 2:
            _die("Usage: experiment start|end ...")
        sub = args[1].lower()
        if sub == "start":
            if len(args) < 4:
                _die('Usage: experiment start <agent> "<description>" ["<hypothesis>"]')
            agent, desc = args[2], args[3]
            hyp = args[4] if len(args) > 4 else ""
            experiment_start(agent, desc, hyp)
        elif sub == "end":
            if len(args) < 3:
                _die('Usage: experiment end <exp_id> ["<conclusion>"]')
            exp_id = args[2]
            conclusion = args[3] if len(args) > 3 else ""
            experiment_end(exp_id, conclusion)
        else:
            _die(f"Unknown experiment subcommand: {sub}")

    elif cmd == "experiments":
        agent = _parse_opt(args, "--agent", "") or None
        list_experiments(agent)

    elif cmd == "attribution":
        if len(args) < 2: _die("Usage: attribution <exp_id>")
        show_attribution(args[1])

    elif cmd == "leaderboard":
        show_leaderboard()

    elif cmd == "log":
        if len(args) < 4: _die("Usage: log <agent> <metric> <value> [--experiment <id>]")
        try: value = float(args[3])
        except ValueError: _die(f"Value must be a number, got '{args[3]}'")
        exp_id = _parse_opt(args, "--experiment", "") or None
        log_metric(args[1], args[2], value, exp_id)

    elif cmd == "rpdc":
        agent = args[1] if len(args) > 1 else None
        show_rpdc(agent)

    elif cmd == "trend":
        if len(args) < 2: _die("Usage: trend <agent> [--days N]")
        show_trend(args[1], _parse_opt(args, "--days", 30))

    elif cmd == "dashboard":
        show_dashboard()

    elif cmd in ("compound-score", "compound_score", "cis"):
        compound_score(_parse_opt(args, "--weeks", 4))

    elif cmd == "report":
        generate_report(_parse_opt(args, "--weeks", 1))

    elif cmd == "agents":
        print(f"\n  AONXI OS Agent Registry ({len(AGENT_METRICS)} agents, {sum(len(m) for m in AGENT_METRICS.values())} metrics)\n")
        for agent in sorted(AGENT_METRICS):
            print(f"  {agent}")
            for metric, meta in sorted(AGENT_METRICS[agent].items()):
                w = meta.get("revenue_weight", 0)
                print(f"    {metric:<40s} {meta['direction']:>4s}  {meta['unit']:<6s}  weight: {w:.2f}")
            print()

    else:
        _die(f"Unknown command '{cmd}'.\n{USAGE}")


if __name__ == "__main__":
    main()
