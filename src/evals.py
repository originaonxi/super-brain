#!/usr/bin/env python3
from __future__ import annotations
"""
AONXI OS / Super Brain - Agent Evaluation & Metrics System

Answers the question: "How do we know each agent is getting better day by day?"

Tracks per-agent metrics, calculates improvement trends, and produces a
compound intelligence score that measures how agents improve *each other*.

Usage:
    python3 evals.py log <agent> <metric> <value>
    python3 evals.py trend <agent> [--days N]
    python3 evals.py dashboard
    python3 evals.py report [--weeks N]
    python3 evals.py compound-score [--weeks N]
"""

import json
import math
import os
import sqlite3
import statistics
import sys
import textwrap
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = Path.home() / "super-brain" / "data" / "evals.db"

# Canonical agent definitions.  Each metric has:
#   direction: "up" means higher is better, "down" means lower is better
#   unit: display label
AGENT_METRICS: dict[str, dict[str, dict]] = {
    "outreach": {
        "leads_found":       {"direction": "up",   "unit": "count"},
        "emails_sent":       {"direction": "up",   "unit": "count"},
        "reply_rate":        {"direction": "up",   "unit": "%"},
        "meetings_booked":   {"direction": "up",   "unit": "count"},
        "revenue_generated": {"direction": "up",   "unit": "$"},
    },
    "hr": {
        "resumes_screened":     {"direction": "up",   "unit": "count"},
        "time_per_hire":        {"direction": "down", "unit": "days"},
        "offer_acceptance_rate": {"direction": "up",  "unit": "%"},
    },
    "it_helpdesk": {
        "tickets_resolved":    {"direction": "up",   "unit": "count"},
        "auto_resolve_rate":   {"direction": "up",   "unit": "%"},
        "avg_resolution_time": {"direction": "down", "unit": "min"},
    },
    "sales": {
        "pipeline_value": {"direction": "up",   "unit": "$"},
        "close_rate":     {"direction": "up",   "unit": "%"},
        "avg_deal_size":  {"direction": "up",   "unit": "$"},
    },
    "support": {
        "response_time_seconds": {"direction": "down", "unit": "sec"},
        "resolution_rate":       {"direction": "up",   "unit": "%"},
        "csat_score":            {"direction": "up",   "unit": "/5"},
    },
    "finance": {
        "invoices_processed":  {"direction": "up",   "unit": "count"},
        "forecast_accuracy":   {"direction": "up",   "unit": "%"},
        "anomalies_detected":  {"direction": "up",   "unit": "count"},
    },
    "daily_fleet": {
        "emails_delivered": {"direction": "up", "unit": "count"},
        "open_rate":        {"direction": "up", "unit": "%"},
        "click_rate":       {"direction": "up", "unit": "%"},
    },
    "qa": {
        "tests_generated":    {"direction": "up",   "unit": "count"},
        "tests_passed":       {"direction": "up",   "unit": "count"},
        "bugs_found":         {"direction": "up",   "unit": "count"},
        "false_positive_rate": {"direction": "down", "unit": "%"},
    },
    "brain": {
        "memories_count":                {"direction": "up", "unit": "count"},
        "search_relevance_avg":          {"direction": "up", "unit": "/1.0"},
        "cross_repo_patterns_detected":  {"direction": "up", "unit": "count"},
    },
}

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metric_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            agent      TEXT    NOT NULL,
            metric     TEXT    NOT NULL,
            value      REAL    NOT NULL,
            ts         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime')),
            week_iso   TEXT    NOT NULL DEFAULT (strftime('%Y-W%W', 'now', 'localtime'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_metric_ts
        ON metric_logs (agent, metric, ts)
    """)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def log_metric(agent: str, metric: str, value: float) -> None:
    agent = agent.lower().replace("-", "_")
    metric = metric.lower().replace("-", "_")

    if agent not in AGENT_METRICS:
        _die(f"Unknown agent '{agent}'. Valid: {', '.join(sorted(AGENT_METRICS))}")
    if metric not in AGENT_METRICS[agent]:
        valid = ", ".join(sorted(AGENT_METRICS[agent]))
        _die(f"Unknown metric '{metric}' for agent '{agent}'. Valid: {valid}")

    conn = _get_conn()
    now = datetime.now()
    conn.execute(
        "INSERT INTO metric_logs (agent, metric, value, ts, week_iso) VALUES (?, ?, ?, ?, ?)",
        (agent, metric, value, now.strftime("%Y-%m-%dT%H:%M:%S"), now.strftime("%Y-W%W")),
    )
    conn.commit()
    conn.close()
    meta = AGENT_METRICS[agent][metric]
    print(f"  Logged  {agent}.{metric} = {value} {meta['unit']}")


def get_trend(agent: str, days: int = 30) -> dict[str, list[dict]]:
    """Return {metric: [{ts, value}, ...]} for the given agent over `days` days."""
    agent = agent.lower().replace("-", "_")
    if agent not in AGENT_METRICS:
        _die(f"Unknown agent '{agent}'.")

    conn = _get_conn()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")
    rows = conn.execute(
        "SELECT metric, ts, value FROM metric_logs WHERE agent = ? AND ts >= ? ORDER BY ts",
        (agent, cutoff),
    ).fetchall()
    conn.close()

    result: dict[str, list[dict]] = {}
    for metric, ts, value in rows:
        result.setdefault(metric, []).append({"ts": ts, "value": value})
    return result


def show_trend(agent: str, days: int = 30) -> None:
    trend = get_trend(agent, days)
    if not trend:
        print(f"  No data for agent '{agent}' in the last {days} days.")
        return

    print(f"\n  Trend for '{agent}' (last {days} days)")
    print(f"  {'='*60}")
    for metric, points in sorted(trend.items()):
        meta = AGENT_METRICS.get(agent, {}).get(metric, {})
        direction = meta.get("direction", "up")
        unit = meta.get("unit", "")
        values = [p["value"] for p in points]

        current = values[-1]
        first = values[0]
        change_pct = _safe_pct_change(first, current)
        arrow = _arrow(change_pct, direction)
        sparkline = _sparkline(values)

        print(f"\n  {metric} ({unit}, want {direction})")
        print(f"    {sparkline}")
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
        metrics = AGENT_METRICS[agent]
        scores: list[float] = []

        for metric, meta in metrics.items():
            curr_rows = conn.execute(
                "SELECT AVG(value) FROM metric_logs WHERE agent=? AND metric=? AND week_iso=?",
                (agent, metric, this_week),
            ).fetchone()
            prev_rows = conn.execute(
                "SELECT AVG(value) FROM metric_logs WHERE agent=? AND metric=? AND week_iso=?",
                (agent, metric, prev_week),
            ).fetchone()

            curr_val = curr_rows[0] if curr_rows else None
            prev_val = prev_rows[0] if prev_rows else None
            if curr_val is not None and prev_val is not None and prev_val != 0:
                pct = ((curr_val - prev_val) / abs(prev_val)) * 100
                if meta["direction"] == "down":
                    pct = -pct  # flip so positive = improvement
                scores.append(pct)

        if not scores:
            continue

        any_data = True
        avg_improvement = statistics.mean(scores)
        arrow = _arrow(avg_improvement, "up")
        bar = _bar(avg_improvement, width=30)

        print(f"\n  {agent:<16s} {avg_improvement:+6.1f}% WoW  {arrow}  {bar}")
        for metric, meta in sorted(metrics.items()):
            curr_rows = conn.execute(
                "SELECT AVG(value) FROM metric_logs WHERE agent=? AND metric=? AND week_iso=?",
                (agent, metric, this_week),
            ).fetchone()
            curr_val = curr_rows[0] if curr_rows else None
            if curr_val is not None:
                print(f"    {metric:<30s} {curr_val:>10.2f} {meta['unit']}")

    conn.close()
    if not any_data:
        print("\n  No week-over-week data yet. Log metrics for at least 2 weeks.")
    print(f"\n  {'='*72}\n")


def generate_report(weeks: int = 1) -> None:
    conn = _get_conn()
    now = datetime.now()

    print(f"\n  {'='*72}")
    print(f"  AONXI OS  Weekly Improvement Report")
    print(f"  Generated: {now.strftime('%Y-%m-%d %H:%M')}    Period: last {weeks} week(s)")
    print(f"  {'='*72}")

    week_labels = []
    for i in range(weeks + 1):
        dt = now - timedelta(weeks=i)
        week_labels.append(dt.strftime("%Y-W%W"))
    week_labels.reverse()

    for agent in sorted(AGENT_METRICS):
        metrics = AGENT_METRICS[agent]
        agent_has_data = False

        improvements: list[tuple[str, float]] = []
        regressions: list[tuple[str, float]] = []

        for metric, meta in metrics.items():
            week_avgs: list[float | None] = []
            for wk in week_labels:
                row = conn.execute(
                    "SELECT AVG(value) FROM metric_logs WHERE agent=? AND metric=? AND week_iso=?",
                    (agent, metric, wk),
                ).fetchone()
                week_avgs.append(row[0] if row else None)

            first_val = next((v for v in week_avgs if v is not None), None)
            last_val = next((v for v in reversed(week_avgs) if v is not None), None)
            if first_val is not None and last_val is not None and first_val != 0:
                pct = ((last_val - first_val) / abs(first_val)) * 100
                if meta["direction"] == "down":
                    pct = -pct
                agent_has_data = True
                if pct >= 0:
                    improvements.append((metric, pct))
                else:
                    regressions.append((metric, pct))

        if not agent_has_data:
            continue

        print(f"\n  --- {agent.upper()} ---")
        if improvements:
            improvements.sort(key=lambda x: -x[1])
            for m, p in improvements:
                print(f"    [+] {m:<30s} {p:+.1f}%")
        if regressions:
            regressions.sort(key=lambda x: x[1])
            for m, p in regressions:
                print(f"    [-] {m:<30s} {p:+.1f}%")

    conn.close()
    print(f"\n  {'='*72}\n")


def compound_score(weeks: int = 4) -> None:
    """
    Compound Intelligence Score (CIS).

    Three components:
      1. Individual improvement: weighted average of each agent's week-over-week
         improvement across all its metrics.
      2. Cross-agent lift: correlation between improvement in one agent and
         subsequent improvement in related agents (e.g. outreach leads ->
         sales pipeline, qa bugs_found -> support resolution_rate).
      3. Memory compound rate: is the brain's search relevance and pattern
         detection accelerating?

    Final score = 0.4 * individual + 0.3 * cross_agent + 0.3 * memory
    Scale: -100 (catastrophic regression) to +100 (exponential improvement).
    """
    conn = _get_conn()
    now = datetime.now()

    print(f"\n  {'='*72}")
    print(f"  AONXI OS  Compound Intelligence Score (CIS)")
    print(f"  Period: last {weeks} weeks ending {now.strftime('%Y-%m-%d')}")
    print(f"  {'='*72}")

    # --- 1. Individual improvement per agent ---
    agent_improvements: dict[str, float] = {}
    week_labels = [(now - timedelta(weeks=i)).strftime("%Y-W%W") for i in range(weeks + 1)]
    week_labels.reverse()

    for agent, metrics in AGENT_METRICS.items():
        metric_changes: list[float] = []
        for metric, meta in metrics.items():
            weekly_vals: list[float | None] = []
            for wk in week_labels:
                row = conn.execute(
                    "SELECT AVG(value) FROM metric_logs WHERE agent=? AND metric=? AND week_iso=?",
                    (agent, metric, wk),
                ).fetchone()
                weekly_vals.append(row[0] if row else None)

            # compute compound weekly change
            populated = [(i, v) for i, v in enumerate(weekly_vals) if v is not None]
            if len(populated) >= 2:
                first_i, first_v = populated[0]
                last_i, last_v = populated[-1]
                span = last_i - first_i
                if first_v != 0 and span > 0:
                    total_change = (last_v - first_v) / abs(first_v) * 100
                    if meta["direction"] == "down":
                        total_change = -total_change
                    metric_changes.append(total_change)

        if metric_changes:
            agent_improvements[agent] = statistics.mean(metric_changes)

    if agent_improvements:
        individual_score = _clamp(statistics.mean(agent_improvements.values()), -100, 100)
    else:
        individual_score = 0.0

    print(f"\n  1. Individual Agent Improvement")
    if agent_improvements:
        for agent in sorted(agent_improvements):
            val = agent_improvements[agent]
            print(f"     {agent:<16s} {val:+6.1f}%  {_arrow(val, 'up')}")
        print(f"     {'':16s} ------")
        print(f"     {'Mean':<16s} {individual_score:+6.1f}%")
    else:
        print("     No data available.")

    # --- 2. Cross-agent lift ---
    # Defined causal links: (source_agent, source_metric) -> (target_agent, target_metric)
    CAUSAL_LINKS = [
        ("outreach", "leads_found",        "sales",    "pipeline_value"),
        ("outreach", "meetings_booked",    "sales",    "close_rate"),
        ("qa",       "bugs_found",         "support",  "resolution_rate"),
        ("qa",       "tests_passed",       "it_helpdesk", "auto_resolve_rate"),
        ("brain",    "search_relevance_avg","outreach", "reply_rate"),
        ("brain",    "cross_repo_patterns_detected", "qa", "bugs_found"),
        ("hr",       "time_per_hire",       "it_helpdesk", "tickets_resolved"),
        ("daily_fleet", "open_rate",        "outreach",    "reply_rate"),
        ("finance",  "forecast_accuracy",  "sales",    "pipeline_value"),
    ]

    cross_scores: list[float] = []
    print(f"\n  2. Cross-Agent Lift (causal links)")
    for src_agent, src_metric, tgt_agent, tgt_metric in CAUSAL_LINKS:
        src_change = _metric_change(conn, src_agent, src_metric, week_labels,
                                    AGENT_METRICS[src_agent][src_metric]["direction"])
        tgt_change = _metric_change(conn, tgt_agent, tgt_metric, week_labels,
                                    AGENT_METRICS[tgt_agent][tgt_metric]["direction"])
        if src_change is not None and tgt_change is not None:
            # If source improved and target also improved, that's a positive signal
            if src_change > 0 and tgt_change > 0:
                lift = min(src_change, tgt_change)  # conservative estimate
            elif src_change > 0 and tgt_change <= 0:
                lift = tgt_change * 0.5  # source improved but target didn't -- partial penalty
            else:
                lift = 0.0
            cross_scores.append(lift)
            arrow = _arrow(lift, "up")
            print(f"     {src_agent}.{src_metric} -> {tgt_agent}.{tgt_metric}: {lift:+.1f}% {arrow}")

    if cross_scores:
        cross_agent_score = _clamp(statistics.mean(cross_scores), -100, 100)
    else:
        cross_agent_score = 0.0
        print("     No cross-agent data available yet.")
    print(f"     Cross-agent lift score: {cross_agent_score:+.1f}%")

    # --- 3. Memory compound rate ---
    brain_metrics = ["memories_count", "search_relevance_avg", "cross_repo_patterns_detected"]
    brain_changes: list[float] = []
    print(f"\n  3. Memory Compound Rate (brain)")
    for metric in brain_metrics:
        change = _metric_change(conn, "brain", metric, week_labels,
                                AGENT_METRICS["brain"][metric]["direction"])
        if change is not None:
            brain_changes.append(change)
            print(f"     {metric:<40s} {change:+.1f}%  {_arrow(change, 'up')}")

    if brain_changes:
        # Weight search_relevance higher -- it's the quality signal
        memory_score = _clamp(statistics.mean(brain_changes), -100, 100)
    else:
        memory_score = 0.0
        print("     No brain data available yet.")
    print(f"     Memory compound score: {memory_score:+.1f}%")

    conn.close()

    # --- Final CIS ---
    cis = 0.4 * individual_score + 0.3 * cross_agent_score + 0.3 * memory_score
    cis = _clamp(cis, -100, 100)

    print(f"\n  {'='*72}")
    print(f"  COMPOUND INTELLIGENCE SCORE (CIS)")
    print(f"  {'='*72}")
    print(f"    Individual improvement (40%):   {individual_score:+6.1f}")
    print(f"    Cross-agent lift       (30%):   {cross_agent_score:+6.1f}")
    print(f"    Memory compound rate   (30%):   {memory_score:+6.1f}")
    print(f"    {'':34s} ------")
    print(f"    CIS                          =  {cis:+6.1f}")
    print()
    print(f"    {_cis_rating(cis)}")
    print(f"  {'='*72}\n")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _metric_change(
    conn: sqlite3.Connection,
    agent: str,
    metric: str,
    week_labels: list[str],
    direction: str,
) -> float | None:
    """Compute % improvement for one metric across the given weeks."""
    vals: list[tuple[int, float]] = []
    for i, wk in enumerate(week_labels):
        row = conn.execute(
            "SELECT AVG(value) FROM metric_logs WHERE agent=? AND metric=? AND week_iso=?",
            (agent, metric, wk),
        ).fetchone()
        if row[0] is not None:
            vals.append((i, row[0]))
    if len(vals) < 2:
        return None
    first_v = vals[0][1]
    last_v = vals[-1][1]
    if first_v == 0:
        return None
    pct = ((last_v - first_v) / abs(first_v)) * 100
    if direction == "down":
        pct = -pct
    return pct


def _safe_pct_change(old: float, new: float) -> float:
    if old == 0:
        return 0.0
    return ((new - old) / abs(old)) * 100


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _arrow(value: float, direction: str) -> str:
    """Return an ASCII arrow indicating good/bad direction."""
    if direction == "down":
        value = -value
    if value > 5:
        return "^^"
    elif value > 0:
        return "^"
    elif value == 0:
        return "--"
    elif value > -5:
        return "v"
    else:
        return "vv"


def _sparkline(values: list[float]) -> str:
    """Render a tiny ASCII sparkline."""
    if not values:
        return ""
    blocks = " _.:oO#@"
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1.0
    chars = []
    # sample at most 40 points
    step = max(1, len(values) // 40)
    sampled = values[::step]
    for v in sampled:
        idx = int((v - mn) / rng * (len(blocks) - 1))
        chars.append(blocks[idx])
    return "".join(chars)


def _bar(pct: float, width: int = 30) -> str:
    """Render a horizontal bar for a percentage in [-100, 100]."""
    clamped = _clamp(pct, -100, 100)
    mid = width // 2
    fill = int(abs(clamped) / 100 * mid)
    if clamped >= 0:
        left = " " * mid
        right = "#" * fill + " " * (mid - fill)
    else:
        left = " " * (mid - fill) + "#" * fill
        right = " " * mid
    return f"[{left}|{right}]"


def _cis_rating(score: float) -> str:
    if score >= 20:
        return "Rating: ACCELERATING -- agents are compounding each other's intelligence."
    elif score >= 5:
        return "Rating: IMPROVING -- steady gains across the board."
    elif score >= -5:
        return "Rating: STABLE -- no significant change."
    elif score >= -20:
        return "Rating: DECLINING -- investigate regressions."
    else:
        return "Rating: CRITICAL -- major regressions detected, intervention needed."


def _die(msg: str) -> None:
    print(f"  ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

USAGE = textwrap.dedent("""\
    Usage:
      python3 evals.py log <agent> <metric> <value>   Log a metric data point
      python3 evals.py trend <agent> [--days N]        Show metric trends (default 30 days)
      python3 evals.py dashboard                       Week-over-week dashboard
      python3 evals.py report [--weeks N]              Weekly improvement report
      python3 evals.py compound-score [--weeks N]      Compound Intelligence Score
      python3 evals.py agents                          List all agents and their metrics

    Agents: """ + ", ".join(sorted(AGENT_METRICS)))


def _parse_optional_int(args: list[str], flag: str, default: int) -> int:
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            try:
                return int(args[idx + 1])
            except ValueError:
                _die(f"Invalid value for {flag}")
        else:
            _die(f"{flag} requires a value")
    return default


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(USAGE)
        sys.exit(0)

    cmd = args[0].lower()

    if cmd == "log":
        if len(args) < 4:
            _die("Usage: evals.py log <agent> <metric> <value>")
        agent, metric = args[1], args[2]
        try:
            value = float(args[3])
        except ValueError:
            _die(f"Value must be a number, got '{args[3]}'")
        log_metric(agent, metric, value)

    elif cmd == "trend":
        if len(args) < 2:
            _die("Usage: evals.py trend <agent> [--days N]")
        agent = args[1]
        days = _parse_optional_int(args, "--days", 30)
        show_trend(agent, days)

    elif cmd == "dashboard":
        show_dashboard()

    elif cmd == "report":
        weeks = _parse_optional_int(args, "--weeks", 1)
        generate_report(weeks)

    elif cmd in ("compound-score", "compound_score", "cis"):
        weeks = _parse_optional_int(args, "--weeks", 4)
        compound_score(weeks)

    elif cmd == "agents":
        print(f"\n  AONXI OS Agent Registry ({len(AGENT_METRICS)} agents)\n")
        for agent in sorted(AGENT_METRICS):
            print(f"  {agent}")
            for metric, meta in sorted(AGENT_METRICS[agent].items()):
                print(f"    {metric:<40s} {meta['direction']:>4s}  {meta['unit']}")
            print()

    else:
        _die(f"Unknown command '{cmd}'.\n{USAGE}")


if __name__ == "__main__":
    main()
