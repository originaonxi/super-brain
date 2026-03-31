#!/usr/bin/env python3
"""
company.py — AONXI as an Automated Company

The super-brain repo IS the company.
Every agent is a team member with a job description and KPIs.
Every day the company runs, improves, and reports to you.

Departments:
  SALES    — Find leads → qualify → outreach → close → CRM logged
  DELIVERY — Onboard client → deploy agents → weekly CSAT → iterate
  HR       — Agent health → improvement → cross-training → new hires
  FINANCE  — Revenue tracking → cost/query → ROI per agent → MRR

The KPIs that matter:
  - New sales per week
  - Client CSAT >= 9.0 (non-negotiable)
  - Revenue per client per month
  - Cost to deliver (electricity + time)
  - Agents improving each other (compound score)

Usage:
    python company.py status          # Full company status dashboard
    python company.py sales-pipeline  # What's in the funnel
    python company.py delivery-check  # CSAT and delivery health
    python company.py daily-brief     # Morning CEO report
    python company.py add-client      # Onboard a new client
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from brain import SuperBrain

HOME = Path.home()
DB_PATH = HOME / "super-brain" / "data" / "company.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ── DATABASE SETUP ─────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            company     TEXT,
            email       TEXT,
            plan        TEXT,
            mrr         REAL DEFAULT 0,
            status      TEXT DEFAULT 'onboarding',
            agents      TEXT DEFAULT '[]',
            onboarded   TEXT,
            csat_score  REAL DEFAULT 0,
            csat_count  INTEGER DEFAULT 0,
            notes       TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS pipeline (
            id          TEXT PRIMARY KEY,
            name        TEXT,
            company     TEXT,
            email       TEXT,
            stage       TEXT DEFAULT 'lead',
            score       REAL DEFAULT 0,
            source      TEXT DEFAULT 'outreach',
            created     TEXT,
            last_touch  TEXT,
            notes       TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS csat_log (
            id          TEXT PRIMARY KEY,
            client_id   TEXT,
            score       REAL,
            feedback    TEXT,
            date        TEXT,
            agent       TEXT
        );

        CREATE TABLE IF NOT EXISTS revenue_log (
            id          TEXT PRIMARY KEY,
            client_id   TEXT,
            amount      REAL,
            type        TEXT,
            date        TEXT,
            notes       TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS agent_performance (
            id          TEXT PRIMARY KEY,
            agent_name  TEXT,
            date        TEXT,
            tasks_run   INTEGER DEFAULT 0,
            success     INTEGER DEFAULT 0,
            errors      INTEGER DEFAULT 0,
            revenue_gen REAL DEFAULT 0,
            notes       TEXT DEFAULT ''
        );
    """)
    conn.commit()
    return conn


# ── SALES PIPELINE ─────────────────────────────────────────────────────────

class SalesPipeline:
    """
    Tracks and manages the autonomous sales pipeline.
    Every lead comes from FundingScanner, outreach-agent, or referral.
    Stages: lead → qualified → demo → proposal → closing → won/lost
    """

    STAGES = ["lead", "qualified", "demo", "proposal", "closing", "won", "lost"]
    STAGE_VALUE = {"lead": 0.05, "qualified": 0.15, "demo": 0.3, "proposal": 0.5, "closing": 0.8, "won": 1.0, "lost": 0}

    def __init__(self):
        self.db = get_db()

    def add_lead(self, name: str, company: str, email: str, source: str = "outreach", score: float = 0.5) -> str:
        import uuid
        lid = str(uuid.uuid4())[:8]
        self.db.execute(
            "INSERT INTO pipeline (id, name, company, email, stage, score, source, created, last_touch) VALUES (?,?,?,?,?,?,?,?,?)",
            [lid, name, company, email, "lead", score, source, datetime.now().isoformat(), datetime.now().isoformat()]
        )
        self.db.commit()
        return lid

    def advance_stage(self, lead_id: str, notes: str = "") -> dict:
        row = self.db.execute("SELECT * FROM pipeline WHERE id=?", [lead_id]).fetchone()
        if not row:
            return {"error": "lead not found"}
        current = row["stage"]
        idx = self.STAGES.index(current)
        if idx < len(self.STAGES) - 1:
            next_stage = self.STAGES[idx + 1]
            self.db.execute(
                "UPDATE pipeline SET stage=?, last_touch=?, notes=? WHERE id=?",
                [next_stage, datetime.now().isoformat(), notes, lead_id]
            )
            self.db.commit()
            return {"lead": lead_id, "moved_to": next_stage}
        return {"lead": lead_id, "already_at": current}

    def pipeline_summary(self) -> dict:
        rows = self.db.execute("SELECT stage, COUNT(*) as cnt, AVG(score) as avg_score FROM pipeline GROUP BY stage").fetchall()
        summary = {}
        for r in rows:
            summary[r["stage"]] = {"count": r["cnt"], "avg_score": round(r["avg_score"] or 0, 2)}
        return summary

    def hot_leads(self, threshold: float = 0.7) -> list:
        rows = self.db.execute(
            "SELECT * FROM pipeline WHERE score >= ? AND stage NOT IN ('won','lost') ORDER BY score DESC LIMIT 10",
            [threshold]
        ).fetchall()
        return [dict(r) for r in rows]

    def weekly_velocity(self) -> dict:
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        new = self.db.execute("SELECT COUNT(*) as c FROM pipeline WHERE created >= ?", [week_ago]).fetchone()["c"]
        won = self.db.execute("SELECT COUNT(*) as c FROM pipeline WHERE stage='won' AND last_touch >= ?", [week_ago]).fetchone()["c"]
        return {"new_leads_7d": new, "won_7d": won, "conversion": round(won / max(new, 1) * 100, 1)}


# ── DELIVERY & CSAT ────────────────────────────────────────────────────────

class DeliveryEngine:
    """
    Manages client delivery and CSAT.
    CSAT must stay >= 9.0 — this is a hard gate.
    If any client drops below 8.0, human escalation fires immediately.
    """

    CSAT_TARGET = 9.0
    CSAT_ESCALATE = 8.0

    def __init__(self):
        self.db = get_db()

    def add_client(self, name: str, company: str, email: str, plan: str, mrr: float, agents: list) -> str:
        import uuid
        cid = str(uuid.uuid4())[:8]
        self.db.execute(
            "INSERT INTO clients (id, name, company, email, plan, mrr, status, agents, onboarded) VALUES (?,?,?,?,?,?,?,?,?)",
            [cid, name, company, email, plan, mrr, "active", json.dumps(agents), datetime.now().isoformat()]
        )
        self.db.commit()
        return cid

    def log_csat(self, client_id: str, score: float, feedback: str = "", agent: str = "delivery") -> dict:
        import uuid
        lid = str(uuid.uuid4())[:8]
        self.db.execute(
            "INSERT INTO csat_log (id, client_id, score, feedback, date, agent) VALUES (?,?,?,?,?,?)",
            [lid, client_id, score, feedback, datetime.now().isoformat(), agent]
        )
        # Update client CSAT average
        rows = self.db.execute("SELECT AVG(score) as avg, COUNT(*) as cnt FROM csat_log WHERE client_id=?", [client_id]).fetchone()
        self.db.execute("UPDATE clients SET csat_score=?, csat_count=? WHERE id=?", [rows["avg"], rows["cnt"], client_id])
        self.db.commit()

        alert = None
        if score < self.CSAT_ESCALATE:
            alert = f"ESCALATE: {client_id} scored {score} — below {self.CSAT_ESCALATE} threshold"

        return {"logged": lid, "new_avg": round(rows["avg"] or 0, 2), "alert": alert}

    def csat_dashboard(self) -> dict:
        clients = self.db.execute("SELECT * FROM clients WHERE status='active'").fetchall()
        at_risk = []
        healthy = []
        for c in clients:
            if c["csat_score"] < self.CSAT_ESCALATE and c["csat_count"] > 0:
                at_risk.append({"id": c["id"], "company": c["company"], "csat": c["csat_score"]})
            else:
                healthy.append({"id": c["id"], "company": c["company"], "csat": c["csat_score"]})

        avg = self.db.execute("SELECT AVG(csat_score) as a FROM clients WHERE status='active' AND csat_count > 0").fetchone()["a"] or 0

        return {
            "overall_csat": round(avg, 2),
            "target": self.CSAT_TARGET,
            "at_target": avg >= self.CSAT_TARGET,
            "active_clients": len(clients),
            "at_risk": at_risk,
            "healthy": len(healthy),
        }

    def delivery_checklist(self, client_id: str) -> dict:
        """Standard delivery checklist for a client."""
        client = self.db.execute("SELECT * FROM clients WHERE id=?", [client_id]).fetchone()
        if not client:
            return {"error": "client not found"}

        agents = json.loads(client["agents"] or "[]")
        checklist = {
            "client": client["company"],
            "plan": client["plan"],
            "agents_deployed": agents,
            "checks": {
                "agents_running": len(agents) > 0,
                "csat_above_target": client["csat_score"] >= self.CSAT_TARGET or client["csat_count"] == 0,
                "recent_csat": client["csat_count"] > 0,
            }
        }
        checklist["delivery_score"] = sum(1 for v in checklist["checks"].values() if v) / len(checklist["checks"]) * 10
        return checklist


# ── REVENUE TRACKING ───────────────────────────────────────────────────────

class RevenueTracker:
    def __init__(self):
        self.db = get_db()

    def log_payment(self, client_id: str, amount: float, type: str = "mrr") -> str:
        import uuid
        rid = str(uuid.uuid4())[:8]
        self.db.execute(
            "INSERT INTO revenue_log (id, client_id, amount, type, date) VALUES (?,?,?,?,?)",
            [rid, client_id, amount, type, datetime.now().isoformat()]
        )
        self.db.commit()
        return rid

    def mrr_summary(self) -> dict:
        clients = self.db.execute("SELECT * FROM clients WHERE status='active'").fetchall()
        mrr = sum(c["mrr"] for c in clients)
        return {
            "mrr": mrr,
            "arr": mrr * 12,
            "active_clients": len(clients),
            "avg_mrr_per_client": round(mrr / max(len(clients), 1), 2),
        }

    def revenue_this_month(self) -> float:
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0).isoformat()
        row = self.db.execute("SELECT SUM(amount) as total FROM revenue_log WHERE date >= ?", [month_start]).fetchone()
        return row["total"] or 0


# ── COMPANY STATUS ─────────────────────────────────────────────────────────

class Company:
    """The company. All departments. One view."""

    def __init__(self):
        self.sales = SalesPipeline()
        self.delivery = DeliveryEngine()
        self.revenue = RevenueTracker()
        self._brain = None

    @property
    def brain(self):
        if self._brain is None:
            try:
                self._brain = SuperBrain()
            except Exception:
                pass
        return self._brain

    def daily_brief(self) -> str:
        """Morning CEO report. Auto-generated. Run at 6am."""
        pipeline = self.sales.pipeline_summary()
        hot = self.sales.hot_leads()
        velocity = self.sales.weekly_velocity()
        csat = self.delivery.csat_dashboard()
        mrr = self.revenue.mrr_summary()
        month_rev = self.revenue.revenue_this_month()

        lines = []
        lines.append("=" * 60)
        lines.append(f"  AONXI DAILY BRIEF — {datetime.now().strftime('%A, %B %d %Y %H:%M')}")
        lines.append("=" * 60)

        # Revenue
        lines.append("\n  REVENUE")
        lines.append(f"    MRR:          ${mrr['mrr']:,.0f}")
        lines.append(f"    ARR:          ${mrr['arr']:,.0f}")
        lines.append(f"    This month:   ${month_rev:,.0f}")
        lines.append(f"    Clients:      {mrr['active_clients']}")

        # CSAT — most important metric
        csat_flag = "OK" if csat["at_target"] else "ALERT"
        lines.append(f"\n  CSAT [{csat_flag}]")
        lines.append(f"    Overall:      {csat['overall_csat']:.1f} / 10 (target: {csat['target']})")
        lines.append(f"    Active:       {csat['active_clients']} clients")
        if csat["at_risk"]:
            lines.append(f"    AT RISK:")
            for r in csat["at_risk"]:
                lines.append(f"      {r['company']}: {r['csat']:.1f} — NEEDS IMMEDIATE ATTENTION")

        # Sales pipeline
        lines.append("\n  SALES PIPELINE")
        for stage, data in sorted(pipeline.items()):
            lines.append(f"    {stage:<12} {data['count']:>3} leads  (avg score: {data['avg_score']:.2f})")

        # Velocity
        lines.append(f"\n  PIPELINE VELOCITY (7 days)")
        lines.append(f"    New leads:    {velocity['new_leads_7d']}")
        lines.append(f"    Closed:       {velocity['won_7d']}")
        lines.append(f"    Conversion:   {velocity['conversion']}%")

        # Hot leads
        if hot:
            lines.append(f"\n  HOT LEADS (score >= 0.7)")
            for l in hot[:5]:
                lines.append(f"    {l['company']} ({l['stage']}) — score {l['score']:.2f}")

        lines.append("\n" + "=" * 60)
        lines.append("  Focus today: " + (
            "Fix at-risk clients first. CSAT is the only metric that matters."
            if csat["at_risk"] else
            "Pipeline + sales. CSAT is healthy."
        ))
        lines.append("=" * 60)

        return "\n".join(lines)

    def status(self) -> dict:
        return {
            "timestamp": datetime.now().isoformat(),
            "pipeline": self.sales.pipeline_summary(),
            "velocity": self.sales.weekly_velocity(),
            "csat": self.delivery.csat_dashboard(),
            "revenue": self.revenue.mrr_summary(),
        }


def main():
    company = Company()

    if len(sys.argv) < 2:
        print(company.daily_brief())
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "status":
        s = company.status()
        print(json.dumps(s, indent=2))

    elif cmd == "daily-brief":
        print(company.daily_brief())

    elif cmd == "sales-pipeline":
        pipeline = company.sales.pipeline_summary()
        hot = company.sales.hot_leads()
        velocity = company.sales.weekly_velocity()
        print("\n  SALES PIPELINE")
        for stage, data in sorted(pipeline.items()):
            print(f"    {stage:<12} {data['count']:>3} leads")
        print(f"\n  VELOCITY: {velocity['new_leads_7d']} new, {velocity['won_7d']} won, {velocity['conversion']}% rate")
        if hot:
            print(f"\n  HOT LEADS:")
            for l in hot:
                print(f"    {l['company']} — {l['stage']} — score {l['score']:.2f}")

    elif cmd == "delivery-check":
        csat = company.delivery.csat_dashboard()
        print(f"\n  CSAT: {csat['overall_csat']:.1f} / 10 (target: {csat['target']})")
        print(f"  Active clients: {csat['active_clients']}")
        if csat["at_risk"]:
            print(f"\n  AT RISK (below {company.delivery.CSAT_ESCALATE}):")
            for r in csat["at_risk"]:
                print(f"    {r['company']}: {r['csat']:.1f} — ESCALATE NOW")
        else:
            print(f"  All clients healthy. {csat['healthy']} above target.")

    elif cmd == "add-client":
        if len(sys.argv) < 6:
            print("Usage: company.py add-client <name> <company> <email> <plan> <mrr>")
            sys.exit(1)
        _, _, name, co, email, plan, mrr = sys.argv
        cid = company.delivery.add_client(name, co, email, plan, float(mrr), agents=[])
        print(f"  Client added: {cid} | {co} | ${mrr}/mo")

    elif cmd == "log-csat":
        if len(sys.argv) < 4:
            print("Usage: company.py log-csat <client_id> <score> [feedback]")
            sys.exit(1)
        cid = sys.argv[2]
        score = float(sys.argv[3])
        feedback = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        result = company.delivery.log_csat(cid, score, feedback)
        print(f"  CSAT logged: {result['new_avg']:.1f} avg")
        if result.get("alert"):
            print(f"  !!! {result['alert']}")

    elif cmd == "add-lead":
        if len(sys.argv) < 5:
            print("Usage: company.py add-lead <name> <company> <email> [score]")
            sys.exit(1)
        name, co, email = sys.argv[2], sys.argv[3], sys.argv[4]
        score = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
        lid = company.sales.add_lead(name, co, email, score=score)
        print(f"  Lead added: {lid} | {co} | score {score}")

    else:
        print(f"Unknown: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
