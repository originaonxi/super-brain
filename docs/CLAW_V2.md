# AONXI Claw V2 — The Agent Operating System

> **V1 Claw was an event bus. V2 Claw is a decision engine.**

---

## What V1 Had vs What V2 Adds

| V1 Claw | V2 Claw |
|---------|---------|
| Event bus (SQLite) | Decision Engine + Event Bus |
| File-based context sharing | Direct insight propagation with causal links |
| Poll loop (30s) | Decision cycles + priority queue |
| No trust model | Progressive autonomy (0.0 → 1.0 trust score) |
| No human gates | Configurable approval gates per action type |
| No conflict resolution | Evidence-based tiebreak when agents disagree |
| No self-healing | Heartbeat monitoring + auto-restart |
| No experiment integration | Every decision tracked with RPDC outcome |
| No audit trail | Full audit: trigger → decision → approval → outcome |
| 7 agents, 20 subscriptions | 9 agents, 13 causal links, unlimited decisions |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                       AONXI CLAW V2 DAEMON                          │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  ┌────────────┐  │
│  │   DECISION   │  │    TRUST     │  │  HUMAN   │  │  RESOURCE  │  │
│  │   ENGINE     │  │   SCORING    │  │  GATES   │  │  MANAGER   │  │
│  │              │  │              │  │          │  │            │  │
│  │ Agents       │  │ 0.0 → 1.0   │  │ Approve  │  │ Memory     │  │
│  │ propose      │  │ Earn trust   │  │ Reject   │  │ CPU        │  │
│  │ actions.     │  │ via results. │  │ Rollback │  │ Priority   │  │
│  │ Best action  │  │ Good outcome │  │          │  │            │  │
│  │ wins.        │  │ = more auto. │  │ Required │  │ Urgent     │  │
│  │              │  │ Bad outcome  │  │ for some │  │ preempts   │  │
│  │ Evidence-    │  │ = less auto. │  │ actions  │  │ routine.   │  │
│  │ based.       │  │              │  │ always.  │  │            │  │
│  └──────┬───────┘  └──────┬───────┘  └────┬─────┘  └─────┬──────┘  │
│         │                 │               │               │          │
│  ┌──────▼─────────────────▼───────────────▼───────────────▼───────┐  │
│  │                    DATA LAYER (SQLite WAL)                     │  │
│  │                                                                │  │
│  │  events         │ decisions      │ trust_scores  │ approval_q  │  │
│  │  insights       │ audit_log      │ agent_state   │ resources   │  │
│  └──┬─────┬────┬────┬─────┬────┬────┬─────┬────┬────┬────────────┘  │
│     │     │    │    │     │    │    │     │    │    │               │
└─────┼─────┼────┼────┼─────┼────┼────┼─────┼────┼────┼───────────────┘
      │     │    │    │     │    │    │     │    │    │
  ┌───▼──┐┌─▼──┐┌▼───┐┌──▼─┐┌──▼─┐┌─▼──┐┌─▼──┐┌▼────┐┌──▼──┐
  │SALES ││SUP.││FIN.││ HR ││ QA ││SEO ││FLEET││OUT. ││BRAIN│
  │      ││    ││    ││    ││    ││    ││     ││     ││     │
  │$200K ││73% ││100%││4.2h││24/7││3am ││5/day││559x ││50+  │
  │proved││auto││auto││save││self││runs ││cron ││RPDC ││repos│
  └──────┘└────┘└────┘└────┘└────┘└────┘└─────┘└─────┘└─────┘
```

---

## The Decision Flow

```
1. AGENT PROPOSES ACTION
   outreach proposes: "Send 50 emails to healthcare leads"
   confidence: 0.82, expected RPDC: +5.2x

2. CLAW CHECKS TRUST
   outreach trust score: 0.50 (new agent)
   Action type: "send_outreach_batch" (requires human approval)

3. DECISION ROUTED
   Trust < 0.85 AND action in ALWAYS_REQUIRE_APPROVAL
   → Added to approval queue
   → Human notified

4. HUMAN REVIEWS
   $ python3 claw.py approve aq-c55a32 "Looks good"
   → Decision status: approved
   → Trust updated
   → Audit logged

5. AGENT EXECUTES
   Outreach sends 50 emails
   Results: 5.2% reply rate, 4 meetings booked

6. OUTCOME RECORDED
   $ claw.py record-outcome dec-out-0331 "4 meetings" 8.4
   → RPDC: +8.4x (better than expected +5.2x)
   → Trust score: 0.50 → 0.65 (earned more autonomy)
   → Next time similar action: auto-approved with notification

7. CROSS-AGENT RIPPLE
   outreach.meetings_booked → sales notified: "New meetings — prepare briefs"
   outreach.reply_rate_up → sales adjusts scoring
   Insight stored in shared memory for all agents
```

---

## Trust Scoring — Progressive Autonomy

Every agent starts at 0.50 (neutral). Trust changes based on outcomes:

```
TRUST LEVELS:
  0.85+ = AUTO-APPROVE    Agent acts without human. Full autonomy earned.
  0.40-0.85 = NOTIFY      Agent acts, human notified, can rollback.
  0.00-0.40 = APPROVE     Agent can only suggest. Human must approve.

ALWAYS REQUIRE APPROVAL (regardless of trust):
  - send_email_to_client
  - close_deal
  - create_invoice
  - deploy_agent
  - modify_pricing
  - send_outreach_batch

TRUST UPDATE FORMULA:
  new_score = current * 0.7 + (1.0 if success else 0.0) * 0.3
  Clamped: [0.10, 0.95]

  This means: recent outcomes matter more than old ones.
  A string of successes quickly raises trust.
  A single failure moderately lowers trust.
  An agent can never reach 1.0 (always some oversight).
```

---

## 13 Causal Links — The Family Effect

When one agent improves, the system automatically notifies connected agents:

```
outreach.leads_found         → sales:    "Check new leads"
outreach.meetings_booked     → sales:    "Prepare briefs"
outreach.reply_rate_up       → sales:    "Adjust scoring"

qa.bugs_found                → support:  "Update KB"
qa.tests_passed              → support:  "Reduce escalation threshold"

brain.relevance_improved     → outreach: "Try more personalization"
brain.pattern_detected       → qa:       "Generate regression tests"
brain.pattern_detected       → outreach: "Adjust targeting"

hr.hire_completed            → support:  "Pre-generate onboarding tickets"
daily_fleet.high_open_rate   → outreach: "Warm leads available"
finance.forecast_updated     → sales:    "Adjust pipeline targets"
support.csat_high            → sales:    "Leverage in outreach"
support.churn_prevented      → finance:  "Update forecast"
sales.deal_closed            → finance:  "Update MRR"
sales.deal_closed            → outreach: "Learn from this deal"
```

---

## CLI Reference

```bash
python3 claw.py init                              # Initialize database
python3 claw.py start                             # Init + show status
python3 claw.py status                            # Full system dashboard

python3 claw.py propose <agent> <action> "<desc>" [confidence]
python3 claw.py approve <id> [notes]              # Human approves
python3 claw.py reject <id> [notes]               # Human rejects

python3 claw.py insight <agent> "<insight>"        # Share cross-agent insight
python3 claw.py causal                             # Show all 13 causal links
python3 claw.py trust                              # Show trust scores
python3 claw.py audit [N]                          # Last N audit entries
python3 claw.py health                             # Check agent health
```

---

## Why This Is 10x Better Than Any Agent Orchestrator in 2026

1. **Decision engine, not just event bus.** Agents propose. System evaluates. Best action wins.
2. **Trust scoring.** Agents earn autonomy through results. Bad outcomes = less freedom. No other system has this.
3. **Human-in-the-loop with progressive autonomy.** Not binary (human or auto). Gradual trust building.
4. **13 causal links.** Not just "agents share a queue." Directional cause-effect relationships.
5. **Full audit trail.** Every decision traceable from trigger to outcome. Compliance-ready.
6. **RPDC integration.** Every decision measured by revenue per dollar of cost.
7. **Self-healing.** Heartbeat monitoring, stale agent detection, auto-restart.
8. **Conflict resolution.** When two agents disagree, evidence and trust score break the tie.
9. **All on one Mac Mini.** No cloud infra. No Kubernetes. No DevOps team. SQLite + Python.
10. **Open source.** Every line readable. Every decision auditable. Trust is built on transparency.
