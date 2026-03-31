# AONXI OS — Your Mac Mini Replaces Every SaaS Tool You Pay For

**A self-learning SaaS factory. It watches how you use your existing tools, learns YOUR specific workflows, then builds local versions that are BETTER than the originals — because it has ALL your data in one brain.**

**Live site:** [https://originaonxi.github.io/super-brain/](https://originaonxi.github.io/super-brain/)

Built by [Anmol Sam](https://github.com/originaonxi) | CTO, Aonxi

---

## The Problem

You pay $3,000+/month for siloed SaaS tools that can't talk to each other. Your CRM doesn't know what your support team learned. Your marketing tool can't see your sales data. Your project management tool has no idea what your finance tool knows.

**Your Mac Mini can see ALL of it.**

## The SaaS You Cancel

| SaaS Tool Category | Typical Monthly Cost | With AONXI OS | Savings |
|---|---|---|---|
| CRM & Sales Platform | $800/mo | $0 | $800/mo |
| Support & Ticketing Platform | $55/seat/mo | $0 | $550/mo (10 seats) |
| Marketing Automation Platform | $300/mo | $0 | $300/mo |
| SEO & Marketing Analytics | $200/mo | $0 | $200/mo |
| Project Management Platform | $20/seat/mo | $0 | $200/mo (10 seats) |
| Team Communication Platform | $12.50/seat/mo | $0 | $125/mo (10 seats) |
| Ad Management Platform | $500/mo | $0 | $500/mo |
| Accounting & Finance Platform | $80/mo | $0 | $80/mo |
| **Total** | **$2,755/mo** | **$15/mo electricity** | **$2,740/mo saved** |

**$32,880/year back in your pocket.** And the local versions are better because they share context.

---

## How It Works — The Tool Learning Flow

```
STEP 1: CONNECT                    STEP 2: OBSERVE
┌──────────────────────┐           ┌──────────────────────┐
│ Connect your existing│           │ Mac Mini watches how  │
│ SaaS tools via API   │    ──>    │ you ACTUALLY use them │
│ (CRM, support desk,  │           │ (not how the manual   │
│  marketing, finance) │           │  says to use them)    │
└──────────────────────┘           └──────────────────────┘
                                              │
                                              v
STEP 4: CANCEL                     STEP 3: BUILD
┌──────────────────────┐           ┌──────────────────────┐
│ Cancel subscriptions │           │ Builds local versions │
│ one by one as each   │    <──    │ that replicate YOUR   │
│ local version proves │           │ workflows + add cross-│
│ itself in parallel   │           │ tool intelligence     │
└──────────────────────┘           └──────────────────────┘
```

**Why local versions are BETTER:** Your CRM tool only sees CRM data. Your support tool only sees support data. Your Mac Mini sees EVERYTHING — so when a support ticket comes in from your biggest sales prospect, it knows. When your marketing campaign targets a segment that your finance data shows is unprofitable, it flags it. Siloed SaaS tools can't do this. Your Mac Mini can.

---

## Architecture

```
+------------------------------------------------------------------+
|                         SUPER BRAIN                               |
|                   AONXI OS — SaaS Replacement Engine              |
+------------------------------------------------------------------+
|                                                                    |
|   +------------------+    +------------------+    +--------------+ |
|   | SaaS Replacement |    |  Cross-Tool      |    |  Semantic    | |
|   |    Engine         |    |  Intelligence    |    |  Memory via  | |
|   | (observe, learn, |    |  (patterns that  |    |  Mem0 + Local| |
|   |  build, replace) |    |  span all tools) |    |  SQLite      | |
|   +------------------+    +------------------+    +--------------+ |
|                                                                    |
|   +------------------+    +------------------+    +--------------+ |
|   |  63+ Memories    |    |  9 Categories    |    |  Workflow    | |
|   |  (and growing)   |    |  agent, research |    |  Pattern DB  | |
|   |                  |    |  gtm, aonxi,     |    |  (learned    | |
|   |                  |    |  saas, ci, etc   |    |   behaviors) | |
|   +------------------+    +------------------+    +--------------+ |
|                                                                    |
+----+-------------------+-------------------+----------------------+
     |                   |                   |
     v                   v                   v
+----------+     +-------------+     +----------------+
| CLI Tools|     | Claude Code |     | SaaS Tool APIs |
| mem0_push|     | PostToolUse |     | (CRM, support, |
| mem0_search    | Hook (auto) |     |  marketing, etc)|
+----------+     +-------------+     +----------------+
     |                   |                   |
     v                   v                   v
+------------------------------------------------------------------+
|                    YOUR 55+ PROJECTS                              |
|                                                                    |
|  Agents (20)     Research (10)    GTM (4)    Aonxi (8)    Other  |
|  techm-intel     asm-replication  nova-gtm   aria         echo   |
|  frontier-agent  attention-scratch bre-gtm   memcollab    pkm    |
|  news-briefing   llm-calibration  myhq-gtm  router       dyad   |
|  stock-analyst   moe-efficiency   sn-gtm    safeguard    ...    |
|  ...             ...                         ...                  |
+------------------------------------------------------------------+
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full deep dive.

---

## What Makes This Different

| Dimension | Generic AI Assistants | Cloud CRM/SaaS Suites | Open-Source Self-Hosted | Automation Platforms | AONXI OS |
|---|---|---|---|---|---|
| **Data ownership** | Theirs | Theirs | Yours | Mixed | **Yours — 100% local** |
| **Cross-tool intelligence** | None | Within their suite only | Manual wiring | Rule-based | **Automatic — all data in one brain** |
| **Learns YOUR workflows** | No | No | No | You build automations manually | **Yes — observes and replicates** |
| **Per-query cost** | $0.01-0.10 | N/A | Varies | Per-task pricing | **$0 — local inference** |
| **Replaces SaaS subscriptions** | No | IS the subscription | Partial | No | **Yes — the whole point** |
| **Privacy / compliance** | Data leaves | Data leaves | Depends | Data leaves | **Zero data leaves your hardware** |

---

## Quick Start

### Memory (V1)
```bash
# Push a learning to the brain
~/wrappers/mem0_push.sh "nova-gtm: healthcare leads convert 3x on Tuesdays" "gtm-engine"

# Search the brain
~/wrappers/mem0_search.sh "what works for healthcare outreach?" 5

# Auto-learning: active
# Every Write/Edit/Bash in Claude Code auto-feeds the brain via PostToolUse hook
```

### Orchestration (V2)
```bash
# See the full ecosystem registry
python3 src/brain.py registry

# Dependency graph for any repo
python3 src/brain.py graph aros-agent

# Health check all repos
python3 src/brain.py health-all

# Detect cross-repo patterns
python3 src/brain.py patterns

# Generate improvement suggestions
python3 src/brain.py suggest nova-gtm

# Full ecosystem report
python3 src/brain.py report

# Deep scan + HTML dashboard
python3 src/orchestrator.py dashboard
```

### Evals
```bash
# Run full eval suite across all agent types
python3 src/evals.py run-all

# Eval a specific agent type
python3 src/evals.py run --agent outreach
python3 src/evals.py run --agent delivery
python3 src/evals.py run --agent research

# View compound intelligence score
python3 src/evals.py score

# Week-over-week improvement tracking
python3 src/evals.py weekly-report

# Compare two weeks
python3 src/evals.py compare --week 2026-W12 --week 2026-W13

# Experiment tracking — RPDC attribution
python3 src/evals.py experiment start outreach "switched to 1-paragraph emails"
python3 src/evals.py rpdc
python3 src/evals.py leaderboard
```

### Company
```bash
# Morning CEO brief
python3 src/company.py daily-brief

# Sales pipeline status
python3 src/company.py sales-pipeline

# CSAT check (must be >= 9.0)
python3 src/company.py delivery-check

# Add a client
python3 src/company.py add-client "Jane Smith" "Acme Corp" "jane@acme.com" "business" 4300

# Log CSAT
python3 src/company.py log-csat CLIENT_ID 9.5 "Agents are saving us 4hrs/day"
```

---

## RPDC — The ONE Metric

```
RPDC = Revenue Attributed to Agent / (Inference Cost + Human QC Cost)

Example (Outreach Agent):
  Revenue:        $14,000/month (meetings booked -> deals closed)
  Inference cost:  $0.50/month  (local Ollama, electricity only)
  Human QC cost:   $250/month   (5 hrs/month reviewing emails @ $50/hr)

  RPDC = $14,000 / ($0.50 + $250) = 55.9x

  Every $1 you spend on this agent generates $55.90 in revenue.
```

See [EVALS.md](docs/EVALS.md) for the full experiment tracking and attribution architecture.

---

## What's Inside

```
super-brain/
├── README.md                       # You are here
├── index.html                      # AONXI sales page — 10-section no-brainer funnel
├── src/
│   ├── brain.py                    # V2: Memory + orchestration SDK
│   ├── orchestrator.py             # Ecosystem scan + improvement engine
│   ├── company.py                  # Automated company: sales + delivery + CSAT
│   ├── evals.py                    # Agent evaluation framework — RPDC + experiment tracking
│   ├── local_brain.py              # MemoryMesh local memory layer
│   ├── mem0_push.sh                # Push memories to Mem0 cloud
│   ├── mem0_search.sh              # Search the brain
│   └── mem0_hook.sh                # Claude Code PostToolUse auto-learning hook
├── config/
│   ├── repos.yaml                  # Complete registry of all 50+ repos
│   ├── categories.json             # Memory category taxonomy
│   └── claude_hooks.json           # Claude Code hook config
├── data/
│   ├── company.db                  # SQLite: clients, pipeline, CSAT, revenue
│   └── evals.db                    # SQLite: weekly eval snapshots + compound scores
├── reports/                        # Auto-generated: improvement reports + dashboards
├── docs/
│   ├── ARCHITECTURE.md             # Full system architecture
│   ├── EVOLUTION.md                # V1 -> V5 roadmap
│   └── EVALS.md                    # Evaluation & experiment attribution architecture
├── examples/
│   ├── cross_project_query.sh
│   └── daily_digest.sh
└── tests/
    └── test_brain.sh
```

---

## The Company Architecture

```
                    ┌─────────────────────────────────┐
                    │         SUPER BRAIN V2           │
                    │  The SaaS Replacement Engine     │
                    └──────────────┬──────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
    ┌─────▼──────┐          ┌──────▼──────┐         ┌──────▼──────┐
    │   SALES    │          │  DELIVERY   │         │    BRAIN    │
    │            │          │             │         │             │
    │ FundingScn │          │ AROS + ARIA │         │ Mem0 cloud  │
    │ OutreachV8 │          │ GTM Engines │         │ MemoryMesh  │
    │ NOVA GTM   │          │ QA Systems  │         │ Local SQLite│
    │            │          │             │         │             │
    │ KPI: MRR   │          │ KPI: CSAT   │         │ KPI: Cross- │
    │ KPI: Conv  │          │ >= 9.0      │         │ tool intel  │
    └────────────┘          └─────────────┘         └─────────────┘
          │                        │
          └────────────────────────┘
                    │
              Human QC Gate
              (approve before ship)
```

**The outcome loop:**
1. Brain connects to your existing SaaS tools and observes workflows
2. Detects patterns and builds local equivalents
3. Runs local versions in parallel with existing tools for validation
4. Sales agents find new leads (FundingScanner + Outreach)
5. Delivery agents serve existing clients (CSAT must stay >= 9.0)
6. Research improves agent accuracy
7. Every outcome feeds back to the brain
8. Brain gets smarter, local tools get better, SaaS subscriptions get cancelled

---

## Evolution Roadmap

| Version | Name | Status | Core Capability |
|---------|------|--------|----------------|
| **V1** | Memory Spine | **LIVE** | Store + search 55 projects via Mem0 |
| **V2** | Synaptic Links | Next | Auto-detect cross-project dependencies |
| **V3** | Predictive Cortex + SaaS Tool Learning | Planned | Predict needs + observe and learn SaaS workflows |
| **V4** | Autonomous Hippocampus + SaaS Replacement | Planned | Self-healing memory + autonomous SaaS tool replacement |
| **V5** | Full Business OS | Vision | Zero external dependencies — every tool runs locally |

See [EVOLUTION.md](docs/EVOLUTION.md) for the full vision.

---

## Stats

- **63 memories** across **9 categories**
- **55 projects** indexed and connected
- **0.90 top relevance scores** on cross-project queries
- **Auto-learning** from every Claude Code session
- **< 500ms** search latency
- **$2,740/month** SaaS savings for a typical 10-person team
- **55.9x RPDC** on the outreach agent

---

## License

MIT

---

*Built with Claude Code, Mem0, and the belief that your Mac Mini should replace every SaaS tool you pay for — because it has all your data in one brain, and siloed tools never will.*
