# AONXI OS — Evaluation & Experiment Attribution Architecture

> **"How do you know your agent is getting better at that task without evals?"**
> — Ritesh Malpani, Co-founder @Benchspan (YC P26)
>
> **Our answer:** Revenue Per Dollar Spent on Inference + Human Oversight.
> Fully attributable. End-to-end. Every change is an experiment.
> Every experiment has a before/after. You know exactly which change
> drove which improvement.

---

## Why This Is Superior to Benchspan

| | Benchspan | AONXI Evals |
|---|---|---|
| **What it measures** | Model quality in lab conditions | Agent outcomes in production |
| **Core metric** | Benchmark scores (MMLU, HumanEval) | RPDC — Revenue Per Dollar of Cost |
| **Attribution** | "This model is 3% better on math" | "This code change added $4,200/month" |
| **Cross-agent** | N/A (single model focus) | 13 causal links between agents |
| **Experiment tracking** | Model comparisons | Full before/after with rollback |
| **Revenue tied** | No | Every metric weighted by revenue impact |
| **Runs where** | Cloud benchmarks | Live production, on your hardware |

**Benchspan benchmarks models. We benchmark outcomes.**
They tell you which model is better. We tell you which CHANGE made your
business generate more revenue per dollar spent.

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

*Built for production outcomes, not lab benchmarks.*
*Revenue Per Dollar of Cost. Fully attributable. End-to-end.*
*Superior to Benchspan because we measure what matters: money.*
