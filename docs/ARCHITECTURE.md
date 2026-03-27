# Architecture: Super Brain

## System Overview

Super Brain is a **distributed memory architecture** that unifies 55+ autonomous projects into a single queryable intelligence layer. It operates on three planes: **Ingestion** (how memories enter), **Storage** (how they're organized), and **Retrieval** (how they're surfaced).

---

## The Three Planes

### Plane 1: Ingestion

Memories enter the brain through three channels:

```
                    +------------------+
                    |   INGESTION      |
                    +------------------+
                    |                  |
          +---------+--------+---------+
          |                  |         |
    +-----v------+   +------v---+  +--v-----------+
    | Manual CLI |   | Auto Hook|  | Programmatic |
    | mem0_push  |   | PostTool |  | brain.py SDK |
    | mem0_search|   | Use fire |  | REST API     |
    +------------+   +----------+  +--------------+
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
|   +---------------------------+                                |
|   | Structured Attributes     |                                |
|   | day, hour, quarter,       |                                |
|   | day_of_week, week_of_year |                                |
|   +---------------------------+                                |
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

## Connection Topology

The brain doesn't just store isolated memories — it understands how projects connect:

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
| asm-replication  |     | news-briefing    |     | CI_Accenture
| attention-scratch|     | space-wonder     |     | CI_HubSpot
| llm-calibration  |---->| echo             |     | AdIntel_sn
| moe-efficiency   |     | agi-possible     |     | CompIntel
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
