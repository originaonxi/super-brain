# AONXI OS — Evaluation & Experiment Attribution Architecture

> **"How do you know your agent is getting better at that task without evals?"**
>
> **Our answer:** Revenue Per Dollar Spent on Inference + Human Oversight.
> Fully attributable. End-to-end. Every change is an experiment.
> Every experiment has a before/after. You know exactly which change
> drove which improvement.

---

## Why Existing Eval Approaches Fall Short

The industry has five categories of AI evaluation tools. None of them
measure what actually matters for autonomous agents: **did this change
make the business more money per dollar spent?**

### Category 1: Model Benchmarking Platforms
Tools that compare LLMs on standardized benchmarks (MMLU, HumanEval,
GSM8K, GPQA, etc.). YC-backed startups, research labs, leaderboard sites.

**What they measure:** Model quality in lab conditions.
**What they miss:** A model that scores 2% higher on MMLU doesn't mean
your outreach agent books more meetings. Lab performance ≠ production
outcomes. Zero revenue attribution.

### Category 2: LLM Observability Platforms
Tools that trace prompts, log token usage, track latency, and visualize
LLM call chains. Think: logging dashboards for AI.

**What they measure:** Operational health — latency, error rates, cost per token.
**What they miss:** They tell you the system is running. They don't tell you
if it's running *better*. No experiment tracking. No before/after. No
attribution of which change drove which improvement.

### Category 3: Agent Framework Evals
Built-in evaluation suites inside agent frameworks (LangChain, CrewAI,
AutoGen). Test harnesses for prompt quality and tool-calling accuracy.

**What they measure:** Did the agent use the right tool? Did it follow
the prompt? Task completion rate in synthetic scenarios.
**What they miss:** Single-agent focus. No cross-agent causality.
No revenue weighting. No concept of agents improving each other.

### Category 4: MLOps Experiment Trackers
Platforms for tracking ML experiments — hyperparameters, training runs,
model versions, dataset versions.

**What they measure:** Which model version performed best on which dataset.
**What they miss:** Built for training loops, not production agents.
No concept of RPDC. No cross-agent lift. No concept of a "family"
of agents that compound each other's intelligence.

### Category 5: Business Intelligence Dashboards
Metabase, Tableau, Looker, custom dashboards. Track KPIs and metrics.

**What they measure:** Business outcomes (revenue, churn, CSAT).
**What they miss:** No link between agent changes and business outcomes.
They show you revenue went up. They can't tell you *which agent change*
caused it. No experiment isolation. No attribution chain.

### What AONXI Evals Does Differently

| Dimension | Industry Standard | AONXI Evals |
|---|---|---|
| **What it measures** | Model quality OR operational health OR business KPIs | All three, linked end-to-end |
| **Core metric** | Benchmark scores / latency / revenue (pick one) | RPDC — Revenue Per Dollar of Cost (unified) |
| **Attribution** | "Model X is 3% better on math" | "This code change added $4,200/month to outreach" |
| **Cross-agent** | N/A (single model/agent focus) | 13 causal links between 9 agent types |
| **Experiment tracking** | ML training runs (not production agents) | Full before/after on live production agents |
| **Revenue tied** | Separate system (if at all) | Every metric has a revenue weight (0.0-1.0) |
| **Runs where** | Cloud benchmarks / SaaS dashboards | Live production, on your hardware, $0/query |
| **Compound intelligence** | Not measured | CIS — one score for the whole agent family |

**The industry benchmarks models. We benchmark outcomes.**
They tell you which model is better. We tell you which CHANGE made your
business generate more revenue per dollar spent. And we measure whether
that improvement rippled across your entire agent family.

---

## The ONE Metric: RPDC

```
RPDC = Revenue Attributed to Agent / (Inference Cost + Human QC Cost)

Example (Outreach Agent):
  Revenue:        $14,000/month (meetings booked → deals closed)
  Inference cost:  $0.50/month  (local Ollama, electricity only)
  Human QC cost:   $250/month   (5 hrs/month reviewing emails @ $50/hr)

  RPDC = $14,000 / ($0.50 + $250) = 55.9x

  Every $1 you spend on this agent generates $55.90 in revenue.
```

Target RPDC by agent type:

| Agent | Target RPDC | What Drives It |
|-------|------------|----------------|
| Outreach | > 50x | Meetings booked, deal conversion |
| Sales | > 30x | Pipeline value, close rate |
| HR | > 20x | Time saved per hire, acceptance rate |
| IT Helpdesk | > 15x | Auto-resolve rate, ticket volume |
| Support | > 25x | Churn prevented, CSAT score |
| Finance | > 10x | Forecast accuracy, anomaly detection |
| QA | > 40x | Bugs caught early (vs prod cost) |
| Daily Fleet | > 5x | Engagement → warm lead conversion |

---

## Experiment System — The Core Innovation

Every change to an agent is an experiment. No exceptions.

### Experiment Lifecycle

```
1. START EXPERIMENT
   $ python3 evals.py experiment start outreach "switched to 1-paragraph emails"

   → Snapshots ALL current metrics as baseline
   → Returns experiment ID: exp-out-0331-a4f2bc
   → All subsequent metrics can be tagged to this experiment

2. RUN THE CHANGE
   Agent runs with the new configuration.
   Log metrics as they come in:
   $ python3 evals.py log outreach reply_rate 5.2 --experiment exp-out-0331-a4f2bc
   $ python3 evals.py log outreach meetings_booked 14 --experiment exp-out-0331-a4f2bc

3. END EXPERIMENT
   $ python3 evals.py experiment end exp-out-0331-a4f2bc "shorter emails work"

   → Snapshots ALL current metrics as 'after'
   → Calculates deltas for every metric
   → Calculates RPDC before vs after
   → Identifies cross-agent ripple effects
   → Stores full attribution chain
```

### Attribution Chain

```
Code change: "switched to 1-paragraph emails"
     |
     +-> reply_rate: 3.2% -> 5.1% (+59.4%)
     +-> meetings_booked: 8 -> 14 (+75.0%)
     +-> human_qc_minutes: 45 -> 30 (+33.3%)
     |
     v
RPDC: 32.1x -> 55.9x (+23.8x)
     |
     v
Revenue impact: +$6,000/month

CROSS-AGENT RIPPLE:
  outreach.meetings_booked (+75%) -> expect sales.close_rate to improve
    Reason: Better meetings → higher close rate
  outreach.reply_rate (+59%) -> expect sales.avg_deal_size to improve
    Reason: Better replies → more qualified deals
```

### Experiment Leaderboard

```
$ python3 evals.py leaderboard

  EXPERIMENT LEADERBOARD — Which Changes Actually Worked
  ══════════════════════════════════════════════════════════
  Rank  RPDC Delta  Agent         Change
  ──────────────────────────────────────────────────────────
  >> 1    +23.80x   outreach      switched to 1-paragraph emails
   > 2    +12.40x   outreach      added Tuesday healthcare timing
     3     +8.20x   sales         pre-call company brief injection
     4     +5.10x   it_helpdesk   added VPN auto-diagnosis
     5     -2.30x   hr            removed phone screen step
  ══════════════════════════════════════════════════════════
```

This tells you EXACTLY which changes drove which improvements.
No guessing. No "we think it's better." Hard numbers.

---

## Compound Intelligence Score (CIS)

One number that tells you if the whole system is getting smarter.

### Formula

```
CIS = (0.35 × Individual Improvement)
    + (0.25 × Cross-Agent Causal Lift)
    + (0.20 × Experiment Velocity)
    + (0.20 × Memory Compound Rate)
```

### Components

**1. Individual Improvement (35%)**
Weighted average of each agent's week-over-week metric changes.
Metrics are weighted by `revenue_weight` — meetings_booked matters
more than emails_sent.

**2. Cross-Agent Causal Lift (25%)**
13 defined causal links between agents. When outreach.leads_found
improves, does sales.pipeline_value also improve? This measures the
FAMILY EFFECT — agents teaching agents.

Causal links:
```
outreach.leads_found        → sales.pipeline_value
outreach.meetings_booked    → sales.close_rate
outreach.reply_rate         → sales.avg_deal_size
qa.bugs_found               → support.resolution_rate
qa.tests_passed             → it_helpdesk.auto_resolve_rate
brain.search_relevance_avg  → outreach.reply_rate
brain.cross_agent_insights  → outreach.meetings_booked
brain.patterns_detected     → qa.regression_catch_rate
hr.time_per_hire            → it_helpdesk.tickets_resolved
daily_fleet.open_rate       → outreach.reply_rate
finance.forecast_accuracy   → sales.pipeline_value
support.csat_score          → sales.close_rate
support.churn_prevented     → finance.forecast_accuracy
```

**3. Experiment Velocity (20%)**
Are we running experiments? Are they successful?
- Success rate > 50% = positive signal
- More experiments = faster learning
- This prevents the system from becoming stagnant

**4. Memory Compound Rate (20%)**
Is the brain getting smarter?
- More memories + higher search relevance = compounding
- More cross-repo patterns detected = deeper understanding
- More cross-agent insights shared = wider intelligence

### CIS Ratings

| CIS Score | Rating | Meaning |
|-----------|--------|---------|
| +20 to +100 | ACCELERATING | Agents are compounding each other |
| +5 to +20 | IMPROVING | Steady gains |
| -5 to +5 | STABLE | No significant change |
| -20 to -5 | DECLINING | Investigate regressions |
| -100 to -20 | CRITICAL | Major regressions, intervene |

---

## 9 Agent Types, 40+ Metrics

Every metric has:
- **Direction**: "up" (higher is better) or "down" (lower is better)
- **Unit**: display label
- **Revenue weight**: how much this metric contributes to revenue (0.0-1.0)

### Outreach Agent
| Metric | Direction | Unit | Weight | What it measures |
|--------|-----------|------|--------|-----------------|
| leads_found | up | count | 0.15 | Raw pipeline input |
| emails_sent | up | count | 0.05 | Volume (low weight — quantity ≠ quality) |
| reply_rate | up | % | 0.20 | Message quality signal |
| meetings_booked | up | count | 0.35 | **PRIMARY** — this is the outcome |
| revenue_generated | up | $ | 1.00 | Direct attribution |
| cost_per_lead | down | $ | 0.10 | Efficiency |
| human_qc_minutes | down | min | 0.05 | Oversight cost |

### Sales Pipeline Agent
| Metric | Direction | Weight | What it measures |
|--------|-----------|--------|-----------------|
| pipeline_value | up | 0.30 | Total opportunity value |
| close_rate | up | 0.35 | **PRIMARY** — conversion |
| avg_deal_size | up | 0.20 | Deal quality |
| cycle_time_days | down | 0.10 | Speed to close |
| human_qc_minutes | down | 0.05 | Oversight cost |

### HR Agent
| Metric | Direction | Weight |
|--------|-----------|--------|
| resumes_screened | up | 0.10 |
| time_per_hire | down | 0.30 |
| offer_acceptance_rate | up | 0.25 |
| cost_per_hire | down | 0.20 |
| human_qc_minutes | down | 0.05 |

### IT Helpdesk Agent
| Metric | Direction | Weight |
|--------|-----------|--------|
| tickets_resolved | up | 0.15 |
| auto_resolve_rate | up | 0.35 |
| avg_resolution_time | down | 0.25 |
| escalation_rate | down | 0.15 |
| human_qc_minutes | down | 0.05 |

### Support Agent
| Metric | Direction | Weight |
|--------|-----------|--------|
| response_time_seconds | down | 0.15 |
| resolution_rate | up | 0.30 |
| csat_score | up | 0.35 |
| churn_prevented | up | 0.15 |
| human_qc_minutes | down | 0.05 |

### Finance Agent
| Metric | Direction | Weight |
|--------|-----------|--------|
| invoices_processed | up | 0.15 |
| forecast_accuracy | up | 0.40 |
| anomalies_detected | up | 0.25 |
| time_saved_hours | up | 0.15 |
| human_qc_minutes | down | 0.05 |

### QA Agent
| Metric | Direction | Weight |
|--------|-----------|--------|
| tests_generated | up | 0.15 |
| tests_passed | up | 0.20 |
| bugs_found | up | 0.30 |
| false_positive_rate | down | 0.25 |
| regression_catch_rate | up | 0.10 |

### Daily Fleet
| Metric | Direction | Weight |
|--------|-----------|--------|
| emails_delivered | up | 0.20 |
| open_rate | up | 0.40 |
| click_rate | up | 0.30 |
| unsubscribe_rate | down | 0.10 |

### Brain (Super Brain)
| Metric | Direction | Weight |
|--------|-----------|--------|
| memories_count | up | 0.15 |
| search_relevance_avg | up | 0.40 |
| cross_repo_patterns_detected | up | 0.25 |
| cross_agent_insights_shared | up | 0.20 |

---

## CLI Reference

```bash
# Experiments
python3 evals.py experiment start outreach "shorter email subject lines"
python3 evals.py experiment start sales "added pre-call company briefs"
python3 evals.py experiment end exp-out-0331-a4f2bc "subject lines worked"
python3 evals.py experiments                    # list all
python3 evals.py experiments --agent outreach   # filter by agent
python3 evals.py attribution exp-out-0331-a4f2bc  # full chain
python3 evals.py leaderboard                    # rank by impact

# Metrics
python3 evals.py log outreach meetings_booked 14
python3 evals.py log outreach reply_rate 5.2 --experiment exp-out-0331-a4f2bc
python3 evals.py rpdc                           # all agents
python3 evals.py rpdc outreach                  # single agent

# Analysis
python3 evals.py trend outreach --days 30
python3 evals.py dashboard
python3 evals.py compound-score --weeks 4
python3 evals.py report --weeks 2
python3 evals.py agents                         # registry
```

---

## Data Model

```
┌─────────────────────────────────────────────────────────────┐
│  evals.db (SQLite)                                          │
│                                                             │
│  metric_logs          experiments          daily_snapshots   │
│  ─────────────        ────────────         ─────────────── │
│  id (PK)              id (PK)              id (PK)         │
│  agent                agent                agent            │
│  metric               description          date             │
│  value                hypothesis           metrics_json     │
│  experiment_id (FK)   status               rpdc             │
│  ts                   started_at           cis              │
│  week_iso             ended_at                              │
│                       conclusion           rpdc_log         │
│                       metrics_before       ────────         │
│                       metrics_after        agent            │
│                       rpdc_before          revenue          │
│                       rpdc_after           inference_cost   │
│                       rpdc_delta           human_cost       │
│                       revenue_impact       rpdc             │
│                                            period           │
└─────────────────────────────────────────────────────────────┘
```

---

## The Daily Workflow

```
MORNING (automated via cron):
  1. Orchestrator scans all 50 repos
  2. Metrics auto-logged from agent outputs
  3. Daily snapshot saved
  4. CIS calculated
  5. Dashboard pushed to HTML report

DURING THE DAY (human-triggered):
  1. Start experiment before any agent change
  2. Make the change
  3. Log metrics as they come in
  4. End experiment when results are clear

WEEKLY (automated report):
  1. Weekly improvement report generated
  2. Experiment leaderboard updated
  3. RPDC trends calculated
  4. Cross-agent lift measured
  5. CIS trend graphed
```

---

---

## Full System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AONXI EVALUATION ARCHITECTURE                        │
│         From Code Change → Metric Movement → Revenue Impact             │
└─────────────────────────────────────────────────────────────────────────┘

LAYER 1: EXPERIMENT TRACKING
  Every change = an experiment. No exceptions.
  ┌────────────────────────────────────────────────────────────────────┐
  │  experiment start                                                  │
  │    → snapshot ALL current metrics as baseline                      │
  │    → assign experiment ID                                          │
  │    → all subsequent metrics tagged to this experiment               │
  │                                                                    │
  │  agent runs with the change...                                     │
  │                                                                    │
  │  experiment end                                                    │
  │    → snapshot ALL current metrics as 'after'                       │
  │    → calculate deltas for every metric                             │
  │    → calculate RPDC before vs after                                │
  │    → identify cross-agent ripple effects                           │
  │    → store full attribution chain                                  │
  └────────────────────────────────────────────────────────────────────┘

LAYER 2: METRIC COLLECTION (45 metrics across 9 agents)
  ┌────────────────────────────────────────────────────────────────────┐
  │  Every metric has:                                                 │
  │    • direction (up = better / down = better)                       │
  │    • unit (count, %, $, min, days)                                 │
  │    • revenue_weight (0.0 - 1.0): how much it drives revenue        │
  │                                                                    │
  │  Stored in: SQLite (evals.db)                                      │
  │  Indexed by: agent + metric + timestamp + week                     │
  │  Queryable by: experiment, time range, agent                       │
  └────────────────────────────────────────────────────────────────────┘

LAYER 3: RPDC ENGINE (Revenue Per Dollar of Cost)
  ┌────────────────────────────────────────────────────────────────────┐
  │  RPDC = Revenue / (Inference Cost + Human QC Cost)                 │
  │                                                                    │
  │  Revenue:                                                          │
  │    • Direct: revenue_generated (outreach, sales)                   │
  │    • Estimated: meetings * avg_deal * close_rate (pipeline)        │
  │    • Proxy: tickets_resolved * $25, bugs_found * $200 (support/QA) │
  │                                                                    │
  │  Cost:                                                             │
  │    • Inference: $0.0001/query (local Ollama, electricity only)     │
  │    • Human QC: human_qc_minutes * ($50/hr)                         │
  │                                                                    │
  │  Target: > 10x (every $1 generates $10+ revenue)                   │
  │  Outreach Agent actual: 559x ($14K revenue / $25 cost)             │
  └────────────────────────────────────────────────────────────────────┘

LAYER 4: CROSS-AGENT CAUSALITY (13 causal links)
  ┌────────────────────────────────────────────────────────────────────┐
  │                                                                    │
  │  outreach.leads_found ──────→ sales.pipeline_value                 │
  │  outreach.meetings_booked ──→ sales.close_rate                     │
  │  outreach.reply_rate ───────→ sales.avg_deal_size                  │
  │  qa.bugs_found ─────────────→ support.resolution_rate              │
  │  qa.tests_passed ───────────→ it_helpdesk.auto_resolve_rate        │
  │  brain.search_relevance ────→ outreach.reply_rate                  │
  │  brain.insights_shared ─────→ outreach.meetings_booked             │
  │  brain.patterns_detected ───→ qa.regression_catch_rate             │
  │  hr.time_per_hire ──────────→ it_helpdesk.tickets_resolved         │
  │  daily_fleet.open_rate ─────→ outreach.reply_rate                  │
  │  finance.forecast_accuracy ─→ sales.pipeline_value                 │
  │  support.csat_score ────────→ sales.close_rate                     │
  │  support.churn_prevented ───→ finance.forecast_accuracy            │
  │                                                                    │
  │  When source improves and target also improves = causal lift       │
  │  Conservative estimate: min(source_change, target_change)          │
  └────────────────────────────────────────────────────────────────────┘

LAYER 5: COMPOUND INTELLIGENCE SCORE (CIS)
  ┌────────────────────────────────────────────────────────────────────┐
  │                                                                    │
  │  CIS = (0.35 × Individual Agent Improvement)                       │
  │       + (0.25 × Cross-Agent Causal Lift)                           │
  │       + (0.20 × Experiment Velocity)                               │
  │       + (0.20 × Memory Compound Rate)                              │
  │                                                                    │
  │  Scale: -100 (catastrophic) to +100 (exponential compounding)      │
  │                                                                    │
  │  ACCELERATING (+20 to +100): agents compounding each other         │
  │  IMPROVING    (+5 to +20):   steady gains                          │
  │  STABLE       (-5 to +5):    no change                             │
  │  DECLINING    (-20 to -5):   investigate                           │
  │  CRITICAL     (-100 to -20): intervene immediately                 │
  │                                                                    │
  └────────────────────────────────────────────────────────────────────┘

LAYER 6: EXPERIMENT LEADERBOARD
  ┌────────────────────────────────────────────────────────────────────┐
  │  Every completed experiment ranked by RPDC delta.                   │
  │                                                                    │
  │  Rank  RPDC Delta  Agent      Change                               │
  │  ────  ──────────  ─────      ──────                               │
  │  1     +23.80x     outreach   switched to 1-paragraph emails       │
  │  2     +12.40x     outreach   added Tuesday healthcare timing      │
  │  3     +8.20x      sales      pre-call company brief injection     │
  │  4     +5.10x      helpdesk   added VPN auto-diagnosis             │
  │  5     -2.30x      hr         removed phone screen step            │
  │                                                                    │
  │  This is the answer to: "which changes actually worked?"           │
  │  No opinions. No guesses. Hard numbers. Ranked.                    │
  └────────────────────────────────────────────────────────────────────┘
```

---

## Why No Other System Can Do This

1. **Model benchmarking** tools measure lab performance. We measure production revenue.
2. **LLM observability** tools measure operational health. We measure business outcomes.
3. **Agent framework evals** test single agents in isolation. We measure 9 agents teaching each other across 13 causal links.
4. **MLOps experiment trackers** track training runs. We track live production experiments with revenue attribution.
5. **BI dashboards** show that revenue went up. We show WHICH agent change caused it.

No tool in the market combines experiment tracking + revenue attribution +
cross-agent causality + compound intelligence scoring in one system.
We know because we looked.

---

*Built for production outcomes, not lab benchmarks.*
*Revenue Per Dollar of Cost. Fully attributable. End-to-end.*
*The only eval system that measures what matters: money.*
