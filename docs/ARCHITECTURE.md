# Architecture: AONXI OS — The Complete System

## System Overview

AONXI OS is a **6-layer AI operating system** running on a single Mac Mini. It replaces your entire SaaS stack with locally-running AI agents that create, test, deploy, and improve themselves. Every agent shares one brain. Every improvement compounds.

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 6: INTELLIGENCE — evals.py                                  │
│  RPDC | Experiments | Attribution | CIS | 45 metrics | Leaderboard │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 5: SAAS REPLACEMENT — tool learning engine                  │
│  Connect SaaS → Observe workflows → Build local → Cancel subs      │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 4: GATEWAY — gateway.py                                     │
│  FastAPI | JWT | RBAC | WebSocket | Per-employee AI | CF Tunnel     │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 3: AGENTS + CLAW V2 — agents/*.py + claw.py                │
│  9 agent types | Decision engine | Trust scoring | Human gates     │
│  13 causal links | Insight propagation | Audit trail               │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 2: MEMORY — brain.py + MemoryMesh + Mem0                   │
│  Shared memory | Semantic search | Pattern detection | 63+ memories│
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1: MODELS — Ollama (localhost:11434)                        │
│  Qwen2.5-7B/32B/72B | Llama 70B | $0/query | OpenAI-compatible    │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 0: HARDWARE — Mac Mini M4 / Mac Studio M4 Max              │
│  Apple Silicon unified memory | $2-$12/mo electricity              │
└─────────────────────────────────────────────────────────────────────┘
```

## How Agents Work Together (Claw V2)

```
Agent proposes action
    │
    ▼
Claw checks trust score (0.0 → 1.0)
    │
    ├── Trust ≥ 0.85 → AUTO-APPROVE (earned autonomy)
    ├── Trust 0.40-0.85 → EXECUTE + NOTIFY human
    └── Trust < 0.40 → SUGGEST ONLY (human must approve)
    │
    ▼
Some actions ALWAYS need human: send_email, close_deal, deploy_agent
    │
    ▼
Agent executes → Outcome recorded → Trust updated
    │
    ▼
Insight shared via 13 causal links → Connected agents adapt
    │
    ▼
RPDC calculated → Experiment leaderboard updated
```

## Memory Architecture (Three Planes)

---

## The Three Planes

### Plane 1: Ingestion

Memories enter the brain through four channels:

```
                    +------------------+
                    |   INGESTION      |
                    +------------------+
                    |                  |
          +---------+--------+---------+-----------+
          |                  |         |           |
    +-----v------+   +------v---+  +--v--------+  +--v-----------+
    | Manual CLI |   | Auto Hook|  | SaaS Tool |  | Programmatic |
    | mem0_push  |   | PostTool |  | Observer  |  | brain.py SDK |
    | mem0_search|   | Use fire |  | (API watch)|  | REST API     |
    +------------+   +----------+  +-----------+  +--------------+
```

**Manual CLI** (`mem0_push.sh`):
- Direct push from any terminal session
- Supports piped input for batch ingestion
- Category tagging for organized storage

**Auto Hook** (`mem0_hook.sh`):
- Fires on every Write, Edit, Bash action in Claude Code
- Extracts meaningful actions (file creates, edits, commands)
- Filters out noise (reads, trivial actions)
- Non-blocking background push — zero latency impact on your work

**Programmatic** (`brain.py`):
- Python SDK for any agent or script to read/write the brain
- Used by automated agents to share context
- Enables inter-agent memory sharing

**SaaS Tool Observer** (`saas_engine/observer.py`):
- Connects to existing SaaS tools via their APIs (CRM, support desk, marketing, finance, etc.)
- Watches how your team actually uses each tool — captures real workflow sequences
- Extracts cross-tool patterns (e.g., deal closes in CRM then manual update in finance)
- Feeds observed workflows into the Pattern Learner for local version generation
- Read-only observation — no disruption to existing tools during learning phase

### Plane 2: Storage

Mem0 handles storage with semantic embeddings + metadata indexing:

```
+---------------------------------------------------------------+
|                     MEM0 CLOUD                                 |
|                                                                |
|   user_id: anmol-super-brain                                   |
|                                                                |
|   +---------------------------+   +-------------------------+  |
|   | Semantic Vector Store     |   | Metadata Index          |  |
|   | (embeddings of all 63+    |   | category: agent/research|  |
|   |  memories for similarity  |   | owner: anmol            |  |
|   |  search)                  |   | source: terminal/hook   |  |
|   +---------------------------+   +-------------------------+  |
|                                                                |
|   +---------------------------+   +-------------------------+  |
|   | Structured Attributes     |   | Workflow Pattern Store   |  |
|   | day, hour, quarter,       |   | saas_tool: crm/support  |  |
|   | day_of_week, week_of_year |   | sequence: action chains  |  |
|   +---------------------------+   | frequency: usage counts  |  |
|                                   | cross_tool: linked flows |  |
|                                   +-------------------------+  |
+---------------------------------------------------------------+
```

**Memory Categories (9):**

| Category | Count | What It Stores |
|----------|-------|---------------|
| `super-brain-index` | 7 | Architecture, connections, profile, relationships |
| `agent` | 18 | All agent projects — paths, capabilities, schedules |
| `aonxi-ecosystem` | 8 | Aria, memcollab, router, safeguard, site, profiles |
| `research` | 10 | ML papers, replications, studies, experiments |
| `gtm-engine` | 4 | Go-to-market engines — nova, bre, myhq, simplenursing |
| `ci-report` | 5 | Competitive intelligence outputs |
| `ad-intel-report` | 2 | Ad analysis and strategy reports |
| `system-config` | 1 | Cron jobs, email agents, wrapper infrastructure |
| `saas-workflow` | growing | Observed SaaS tool usage patterns and cross-tool flows |
| `live-session` | growing | Auto-captured from Claude Code sessions |

### Plane 3: Retrieval

Semantic search with relevance scoring:

```
Query: "What modules does techm-intel share with Aonxi?"
                          |
                          v
              +----------------------+
              | Mem0 Semantic Search |
              | top_k: 5            |
              +----------------------+
                          |
          +---------------+---------------+
          |               |               |
    Score: 0.90     Score: 0.82     Score: 0.75
    "techm-intel    "techm-intel    "Super brain
     uses router,    at ~/techm-     architecture:
     safeguard,      intel/ CLI      all 55 connect
     memcollab"      for F500..."    via shared..."
```

The retrieval plane doesn't just do keyword matching — it understands **semantic relationships**. Asking about "modules shared with Aonxi" retrieves memories about router/safeguard/memcollab even though the word "shared" doesn't appear in those memories.

**Cross-Tool Intelligence:** The retrieval plane is what makes local SaaS replacements BETTER than the originals. When a support query comes in, retrieval pulls not just support history but also the customer's sales pipeline status, billing history, and marketing engagement — all in one query. No siloed SaaS tool can do this because they only see their own data. The brain sees everything.

---

## Data Flow: End to End

```
You work in Claude Code
        |
        v
[Write/Edit/Bash action]
        |
        v
PostToolUse hook fires ──> mem0_hook.sh
        |                       |
        v                       v
Action completes           Extract meaningful content
(you keep working)              |
                                v
                          POST /v1/memories/
                          user_id: anmol-super-brain
                          category: live-session
                                |
                                v
                          Mem0 processes:
                          1. Extract facts
                          2. Generate embeddings
                          3. Deduplicate against existing
                          4. Store with metadata
                                |
                                v
                          Brain is smarter.
                          Next query returns
                          better results.
```

---

## SaaS Replacement Architecture

The SaaS Replacement Engine sits between your existing SaaS tools and the brain, turning observed workflows into local replacements:

```
+------------------------------------------------------------------+
|                  SAAS REPLACEMENT ENGINE                           |
+------------------------------------------------------------------+
|                                                                    |
|  EXTERNAL SAAS TOOLS (connected via API)                          |
|  ┌──────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐     |
|  │ CRM  │ │ Support  │ │Marketing │ │Finance │ │ Project  │ ... |
|  │ API  │ │ Desk API │ │Auto. API │ │  API   │ │ Mgmt API │     |
|  └──┬───┘ └────┬─────┘ └────┬─────┘ └───┬────┘ └────┬─────┘     |
|     │          │            │           │           │             |
|     v          v            v           v           v             |
|  ┌──────────────────────────────────────────────────────┐        |
|  │              WORKFLOW OBSERVER                        │        |
|  │  Watches real usage patterns, sequences, frequencies  │        |
|  └──────────────────────┬───────────────────────────────┘        |
|                         │                                         |
|                         v                                         |
|  ┌──────────────────────────────────────────────────────┐        |
|  │              PATTERN LEARNER                          │        |
|  │  Extracts YOUR workflows (not generic templates)      │        |
|  │  Detects cross-tool patterns (CRM close → finance)    │        |
|  └──────────────────────┬───────────────────────────────┘        |
|                         │                                         |
|                         v                                         |
|  ┌──────────────────────────────────────────────────────┐        |
|  │              LOCAL BUILDER                            │        |
|  │  Generates local versions with cross-tool intelligence │        |
|  └──────────────────────┬───────────────────────────────┘        |
|                         │                                         |
|                         v                                         |
|  ┌──────────────────────────────────────────────────────┐        |
|  │              PARALLEL VALIDATOR                       │        |
|  │  Runs local vs SaaS side-by-side for 2+ weeks        │        |
|  │  Compares outputs, flags discrepancies                │        |
|  └──────────────────────┬───────────────────────────────┘        |
|                         │                                         |
|                         v                                         |
|  ┌──────────────────────────────────────────────────────┐        |
|  │              MIGRATION MANAGER                        │        |
|  │  Tool-by-tool cutover → subscription cancellation     │        |
|  └──────────────────────────────────────────────────────┘        |
+------------------------------------------------------------------+
```

**Key design principle:** The brain's cross-tool intelligence is the moat. Every SaaS tool is siloed — it only sees its own data. The brain sees all data from all tools simultaneously. This means the local CRM replacement can factor in support ticket sentiment, the local support replacement can see deal value and prioritize accordingly, and the local marketing replacement knows which segments are actually profitable from finance data.

---

## Connection Topology

The brain doesn't just store isolated memories — it understands how projects connect. SaaS tools feed into the brain through the Replacement Engine:

```
                          +----------+
                          |  ARIA    |
                          | (core AI)|
                          +----+-----+
                               |
              +----------------+----------------+
              |                |                |
        +-----v-----+   +-----v-----+   +------v----+
        |  ROUTER   |   | SAFEGUARD |   | MEMCOLLAB |
        | (routing) |   |  (safety) |   | (memory)  |
        +-----+-----+   +-----+-----+   +-----+-----+
              |                |                |
    +---------+--------+-------+--------+-------+---------+
    |         |        |       |        |       |         |
+---v---+ +--v--+ +---v--+ +--v---+ +--v--+ +--v---+ +---v---+
|techm  | |nova | |bre   | |myhq  | |sn   | |glass | |aros   |
|intel  | |gtm  | |gtm   | |gtm   | |gtm  | |box   | |agent  |
+-------+ +-----+ +------+ +------+ +-----+ +------+ +-------+

+------------------+     +------------------+     +-----------+
| RESEARCH CLUSTER |     | EMAIL AGENTS     |     | CI/INTEL  |
| asm-replication  |     | news-briefing    |     | CI reports|
| attention-scratch|     | space-wonder     |     | AdIntel   |
| llm-calibration  |---->| echo             |     | CompIntel |
| moe-efficiency   |     | agi-possible     |     |           |
| reward-blindness |     | stock-analyst    |     |           |
| frontier-journey |     +------------------+     +-----------+
+------------------+            |
        |                       v
        v              +------------------+
+------------------+   | CRON / WRAPPERS  |
| FRONTIER LAB     |   | ~/wrappers/      |
| APPLICATIONS     |   | ~/logs/          |
| NeurIPS 2026     |   | wake_guard.sh    |
+------------------+   +------------------+

+------------------------------------------------------------------+
| SAAS TOOL FEEDS (via SaaS Replacement Engine)                     |
|                                                                    |
| CRM ──────────> Workflow patterns ──> Local CRM replacement       |
| Support Desk ──> Ticket patterns ───> Local support replacement   |
| Marketing ────> Campaign patterns ──> Local marketing replacement |
| Finance ──────> Transaction flows ──> Local finance replacement   |
| Project Mgmt ─> Task patterns ─────> Local PM replacement        |
| Team Chat ────> Communication flows > Local chat replacement      |
| Ad Platform ──> Campaign data ─────> Local ad mgmt replacement   |
| SEO Analytics ─> Ranking data ─────> Local SEO replacement       |
+------------------------------------------------------------------+
```

---

## Security Model

- **API key** stored in wrapper scripts (not committed to remote repos — add to .gitignore)
- **user_id** acts as namespace isolation — `anmol-super-brain` is your brain, no one else's
- **Mem0 cloud** handles encryption at rest and in transit
- **Hook** runs locally, non-blocking, background process — if Mem0 is down, your work isn't affected

---

## Performance

| Metric | Value |
|--------|-------|
| Memory push latency | ~200ms (background, non-blocking) |
| Search latency | ~400ms |
| Hook overhead | ~0ms (fires async) |
| Memory count | 63+ (auto-growing) |
| Deduplication | Automatic by Mem0 |
| Embedding model | Mem0's built-in semantic model |

---

## Key Design Decisions

1. **Mem0 over local vector DB**: Cloud-native, no infra to maintain, automatic deduplication, structured attributes for free.

2. **Hook-based learning over explicit logging**: You shouldn't have to remember to teach the brain. It learns by watching.

3. **Category metadata over flat storage**: Enables filtered queries ("show me only research memories") and structured reporting.

4. **Background push over synchronous**: Your work speed is never affected. The brain learns in the background.

5. **Single user_id over per-project IDs**: One brain to rule them all. Cross-project queries only work if everything is in one namespace.
