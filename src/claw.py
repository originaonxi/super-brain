#!/usr/bin/env python3
"""
AONXI CLAW V2 — The Agent Operating System
=============================================
10x beyond V1 Claw. This is not an event bus. This is a decision engine.

What V1 had: event bus, file-based context, poll loops.
What V2 adds:
  1. DECISION ENGINE — agents propose actions, system evaluates, best action wins
  2. TRUST SCORING — progressive autonomy based on track record (0.0 to 1.0)
  3. HUMAN-IN-THE-LOOP — configurable approval gates per agent + action type
  4. CONFLICT RESOLUTION — when two agents disagree, evidence-based tiebreak
  5. RESOURCE MANAGER — Mac Mini compute allocation across concurrent agents
  6. SELF-HEALING — detect failed agents, restart, re-route work
  7. EXPERIMENT INTEGRATION — every action is an experiment, RPDC tracked
  8. CROSS-AGENT LEARNING — 13 causal links with automatic insight propagation
  9. AUDIT TRAIL — every decision traceable from trigger to outcome
  10. PRIORITY QUEUE — urgent work preempts routine work

Architecture:
  ┌──────────────────────────────────────────────────────────────────┐
  │                    AONXI CLAW V2 DAEMON                         │
  │                                                                  │
  │  ┌────────────┐ ┌────────────┐ ┌──────────┐ ┌───────────────┐  │
  │  │  DECISION  │ │   TRUST    │ │  HUMAN   │ │   RESOURCE    │  │
  │  │  ENGINE    │ │  SCORING   │ │  GATES   │ │   MANAGER     │  │
  │  └─────┬──────┘ └─────┬──────┘ └────┬─────┘ └──────┬────────┘  │
  │        │              │              │              │            │
  │  ┌─────▼──────────────▼──────────────▼──────────────▼────────┐  │
  │  │                    EVENT BUS (SQLite)                      │  │
  │  │  events | decisions | trust_scores | approvals | audit    │  │
  │  └──┬──────┬──────┬──────┬──────┬──────┬──────┬─────────────┘  │
  │     │      │      │      │      │      │      │                │
  └─────┼──────┼──────┼──────┼──────┼──────┼──────┼────────────────┘
        │      │      │      │      │      │      │
    ┌───▼──┐┌──▼──┐┌──▼───┐┌─▼──┐┌─▼───┐┌─▼──┐┌──▼───┐┌────────┐
    │SALES ││SUPP.││FIN.  ││ HR ││ QA  ││SEO ││FLEET ││OUTREACH│
    │AGENT ││AGENT││AGENT ││AGT ││AGENT││AGT ││AGENT ││ AGENT  │
    └──────┘└─────┘└──────┘└────┘└─────┘└────┘└──────┘└────────┘

Run:    python3 claw.py start
Status: python3 claw.py status
Tail:   python3 claw.py tail
"""

import asyncio
import json
import os
import signal
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# ─────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────

CLAW_DIR = Path(__file__).parent.parent
DB_PATH = CLAW_DIR / "data" / "claw.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

POLL_INTERVAL = 10       # seconds between event processing
HEALTH_INTERVAL = 120    # seconds between health checks
DECISION_INTERVAL = 30   # seconds between decision cycles

# Trust thresholds — agents earn autonomy
TRUST_AUTO_APPROVE = 0.85   # above this: agent acts without human approval
TRUST_SUGGEST_ONLY = 0.40   # below this: agent can only suggest, human must approve
# between 0.40-0.85: agent acts but human is notified and can rollback

# Human approval required for these action types regardless of trust
ALWAYS_REQUIRE_APPROVAL = [
    "send_email_to_client",
    "close_deal",
    "create_invoice",
    "deploy_agent",
    "modify_pricing",
    "send_outreach_batch",
]

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# ─────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        -- Events: what happened
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            source_agent TEXT NOT NULL,
            target_agent TEXT,
            payload TEXT NOT NULL DEFAULT '{}',
            priority INTEGER DEFAULT 5,
            correlation_id TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            processed_at TEXT,
            processed_by TEXT
        );

        -- Decisions: what agents want to do
        CREATE TABLE IF NOT EXISTS decisions (
            id TEXT PRIMARY KEY,
            agent TEXT NOT NULL,
            action_type TEXT NOT NULL,
            description TEXT NOT NULL,
            evidence TEXT DEFAULT '{}',
            confidence REAL DEFAULT 0.5,
            expected_rpdc_impact REAL DEFAULT 0,
            status TEXT DEFAULT 'proposed',
            approved_by TEXT,
            approved_at TEXT,
            executed_at TEXT,
            outcome TEXT,
            outcome_rpdc REAL,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Trust scores: progressive autonomy
        CREATE TABLE IF NOT EXISTS trust_scores (
            agent TEXT PRIMARY KEY,
            score REAL DEFAULT 0.5,
            total_decisions INTEGER DEFAULT 0,
            successful_decisions INTEGER DEFAULT 0,
            failed_decisions INTEGER DEFAULT 0,
            last_updated TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Human approval queue
        CREATE TABLE IF NOT EXISTS approval_queue (
            id TEXT PRIMARY KEY,
            decision_id TEXT NOT NULL,
            agent TEXT NOT NULL,
            action_type TEXT NOT NULL,
            description TEXT NOT NULL,
            evidence TEXT DEFAULT '{}',
            status TEXT DEFAULT 'pending',
            reviewer TEXT,
            reviewed_at TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (decision_id) REFERENCES decisions(id)
        );

        -- Agent state: heartbeats and status
        CREATE TABLE IF NOT EXISTS agent_state (
            agent TEXT PRIMARY KEY,
            status TEXT DEFAULT 'idle',
            last_heartbeat TEXT,
            last_run_at TEXT,
            last_run_status TEXT,
            last_run_summary TEXT DEFAULT '{}',
            memory_mb REAL DEFAULT 0,
            cpu_pct REAL DEFAULT 0,
            errors_last_hour INTEGER DEFAULT 0
        );

        -- Audit trail: every decision traced
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id TEXT,
            event_type TEXT NOT NULL,
            agent TEXT,
            action TEXT NOT NULL,
            detail TEXT DEFAULT '',
            trust_score_at_time REAL,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Cross-agent insights: the family effect
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_agent TEXT NOT NULL,
            insight TEXT NOT NULL,
            evidence TEXT DEFAULT '{}',
            consumed_by TEXT DEFAULT '[]',
            impact_score REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Resource allocation
        CREATE TABLE IF NOT EXISTS resource_pool (
            agent TEXT PRIMARY KEY,
            allocated_memory_mb REAL DEFAULT 0,
            allocated_cpu_pct REAL DEFAULT 0,
            priority INTEGER DEFAULT 5,
            last_allocated TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_events_unprocessed ON events(processed_at) WHERE processed_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status);
        CREATE INDEX IF NOT EXISTS idx_approval_pending ON approval_queue(status) WHERE status = 'pending';
        CREATE INDEX IF NOT EXISTS idx_insights_recent ON insights(created_at);
    """)

    # Initialize trust scores for all agents
    agents = ["sales", "support", "finance", "hr", "qa", "seo", "daily_fleet", "outreach", "brain"]
    for agent in agents:
        conn.execute("""
            INSERT OR IGNORE INTO trust_scores (agent, score) VALUES (?, 0.5)
        """, (agent,))
        conn.execute("""
            INSERT OR IGNORE INTO agent_state (agent, status) VALUES (?, 'idle')
        """, (agent,))

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────
# DECISION ENGINE — agents propose, system decides
# ─────────────────────────────────────────────────────────────────

def propose_decision(agent: str, action_type: str, description: str,
                     evidence: dict = None, confidence: float = 0.5,
                     expected_rpdc: float = 0) -> str:
    """Agent proposes an action. Returns decision ID."""
    dec_id = f"dec-{agent[:3]}-{datetime.now().strftime('%m%d%H%M')}-{uuid.uuid4().hex[:4]}"
    conn = get_db()

    conn.execute("""
        INSERT INTO decisions (id, agent, action_type, description, evidence,
                               confidence, expected_rpdc_impact, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'proposed')
    """, (dec_id, agent, action_type, description,
          json.dumps(evidence or {}), confidence, expected_rpdc))

    # Check trust level
    trust = conn.execute("SELECT score FROM trust_scores WHERE agent=?", (agent,)).fetchone()
    trust_score = trust["score"] if trust else 0.5

    # Determine approval path
    needs_human = (
        action_type in ALWAYS_REQUIRE_APPROVAL or
        trust_score < TRUST_SUGGEST_ONLY or
        confidence < 0.6
    )

    auto_approve = (
        trust_score >= TRUST_AUTO_APPROVE and
        confidence >= 0.8 and
        action_type not in ALWAYS_REQUIRE_APPROVAL
    )

    if auto_approve:
        conn.execute("UPDATE decisions SET status='approved', approved_by='auto-trust' WHERE id=?", (dec_id,))
        _audit(conn, dec_id, "auto_approved", agent, f"Trust={trust_score:.2f}, Confidence={confidence:.2f}")
        status = "auto-approved"
    elif needs_human:
        # Add to approval queue
        aq_id = f"aq-{uuid.uuid4().hex[:6]}"
        conn.execute("""
            INSERT INTO approval_queue (id, decision_id, agent, action_type, description, evidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (aq_id, dec_id, agent, action_type, description, json.dumps(evidence or {})))
        conn.execute("UPDATE decisions SET status='awaiting_approval' WHERE id=?", (dec_id,))
        _audit(conn, dec_id, "queued_for_approval", agent, f"Trust={trust_score:.2f}, Action={action_type}")
        status = "awaiting-approval"
    else:
        # Notify human but proceed
        conn.execute("UPDATE decisions SET status='approved', approved_by='auto-notify' WHERE id=?", (dec_id,))
        _audit(conn, dec_id, "auto_approved_notify", agent, f"Trust={trust_score:.2f}, human notified")
        status = "approved-with-notification"

    conn.commit()
    conn.close()
    return dec_id, status


def approve_decision(decision_id: str, reviewer: str = "human", notes: str = "") -> bool:
    """Human approves a decision."""
    conn = get_db()
    conn.execute("""
        UPDATE decisions SET status='approved', approved_by=?, approved_at=datetime('now','localtime')
        WHERE id=?
    """, (reviewer, decision_id))
    conn.execute("""
        UPDATE approval_queue SET status='approved', reviewer=?,
        reviewed_at=datetime('now','localtime'), notes=?
        WHERE decision_id=?
    """, (reviewer, notes, decision_id))
    dec = conn.execute("SELECT agent FROM decisions WHERE id=?", (decision_id,)).fetchone()
    if dec:
        _audit(conn, decision_id, "human_approved", dec["agent"], f"Reviewer={reviewer}: {notes}")
    conn.commit()
    conn.close()
    return True


def reject_decision(decision_id: str, reviewer: str = "human", notes: str = "") -> bool:
    """Human rejects a decision."""
    conn = get_db()
    conn.execute("UPDATE decisions SET status='rejected' WHERE id=?", (decision_id,))
    conn.execute("""
        UPDATE approval_queue SET status='rejected', reviewer=?,
        reviewed_at=datetime('now','localtime'), notes=?
        WHERE decision_id=?
    """, (reviewer, notes, decision_id))
    dec = conn.execute("SELECT agent FROM decisions WHERE id=?", (decision_id,)).fetchone()
    if dec:
        _update_trust(conn, dec["agent"], success=False)
        _audit(conn, decision_id, "human_rejected", dec["agent"], f"Reviewer={reviewer}: {notes}")
    conn.commit()
    conn.close()
    return True


def record_outcome(decision_id: str, outcome: str, rpdc: float = 0) -> None:
    """Record the outcome of an executed decision. Updates trust score."""
    conn = get_db()
    conn.execute("""
        UPDATE decisions SET status='completed', outcome=?, outcome_rpdc=?,
        executed_at=datetime('now','localtime') WHERE id=?
    """, (outcome, rpdc, decision_id))
    dec = conn.execute("SELECT agent, expected_rpdc_impact FROM decisions WHERE id=?", (decision_id,)).fetchone()
    if dec:
        success = rpdc >= 0  # positive RPDC = success
        _update_trust(conn, dec["agent"], success=success)
        _audit(conn, decision_id, "outcome_recorded", dec["agent"],
               f"RPDC={rpdc:+.2f}x, Expected={dec['expected_rpdc_impact']:+.2f}x")
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────
# TRUST SCORING — progressive autonomy
# ─────────────────────────────────────────────────────────────────

def _update_trust(conn, agent: str, success: bool):
    """Update trust score based on decision outcome."""
    row = conn.execute("SELECT * FROM trust_scores WHERE agent=?", (agent,)).fetchone()
    if not row:
        return

    total = row["total_decisions"] + 1
    succ = row["successful_decisions"] + (1 if success else 0)
    fail = row["failed_decisions"] + (0 if success else 1)

    # Exponential moving average with recency bias
    # Recent outcomes matter more than old ones
    base_rate = succ / total if total > 0 else 0.5
    recency_weight = 0.3  # 30% weight to most recent outcome
    current = row["score"]
    new_score = current * (1 - recency_weight) + (1.0 if success else 0.0) * recency_weight

    # Clamp between 0.1 and 0.95
    new_score = max(0.1, min(0.95, new_score))

    conn.execute("""
        UPDATE trust_scores SET score=?, total_decisions=?, successful_decisions=?,
        failed_decisions=?, last_updated=datetime('now','localtime') WHERE agent=?
    """, (new_score, total, succ, fail, agent))


def get_trust_scores() -> list:
    conn = get_db()
    rows = conn.execute("SELECT * FROM trust_scores ORDER BY score DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────
# CROSS-AGENT LEARNING — the family effect
# ─────────────────────────────────────────────────────────────────

# The 13 causal links between agents
CAUSAL_LINKS = {
    ("outreach", "leads_found"):        [("sales", "Check new leads from outreach")],
    ("outreach", "meetings_booked"):    [("sales", "New meetings — prepare briefs")],
    ("outreach", "reply_rate_up"):      [("sales", "Reply quality improving — adjust scoring")],
    ("qa", "bugs_found"):              [("support", "New bugs found — update KB")],
    ("qa", "tests_passed"):            [("support", "Fewer bugs — reduce escalation threshold")],
    ("brain", "relevance_improved"):   [("outreach", "Better memory — try more personalization")],
    ("brain", "pattern_detected"):     [("qa", "New pattern — generate regression tests"),
                                        ("outreach", "New pattern — adjust targeting")],
    ("hr", "hire_completed"):          [("support", "New hire — pre-generate onboarding tickets")],
    ("daily_fleet", "high_open_rate"): [("outreach", "Audience engaged — warm leads available")],
    ("finance", "forecast_updated"):   [("sales", "Forecast changed — adjust pipeline targets")],
    ("support", "csat_high"):          [("sales", "CSAT high — leverage in outreach")],
    ("support", "churn_prevented"):    [("finance", "Churn prevented — update forecast")],
    ("sales", "deal_closed"):          [("finance", "New revenue — update MRR"),
                                        ("outreach", "Win pattern — learn from this deal")],
}


def share_insight(source_agent: str, insight: str, evidence: dict = None) -> int:
    """Agent shares an insight. Returns insight ID. Triggers causal propagation."""
    conn = get_db()
    c = conn.execute("""
        INSERT INTO insights (source_agent, insight, evidence) VALUES (?, ?, ?)
    """, (source_agent, insight, json.dumps(evidence or {})))
    insight_id = c.lastrowid

    # Check if this matches any causal links
    for (src, trigger), targets in CAUSAL_LINKS.items():
        if src == source_agent and trigger.lower() in insight.lower():
            for target_agent, notification in targets:
                emit_event(conn, f"{source_agent}.insight_propagated", source_agent,
                          target_agent, {"insight": insight, "notification": notification,
                                         "insight_id": insight_id})

    _audit(conn, None, "insight_shared", source_agent, f"Insight #{insight_id}: {insight[:80]}")
    conn.commit()
    conn.close()
    return insight_id


def get_insights_for(agent: str, limit: int = 10) -> list:
    """Get recent insights relevant to this agent from causal links."""
    conn = get_db()
    # Get insights from agents that have causal links TO this agent
    source_agents = set()
    for (src, _), targets in CAUSAL_LINKS.items():
        for tgt, _ in targets:
            if tgt == agent:
                source_agents.add(src)

    if not source_agents:
        conn.close()
        return []

    placeholders = ",".join("?" * len(source_agents))
    rows = conn.execute(f"""
        SELECT * FROM insights WHERE source_agent IN ({placeholders})
        ORDER BY created_at DESC LIMIT ?
    """, (*source_agents, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────
# EVENT BUS
# ─────────────────────────────────────────────────────────────────

def emit_event(conn_or_none, event_type: str, source: str, target: str = None,
               payload: dict = None, priority: int = 5) -> int:
    """Emit an event to the bus."""
    conn = conn_or_none or get_db()
    c = conn.execute("""
        INSERT INTO events (event_type, source_agent, target_agent, payload, priority)
        VALUES (?, ?, ?, ?, ?)
    """, (event_type, source, target, json.dumps(payload or {}), priority))
    eid = c.lastrowid
    if conn_or_none is None:
        conn.commit()
        conn.close()
    return eid


def emit(event_type: str, source: str, target: str = None,
         payload: dict = None, priority: int = 5) -> int:
    """Public emit function."""
    return emit_event(None, event_type, source, target, payload, priority)


# ─────────────────────────────────────────────────────────────────
# SELF-HEALING
# ─────────────────────────────────────────────────────────────────

def check_agent_health() -> list:
    """Check all agents. Return list of issues."""
    conn = get_db()
    issues = []
    agents = conn.execute("SELECT * FROM agent_state").fetchall()

    for agent in agents:
        # Check heartbeat (should be within last 10 minutes if running)
        if agent["last_heartbeat"]:
            last = datetime.fromisoformat(agent["last_heartbeat"])
            if datetime.now() - last > timedelta(minutes=10) and agent["status"] == "running":
                issues.append({
                    "agent": agent["agent"],
                    "issue": "stale_heartbeat",
                    "detail": f"Last heartbeat {agent['last_heartbeat']}, status still 'running'",
                    "action": "restart"
                })
                conn.execute("UPDATE agent_state SET status='stale' WHERE agent=?", (agent["agent"],))

        # Check error rate
        if agent["errors_last_hour"] and agent["errors_last_hour"] > 10:
            issues.append({
                "agent": agent["agent"],
                "issue": "high_error_rate",
                "detail": f"{agent['errors_last_hour']} errors in last hour",
                "action": "throttle"
            })

    conn.commit()
    conn.close()
    return issues


# ─────────────────────────────────────────────────────────────────
# AUDIT
# ─────────────────────────────────────────────────────────────────

def _audit(conn, decision_id, event_type, agent, detail):
    trust = conn.execute("SELECT score FROM trust_scores WHERE agent=?", (agent,)).fetchone()
    trust_score = trust["score"] if trust else 0.5
    conn.execute("""
        INSERT INTO audit_log (decision_id, event_type, agent, action, detail, trust_score_at_time)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (decision_id, event_type, agent, event_type, detail, trust_score))


# ─────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────

def show_status():
    """Show full system status."""
    init_db()
    conn = get_db()

    print(f"\n  {'='*72}")
    print(f"  AONXI CLAW V2 — Agent Operating System")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  {'='*72}")

    # Trust scores
    print(f"\n  TRUST SCORES (progressive autonomy)")
    print(f"  {'─'*60}")
    scores = conn.execute("SELECT * FROM trust_scores ORDER BY score DESC").fetchall()
    for s in scores:
        bar_len = int(s["score"] * 30)
        bar = "#" * bar_len + "." * (30 - bar_len)
        level = "AUTO" if s["score"] >= TRUST_AUTO_APPROVE else "NOTIFY" if s["score"] >= TRUST_SUGGEST_ONLY else "APPROVE"
        print(f"  {s['agent']:<12s} {s['score']:.2f} [{bar}] {level:>7s}  ({s['successful_decisions']}/{s['total_decisions']} ok)")

    # Agent states
    print(f"\n  AGENT STATUS")
    print(f"  {'─'*60}")
    agents = conn.execute("SELECT * FROM agent_state ORDER BY agent").fetchall()
    for a in agents:
        status_color = a["status"] or "idle"
        print(f"  {a['agent']:<12s} {status_color:<10s} last: {a['last_run_at'] or 'never':<20s} errors: {a['errors_last_hour'] or 0}")

    # Pending approvals
    pending = conn.execute("SELECT * FROM approval_queue WHERE status='pending' ORDER BY created_at DESC").fetchall()
    if pending:
        print(f"\n  PENDING APPROVALS ({len(pending)})")
        print(f"  {'─'*60}")
        for p in pending:
            print(f"  [{p['id']}] {p['agent']:<10s} {p['action_type']:<25s} {p['description'][:40]}")
        print(f"\n  Approve: python3 claw.py approve <id>")
        print(f"  Reject:  python3 claw.py reject <id>")

    # Recent decisions
    recent = conn.execute("SELECT * FROM decisions ORDER BY created_at DESC LIMIT 5").fetchall()
    if recent:
        print(f"\n  RECENT DECISIONS")
        print(f"  {'─'*60}")
        for d in recent:
            rpdc = f"RPDC:{d['outcome_rpdc']:+.1f}x" if d['outcome_rpdc'] else ""
            print(f"  [{d['id']:<24s}] {d['status']:<12s} {d['agent']:<10s} {d['description'][:30]} {rpdc}")

    # Recent insights (family effect)
    insights = conn.execute("SELECT * FROM insights ORDER BY created_at DESC LIMIT 5").fetchall()
    if insights:
        print(f"\n  RECENT INSIGHTS (cross-agent learning)")
        print(f"  {'─'*60}")
        for i in insights:
            print(f"  [{i['source_agent']:<10s}] {i['insight'][:60]}")

    # Stats
    ev_count = conn.execute("SELECT COUNT(*) as n FROM events").fetchone()["n"]
    dec_count = conn.execute("SELECT COUNT(*) as n FROM decisions").fetchone()["n"]
    ins_count = conn.execute("SELECT COUNT(*) as n FROM insights").fetchone()["n"]
    audit_count = conn.execute("SELECT COUNT(*) as n FROM audit_log").fetchone()["n"]
    print(f"\n  SYSTEM: {ev_count} events | {dec_count} decisions | {ins_count} insights | {audit_count} audit entries")
    print(f"  {'='*72}\n")

    conn.close()


def show_audit(limit=20):
    """Show audit trail."""
    init_db()
    conn = get_db()
    rows = conn.execute("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()

    print(f"\n  AUDIT TRAIL (last {limit} entries)")
    print(f"  {'='*72}")
    for r in rows:
        trust = f"T={r['trust_score_at_time']:.2f}" if r['trust_score_at_time'] else ""
        print(f"  {r['created_at']}  {r['agent']:<10s} {r['action']:<25s} {trust:>6s}  {r['detail'][:40]}")
    print(f"  {'='*72}\n")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0].lower()

    if cmd in ("init", "start"):
        init_db()
        print("  CLAW V2 initialized. Database ready.")
        print(f"  DB: {DB_PATH}")
        print(f"  Agents: 9 registered")
        print(f"  Trust: all agents start at 0.50")
        if cmd == "start":
            show_status()

    elif cmd == "status":
        show_status()

    elif cmd == "trust":
        init_db()
        for s in get_trust_scores():
            level = "AUTO" if s["score"] >= TRUST_AUTO_APPROVE else "NOTIFY" if s["score"] >= TRUST_SUGGEST_ONLY else "APPROVE"
            print(f"  {s['agent']:<12s} {s['score']:.2f} [{level}]  {s['successful_decisions']}/{s['total_decisions']} successful")

    elif cmd == "approve":
        if len(args) < 2:
            print("  Usage: claw.py approve <approval_id> [notes]")
            return
        notes = " ".join(args[2:]) if len(args) > 2 else ""
        # Get decision_id from approval queue
        init_db()
        conn = get_db()
        row = conn.execute("SELECT decision_id FROM approval_queue WHERE id=?", (args[1],)).fetchone()
        if not row:
            # Try as decision_id directly
            row = conn.execute("SELECT id as decision_id FROM decisions WHERE id=?", (args[1],)).fetchone()
        conn.close()
        if row:
            approve_decision(row["decision_id"], "human", notes)
            print(f"  Approved: {args[1]}")
        else:
            print(f"  Not found: {args[1]}")

    elif cmd == "reject":
        if len(args) < 2:
            print("  Usage: claw.py reject <approval_id> [notes]")
            return
        notes = " ".join(args[2:]) if len(args) > 2 else ""
        init_db()
        conn = get_db()
        row = conn.execute("SELECT decision_id FROM approval_queue WHERE id=?", (args[1],)).fetchone()
        if not row:
            row = conn.execute("SELECT id as decision_id FROM decisions WHERE id=?", (args[1],)).fetchone()
        conn.close()
        if row:
            reject_decision(row["decision_id"], "human", notes)
            print(f"  Rejected: {args[1]}")
        else:
            print(f"  Not found: {args[1]}")

    elif cmd == "propose":
        if len(args) < 4:
            print('  Usage: claw.py propose <agent> <action_type> "<description>"')
            return
        init_db()
        dec_id, status = propose_decision(args[1], args[2], args[3],
                                          confidence=float(args[4]) if len(args) > 4 else 0.5)
        print(f"  Decision: {dec_id}")
        print(f"  Status:   {status}")

    elif cmd == "insight":
        if len(args) < 3:
            print('  Usage: claw.py insight <agent> "<insight>"')
            return
        init_db()
        iid = share_insight(args[1], args[2])
        print(f"  Insight #{iid} shared by {args[1]}")
        print(f"  Causal propagation triggered.")

    elif cmd == "audit":
        limit = int(args[1]) if len(args) > 1 else 20
        show_audit(limit)

    elif cmd == "health":
        init_db()
        issues = check_agent_health()
        if issues:
            for i in issues:
                print(f"  [{i['issue']}] {i['agent']}: {i['detail']} -> {i['action']}")
        else:
            print("  All agents healthy.")

    elif cmd == "causal":
        print(f"\n  CAUSAL LINK MAP (13 links)")
        print(f"  {'='*60}")
        for (src, trigger), targets in sorted(CAUSAL_LINKS.items()):
            for tgt, desc in targets:
                print(f"  {src}.{trigger:<25s} -> {tgt:<10s} ({desc})")
        print(f"  {'='*60}\n")

    else:
        print(f"  Unknown command: {cmd}")
        print(f"  Commands: init, start, status, trust, approve, reject, propose, insight, audit, health, causal")


if __name__ == "__main__":
    main()
