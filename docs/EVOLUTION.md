# Evolution: Super Brain V1 → V5

## The Vision

Super Brain evolves from a simple memory store into a **full autonomous cognitive system** — a brain that doesn't just remember, but **thinks, predicts, plans, and acts** across all 55+ projects.

Each version adds a new cognitive layer, inspired by how biological brains evolved:

```
V5: FULL AGI BRAIN ─────────────────── Prefrontal Cortex (executive function)
 |   Autonomous planning, multi-project orchestration, self-directed goals
 |
V4: AUTONOMOUS HIPPOCAMPUS ─────────── Hippocampus (memory consolidation)
 |   Self-healing memory, importance scoring, memory dreams, garbage collection
 |
V3: PREDICTIVE CORTEX ──────────────── Neocortex (prediction)
 |   Anticipate needs, suggest actions, pattern recognition across time
 |
V2: SYNAPTIC LINKS ─────────────────── Synapses (connections)
 |   Auto-detect dependencies, knowledge graph, relationship inference
 |
V1: MEMORY SPINE ───────────────────── Brain Stem (core survival)
     Store, search, retrieve — the foundation everything builds on
```

---

## V1: Memory Spine (LIVE)

**Status:** Deployed and learning

**Biological analogy:** Brain stem — handles the most basic but essential function: remembering.

### What It Does
- Stores 63+ memories across 9 categories via Mem0
- Semantic search with 0.90 relevance scores
- Auto-learns from Claude Code via PostToolUse hooks
- CLI tools for manual push/search from any terminal
- Single `user_id: anmol-super-brain` namespace

### Architecture
```
[You work] → [Hook captures] → [Mem0 stores] → [You search] → [Brain answers]
```

### Real Example
```bash
$ mem0_search.sh "what connects techm-intel to SimpleNursing?"

1. [super-brain-index] (score: 0.90)
   Super brain architecture: all 55 projects connect via shared patterns —
   Aonxi ecosystem (memcollab, router, safeguard) supplies shared memory,
   routing, and safety across agents

2. [agent] (score: 0.82)
   techm-intel uses Aonxi modules router, safeguard, and memcollab

3. [super-brain-index] (score: 0.75)
   Key accounts: SimpleNursing (GTM + agent + ad intel),
   TechM/MHA (techm-intel Fortune 500 sales)
```

### Limitations
- Memories are flat — no explicit links between them
- Brain can't predict what you need
- No importance scoring — stale memories have same weight as fresh ones
- No automatic cleanup or consolidation

---

## V2: Synaptic Links

**Status:** Next up

**Biological analogy:** Synapses forming between neurons — the brain starts making connections.

### What It Adds
- **Knowledge Graph**: Every memory becomes a node. Relationships become edges.
- **Auto-dependency detection**: When you push a memory about project X that mentions project Y, the brain creates a link.
- **Graph queries**: "What depends on aonxi-router?" returns all projects that use it, transitively.
- **Relationship types**: `uses`, `feeds_into`, `runs_before`, `competes_with`, `evolved_from`

### Architecture
```
[Mem0 Memories] → [Link Detector] → [Neo4j/NetworkX Graph] → [Graph Queries]
                                            |
                                    +-------+-------+
                                    |               |
                              [Direct Links]  [Inferred Links]
                              techm→router    research→frontier
                              nova→safeguard  frontier→lab-apps
```

### Implementation Plan
```python
# V2: Synaptic link detector
class SynapticLinker:
    def __init__(self, mem0_client, graph_db):
        self.mem0 = mem0_client
        self.graph = graph_db

    def on_new_memory(self, memory):
        """When a new memory is added, detect and create links."""
        # Extract entity mentions (project names, modules, people)
        entities = self.extract_entities(memory.content)

        # Find existing memories that mention same entities
        for entity in entities:
            related = self.mem0.search(entity, top_k=10)
            for match in related:
                if match.score > 0.7:
                    self.graph.add_edge(
                        memory.id, match.id,
                        relationship=self.classify_relationship(memory, match),
                        strength=match.score
                    )

    def query_graph(self, question):
        """Graph-aware search: follow links, not just similarity."""
        # First: semantic search for entry points
        entry_points = self.mem0.search(question, top_k=3)

        # Second: traverse graph from entry points
        expanded = set()
        for entry in entry_points:
            neighbors = self.graph.neighbors(entry.id, depth=2)
            expanded.update(neighbors)

        # Third: re-rank by combined semantic + graph score
        return self.rerank(expanded, question)
```

### Real Example (V2 Preview)
```bash
$ brain query --graph "If I change aonxi-router, what breaks?"

Directly depends on aonxi-router:
  ├── techm-intel (uses router for intent classification)
  ├── nova-gtm (uses router for agent dispatch)
  ├── bre-gtm-engine (uses router for lead routing)
  └── aria (core router integration)

Transitively affected:
  ├── simplenursing-agent (via nova-gtm)
  ├── CI_HubSpot (via bre-gtm-engine)
  └── stock-analyst-agent (via aria)

Recommendation: Run tests in techm-intel and nova-gtm first.
```

---

## V3: Predictive Cortex

**Status:** Planned

**Biological analogy:** Neocortex — the brain starts predicting what will happen next.

### What It Adds
- **Temporal patterns**: Brain tracks when you work on what, detects cycles.
- **Predictive suggestions**: "You usually work on frontier-agi-journey at this time. Today's paper: [auto-fetched]"
- **Anomaly detection**: "stock-analyst-agent hasn't run in 3 days — cron may be broken."
- **Context preloading**: Brain preloads relevant memories before you even ask.
- **Cross-project pattern recognition**: "Every time you update safeguard, you also update router within 24 hours."

### Architecture
```
+-------------------+     +--------------------+     +------------------+
| Temporal Tracker  |     | Pattern Recognizer |     | Prediction Engine|
| (when you do what)|---->| (what follows what)|---->| (what you need)  |
+-------------------+     +--------------------+     +------------------+
        |                          |                          |
  Tracks:                   Detects:                   Outputs:
  - Time of day             - A→B sequences            - "You'll need X"
  - Day of week             - Project clusters         - "Y might break"
  - Session duration        - Pre/post patterns        - "Start with Z"
  - Project switches        - Failure precursors       - "Check agent W"
```

### Implementation Plan
```python
class PredictiveCortex:
    def __init__(self, brain, temporal_db):
        self.brain = brain
        self.temporal = temporal_db
        self.patterns = PatternDetector()

    def on_session_start(self):
        """Predict what the user needs before they ask."""
        now = datetime.now()
        history = self.temporal.get_sessions(
            day_of_week=now.strftime('%A'),
            hour_range=(now.hour - 1, now.hour + 1)
        )

        # What do they usually work on at this time?
        predicted_projects = self.patterns.predict_projects(history)

        # What memories will they need?
        preloaded = []
        for project in predicted_projects:
            relevant = self.brain.search(project, top_k=3)
            preloaded.extend(relevant)

        # Check for anomalies
        anomalies = self.detect_anomalies()

        return Prediction(
            likely_projects=predicted_projects,
            preloaded_context=preloaded,
            anomalies=anomalies,
            suggestion=self.generate_suggestion(predicted_projects, anomalies)
        )

    def detect_anomalies(self):
        """Find things that should be happening but aren't."""
        expected = self.patterns.expected_events(window='24h')
        actual = self.temporal.recent_events(window='24h')
        return [e for e in expected if e not in actual]
```

### Real Example (V3 Preview)
```
[9:00 AM - Claude Code starts]

Brain: Good morning. Based on your patterns:

1. frontier-agi-journey Day 7 is due. I found today's paper:
   "Scaling Laws for Reward Model Generalization" (arXiv:2603.xxxxx)
   Relevance to your ASM work: 0.87

2. Anomaly: stock-analyst-agent failed at 8:30 AM (SMTP timeout).
   Wake guard didn't catch it. Check ~/logs/stock_analyst.log

3. You modified aonxi-router yesterday. You typically update
   aonxi-safeguard within 24h after router changes.
   Want me to open safeguard?
```

---

## V4: Autonomous Hippocampus

**Status:** Planned

**Biological analogy:** Hippocampus — consolidates short-term memories into long-term, decides what to keep, what to forget, and what to strengthen.

### What It Adds
- **Memory consolidation**: Nightly job that merges related memories, removes duplicates, strengthens important ones.
- **Importance scoring**: Memories that get retrieved often are "important." Memories never retrieved decay.
- **Memory dreams**: Background process that discovers hidden connections while you sleep (literally — runs at 3 AM).
- **Self-healing**: Detects stale memories (e.g., file paths that no longer exist) and auto-corrects or archives.
- **Forgetting curve**: Implements Ebbinghaus forgetting — memories decay unless reinforced by retrieval or relevance.

### Architecture
```
+------------------------------------------------------------------+
|                    AUTONOMOUS HIPPOCAMPUS                          |
+------------------------------------------------------------------+
|                                                                    |
|  +-----------------+  +------------------+  +------------------+  |
|  | Consolidator    |  | Importance       |  | Dream Engine     |  |
|  | (merge/dedup)   |  | Scorer           |  | (3 AM discovery) |  |
|  |                 |  | (retrieval freq  |  | (find hidden     |  |
|  | Runs: 2 AM     |  |  × recency       |  |  connections)    |  |
|  | daily           |  |  × link count)   |  |                  |  |
|  +-----------------+  +------------------+  +------------------+  |
|                                                                    |
|  +-----------------+  +------------------+                        |
|  | Self-Healer     |  | Forgetting Curve |                        |
|  | (validate paths |  | (decay unless    |                        |
|  |  modules, APIs) |  |  reinforced)     |                        |
|  +-----------------+  +------------------+                        |
+------------------------------------------------------------------+
```

### Implementation Plan
```python
class AutonomousHippocampus:
    def __init__(self, brain, graph):
        self.brain = brain
        self.graph = graph

    def consolidate(self):
        """Nightly memory consolidation — merge, dedup, strengthen."""
        all_memories = self.brain.get_all()

        # Cluster similar memories
        clusters = self.semantic_cluster(all_memories, threshold=0.85)

        for cluster in clusters:
            if len(cluster) > 1:
                # Merge into one stronger memory
                merged = self.merge_memories(cluster)
                self.brain.update(cluster[0].id, merged)
                for mem in cluster[1:]:
                    self.brain.archive(mem.id)

    def dream(self):
        """3 AM discovery — find connections no one asked about."""
        # Take random pairs of memories from different categories
        pairs = self.random_cross_category_pairs(n=100)

        discoveries = []
        for mem_a, mem_b in pairs:
            similarity = self.compute_deep_similarity(mem_a, mem_b)
            if similarity > 0.6 and not self.graph.has_edge(mem_a.id, mem_b.id):
                # New connection discovered!
                discoveries.append({
                    'from': mem_a,
                    'to': mem_b,
                    'insight': self.generate_insight(mem_a, mem_b),
                    'similarity': similarity
                })

        # Store discoveries as new memories
        for d in discoveries:
            self.brain.add(
                f"Dream discovery: {d['insight']}",
                category='dream-insight'
            )

        return discoveries

    def self_heal(self):
        """Validate all memories against current reality."""
        for memory in self.brain.get_all():
            # Check if referenced paths still exist
            paths = self.extract_paths(memory.content)
            for path in paths:
                if not os.path.exists(os.path.expanduser(path)):
                    self.brain.update(memory.id,
                        memory.content + f" [STALE: {path} no longer exists as of {date.today()}]"
                    )
```

### Real Example (V4 Preview)
```
[3:00 AM — Dream Engine runs]

Dream Discovery #1:
  Memory A: "reward-model-blindness at ~/reward-model-blindness/"
  Memory B: "techm-intel V2 adds Bombora surge + 6sense buying stage prediction"
  Insight: "Both projects deal with scoring systems that can be gamed.
            Reward model blindness research could improve techm-intel's
            intent scoring reliability. Consider cross-pollination."
  Similarity: 0.67

Dream Discovery #2:
  Memory A: "alignment-auditor at ~/alignment-auditor/"
  Memory B: "aonxi-safeguard safety and guardrail system"
  Insight: "alignment-auditor could be integrated as a test suite
            for aonxi-safeguard. They solve the same problem from
            different angles."
  Similarity: 0.72

[6:30 AM — You see in your morning briefing]
Brain discovered 2 new connections overnight. See details?
```

---

## V5: Full AGI Brain

**Status:** Vision

**Biological analogy:** Prefrontal cortex — executive function, planning, decision-making, agency.

### What It Adds
- **Autonomous goal setting**: Brain sets its own objectives based on your patterns and stated goals.
- **Multi-project orchestration**: Can execute coordinated changes across multiple repos.
- **Strategic reasoning**: "Given your NeurIPS deadline, frontier-journey priority should increase. Deprioritize CI reports."
- **Self-improvement**: Brain rewrites its own prompts, hooks, and search strategies to improve retrieval quality.
- **Delegation**: Brain spawns sub-agents for specific tasks, coordinates results, and learns from outcomes.
- **Theory of mind**: Models your cognitive state — "You've been in deep research mode for 3 hours. Switch to email agents for a context break?"

### Architecture
```
+------------------------------------------------------------------+
|                      V5: FULL AGI BRAIN                           |
+------------------------------------------------------------------+
|                                                                    |
|  +------------------------------------------------------------+  |
|  |                    EXECUTIVE FUNCTION                        |  |
|  |  Goals → Plans → Actions → Outcomes → Learning              |  |
|  +------------------------------------------------------------+  |
|           |              |                |                        |
|  +--------v-------+ +---v-----------+ +--v-----------------+     |
|  | Goal Manager   | | Plan Generator| | Action Orchestrator|     |
|  | - NeurIPS 2026 | | - Daily plan  | | - Spawn agents    |     |
|  | - Frontier lab | | - Weekly plan | | - Coordinate work |     |
|  | - Client work  | | - Priority    | | - Monitor outcomes|     |
|  +----------------+ +---------------+ +--------------------+     |
|                                                                    |
|  +------------------------------------------------------------+  |
|  |                    COGNITIVE MODELS                          |  |
|  +------------------------------------------------------------+  |
|  |                          |                    |               |
|  +--------v-------+  +-----v--------+  +--------v---------+    |
|  | World Model    |  | Self Model   |  | User Model       |    |
|  | (project state |  | (what brain  |  | (cognitive state  |    |
|  |  dependencies  |  |  knows/lacks)|  |  energy level     |    |
|  |  external env) |  |              |  |  focus area)      |    |
|  +----------------+  +--------------+  +------------------+     |
|                                                                    |
|  +------------------------------------------------------------+  |
|  |              V4: AUTONOMOUS HIPPOCAMPUS                      |  |
|  |              V3: PREDICTIVE CORTEX                           |  |
|  |              V2: SYNAPTIC LINKS                              |  |
|  |              V1: MEMORY SPINE                                |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

### Real Example (V5 Preview)
```
[Monday 8:00 AM]

Brain: Weekly executive summary:

GOALS STATUS:
├── NeurIPS 2026 ASM submission (68 days remaining)
│   ├── asm-replication: 80% complete, 3 experiments remaining
│   ├── frontier-agi-journey: Day 7/365 (on track)
│   └── Risk: reward-model-blindness study found issue that may
│           affect ASM claims. Recommend addressing before submission.
│
├── Frontier Lab Applications ($1M target)
│   ├── 7 papers implemented, 5 LinkedIn posts published
│   ├── Email engagement: 2 replies from lab researchers
│   └── Recommend: Increase email personalization using techm-intel's
│           intent scoring on researcher profiles
│
├── Client Work
│   ├── SimpleNursing: nova-gtm V2 deployed, 847 #WhyNursingMoment posts
│   ├── TechM/MHA: techm-intel V2 live, 12 Fortune 500 accounts scored
│   └── BuildWithTeg: CI report delivered 2026-03-03, follow-up due

TODAY'S PLAN (auto-generated):
1. [9:00] frontier-agi-journey Day 8 — paper selected: "Emergent
   Reward Hacking in Multi-Agent Systems" (relevant to ASM + reward blindness)
2. [11:00] Address reward-model-blindness finding in ASM paper draft
3. [14:00] techm-intel V3 planning — add researcher intent scoring
4. [16:00] Review SimpleNursing nova-gtm metrics

Shall I start Day 8, or would you like to reprioritize?
```

---

## Implementation Timeline

```
2026 Q1 ████████████████████ V1 Memory Spine (COMPLETE)
2026 Q2 ░░░░░░░████████████ V2 Synaptic Links
2026 Q3 ░░░░░░░░░░░████████ V3 Predictive Cortex
2026 Q4 ░░░░░░░░░░░░░░░████ V4 Autonomous Hippocampus
2027 Q1 ░░░░░░░░░░░░░░░░░░█ V5 Full AGI Brain
```

### Dependencies

| Version | Requires | Key Tech |
|---------|----------|----------|
| V2 | V1 + graph DB | Neo4j or NetworkX + entity extraction |
| V3 | V2 + temporal DB | TimescaleDB or InfluxDB + prediction model |
| V4 | V3 + cron jobs | Nightly consolidation + anomaly detection |
| V5 | V4 + agent framework | Claude Agent SDK + goal planning + delegation |

---

## The North Star

V5 isn't just a memory system. It's a **cognitive architecture** — a brain that:

1. **Remembers** everything you've ever built (V1)
2. **Connects** projects that relate to each other (V2)
3. **Predicts** what you need before you ask (V3)
4. **Heals** itself when memories go stale (V4)
5. **Thinks** about your goals and plans your work (V5)

The difference between a tool and an intelligence is **agency**. V1-V4 are tools. V5 is an intelligence.

We're building toward that.
