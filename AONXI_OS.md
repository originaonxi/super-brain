# AONXI OS — The Complete Architecture

> **One Mac Mini M4. Replacing every SaaS tool you pay for. Zero per-query cost.**
>
> Your Mac Mini is a self-learning SaaS factory. It watches how you use your
> existing tools, learns YOUR specific workflows, then builds local versions
> that are BETTER than the originals — because it has ALL your data in one brain.
> Siloed SaaS tools can't talk to each other. Your Mac Mini can.
>
> **Live site:** [https://originaonxi.github.io/super-brain/](https://originaonxi.github.io/super-brain/)

---

## The Vision in One Sentence

A Mac Mini in every office — it doesn't just serve AI, it replaces every SaaS
subscription you pay for by learning your workflows and building local versions
that have cross-tool intelligence no siloed cloud tool can match.

---

## The Three Business Models

### Model 1: The Individual / SMB
Mac Mini at your home or office.
You and your team connect from anywhere in the world via Cloudflare Tunnel.
One login per person. Their AI knows their job, their tools, their style.
They get a customized Claude — not a generic chatbot.

```
Your Mac Mini (home/office)
    │
    ├── Cloudflare Tunnel → aonxi.yourcompany.com (HTTPS, globally accessible)
    │
    ├── Employee 1 (CEO) → AI tuned for strategy, investor comms, decisions
    ├── Employee 2 (Sales) → AI tuned for outreach, CRM, proposals
    ├── Employee 3 (Support) → AI tuned for tickets, escalations, empathy
    └── Employee 4 (Dev) → AI tuned for code review, docs, PRs
```

**Cost to you:** $15/month electricity.
**What you charge:** $50–200/seat/month.
**Margin:** 90%+.

---

### Model 2: The WeWork / Office Building Model
One Mac Studio M4 Max per building.
Every person who connects to that building's WiFi gets access to the building's AI.
The building sells AI access as an amenity — like WiFi.
You sell to building management companies, not to individuals.

```
WeWork Building (500 members)
    │
    ├── Mac Studio M4 Max 64GB (in server room or closet)
    │
    ├── Captive portal / QR code → members get AI access
    ├── Building management → usage dashboard, billing, control
    ├── Members → hot-desk AI, meeting prep, email drafting
    └── Enterprise tenants → their own isolated AI workspace
```

**You sell to:** WeWork, IWG, Regus, Industrious, CBRE, JLL, building owners.
**Price:** $12,900 setup + $500/month support.
**Their margin:** They charge $29/month per member. 500 members = $14,500/month.
**Net profit per building:** $14,000/month. Recurring. Forever.
**TAM:** 1.2M commercial office buildings in the USA alone.

---

### Model 3: The Enterprise / Department Model
Mac Studio cluster per department.
HR has its own AI. Sales has its own AI. IT has its own AI. Finance has its own.
All connected via Super Brain — they learn from each other.
But data is siloed — HR data doesn't leak to Sales.

```
Enterprise (500+ people)
    │
    ├── Mac Studio A → HR Department AI (resumes, policies, PTO, onboarding)
    ├── Mac Studio B → Sales Department AI (leads, proposals, CRM)
    ├── Mac Studio C → IT Helpdesk AI (tickets, access, infra docs)
    ├── Mac Studio D → Finance AI (P&L, invoices, forecasting)
    │
    └── Super Brain (shared) → cross-dept intelligence without data leakage
```

**Price:** $24,900 setup + $2,000/month support.
**Value delivered:** Replaces $180,000/year in cloud AI subscriptions.
**ROI in month 1.**

---

## The Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AONXI OS — FULL STACK                         │
└─────────────────────────────────────────────────────────────────┘

LAYER 0: HARDWARE
├── Mac Mini M4 / Mac Studio M4 Max
├── Apple Silicon: unified memory = fastest LLM inference on earth
├── 16–128GB unified RAM → run 14B to 72B parameter models locally
└── 10W–45W power draw → $8–$15/month electricity for full AI OS

LAYER 1: MODEL LAYER (local, no cloud)
├── Qwen2.5-72B Q4 (Mac Studio 64GB) — near GPT-4o quality
├── Qwen2.5-32B Q4 (Mac Mini Pro 24GB) — GPT-4o mini equivalent
├── Qwen2.5-14B Q8 (Mac Mini 16GB) — GPT-3.5 beater
├── LLM server: Ollama (REST API, OpenAI-compatible)
└── All models run 100% offline. Zero API costs. Zero data leaving.

LAYER 2: MEMORY LAYER
├── MemoryMesh (local SQLite + FTS5) — per-user, per-tenant memory
├── Qdrant (local vector DB) — semantic search across all knowledge
├── Mem0 API (optional cloud sync) — cross-device memory persistence
└── Super Brain orchestrator — pattern detection across all tenants

LAYER 2.5: SAAS REPLACEMENT ENGINE
├── SaaS Connector (API adapters for CRM, support, marketing, finance, etc.)
├── Workflow Observer (watches how you ACTUALLY use each tool)
├── Pattern Learner (extracts your specific workflows, not generic templates)
├── Local Builder (generates local equivalents with cross-tool intelligence)
├── Parallel Validator (runs local version alongside SaaS for verification)
└── Migration Manager (cutover control + subscription cancellation tracking)

LAYER 3: AGENT LAYER
├── Omni-Outreach Agent (all channels: LinkedIn, ads, SEO, email, social)
├── Employee AI (per-person customized Claude workspace)
├── Sales Pipeline Agent (lead→qualify→demo→close)
├── Delivery Agent (onboard→deploy→CSAT→iterate)
├── HR Agent (resumes→schedule→onboard→policies)
├── IT Helpdesk Agent (tickets→resolve→escalate→learn)
├── Support Agent (inbound→resolve→escalate→retain)
├── Finance Agent (invoices→categorize→forecast→report)
└── Custom Agent (any workflow → agent in 48 hours)

LAYER 4: GATEWAY LAYER (internet-facing)
├── FastAPI server (port 8080 local) — the web interface
├── WebSocket server — real-time agent output streaming
├── JWT auth — secure login, multi-tenant isolation
├── Role-based access control (RBAC) — per-employee permissions
├── Rate limiting — fair use per tenant
└── Cloudflare Tunnel — HTTPS globally accessible, no port forwarding

LAYER 5: BILLING LAYER
├── Per-query tracking (every LLM call logged with tokens)
├── Per-user usage dashboard
├── Per-tenant monthly report
├── Stripe integration for recurring billing
└── Usage-based pricing tiers

LAYER 6: INTELLIGENCE LAYER
├── Cross-tenant learning (anonymized patterns only)
├── Predictive analytics (which leads convert, which employees churn)
├── CSAT prediction (flag at-risk clients before they churn)
├── Revenue forecasting (MRR → ARR trajectory)
└── Agent improvement scoring (did this agent make others better?)
```

---

## The SaaS Replacement Engine

The core innovation of AONXI OS: your Mac Mini doesn't just run AI agents — it **replaces the SaaS tools you're already paying for** by learning how you use them and building local versions that are better.

### How It Works

**Step 1: Connect via API**
The Mac Mini connects to your existing SaaS tools (CRM, support desk, marketing automation, accounting, SEO analytics, project management, team chat, ad platforms) via their APIs. Read-only at first. No disruption.

**Step 2: Observe and Learn Workflows**
The Workflow Observer watches how your team ACTUALLY uses each tool — not how the manual says to use it. It captures:
- Which features you use (and which you don't — most teams use <20% of any SaaS tool)
- The sequences: what happens after a deal closes? After a support ticket resolves?
- The cross-tool patterns: when a big deal closes in CRM, does someone manually update the finance tool?
- The workarounds: copy-paste between tools, manual data entry, spreadsheet bridges

**Step 3: Build Local Equivalents**
The Local Builder generates streamlined local versions that replicate YOUR workflows. These local versions have a superpower no SaaS tool has: **cross-tool intelligence**. Because all your data lives in one brain:
- Your support agent sees the full sales history before responding to a ticket
- Your outreach agent knows which customer segments are profitable (from finance data)
- Your project management view knows which clients have open support issues
- Your marketing agent knows which leads your sales team has already contacted

**Step 4: Parallel Run and Validation**
The local version runs alongside the SaaS tool. Both receive the same inputs. Outputs are compared. When the local version matches or exceeds the SaaS tool's utility for 2+ weeks, it's validated.

**Step 5: Cutover and Cancel**
Migration is tool-by-tool, not all-at-once:
```
Week 1-2:   Connect CRM API, observe workflows
Week 3-4:   Local CRM runs in parallel, outputs compared
Week 5:     Local CRM validated → cancel CRM subscription ($800/mo saved)
Week 6-7:   Connect support desk API, observe workflows
Week 8-9:   Local support runs in parallel
Week 10:    Local support validated → cancel subscription ($550/mo saved)
...repeat for each tool...
```

### Why Local Versions Are Better

| Dimension | Siloed SaaS Tool | AONXI Local Version |
|---|---|---|
| **Data visibility** | Only sees its own data | Sees ALL your business data |
| **Cross-tool triggers** | Requires Zapier/Make + manual setup | Automatic — it's all one brain |
| **Learns your patterns** | Generic for all customers | Trained on YOUR specific workflows |
| **Privacy** | Your data on their servers | Your data on your hardware |
| **Monthly cost** | $50-$800/tool/month | $0 per query, $15/mo electricity |
| **Customization** | Limited to their UI/API | Unlimited — you own the code |

---

## The Agent Family — Complete Map

```
                         ┌───────────────────┐
                         │    SUPER BRAIN     │
                         │  (orchestrator)    │
                         │  MemoryMesh+Mem0   │
                         └─────────┬─────────┘
                                   │ (all agents read/write here)
          ┌──────────────┬─────────┼─────────┬──────────────┐
          │              │         │         │              │
    ┌─────▼────┐   ┌─────▼───┐ ┌──▼──────┐ ┌▼──────────┐ ┌▼──────────┐
    │  OUTREACH │   │ EMPLOYEE│ │ DELIVERY│ │    HR     │ │    IT     │
    │  AGENT   │   │   AI    │ │  AGENT  │ │  AGENT   │ │  HELPDESK │
    │          │   │         │ │         │ │          │ │  AGENT    │
    │ LinkedIn │   │ Per-role│ │ Onboard │ │ Resumes  │ │ Tickets   │
    │ Meta Ads │   │ Memory  │ │ CSAT 9+ │ │ Policies │ │ Passwords │
    │ Google   │   │ Persona │ │ Retain  │ │ Onboard  │ │ VPN/Access│
    │ Twitter  │   │ Tools   │ │ Upsell  │ │ Benefits │ │ Knowledge │
    │ SEO Sig  │   │ Context │ │         │ │          │ │           │
    │ Job Sig  │   │         │ │         │ │          │ │           │
    └──────────┘   └─────────┘ └─────────┘ └──────────┘ └───────────┘
          │              │         │         │              │
          └──────────────┴─────────┴─────────┴──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │        GATEWAY LAYER         │
                    │   FastAPI + WebSocket + JWT  │
                    │   Cloudflare Tunnel → HTTPS  │
                    └──────────────┬──────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
    ┌─────▼──────┐          ┌──────▼──────┐         ┌──────▼──────┐
    │  Individual │          │   WeWork    │         │  Enterprise │
    │   Users    │          │  Building   │         │ Departments │
    │  (global)  │          │ (500 users) │         │ (5 studios) │
    └────────────┘          └─────────────┘         └─────────────┘
```

---

## The Omni-Outreach Agent — All Channels

The outreach agent doesn't just scrape Google Maps. It covers every signal a prospect could leave anywhere on the internet.

### Signal Sources

| Signal | Source | What it detects | Priority |
|--------|---------|----------------|----------|
| **LinkedIn** | LinkedIn API / Sales Nav | Job changes, company growth, posts about pain points | Critical |
| **Meta Ads** | Meta Ad Library | What competitors are advertising, who's spending | High |
| **Google Ads** | Google Keyword Planner | Who's buying keywords in your category | High |
| **SEO Signals** | Ahrefs/SEMrush API | Companies ranking for buying-intent keywords | High |
| **Job Postings** | Indeed/LinkedIn Jobs | Hiring signals = growth = budget = buying intent | Critical |
| **Funding News** | Crunchbase, Techcrunch | Newly funded = cash to spend | Critical |
| **News Mentions** | Google News API | Companies mentioned in trade press | Medium |
| **Social Intent** | Twitter/X, Reddit | People complaining about competitors, asking for solutions | High |
| **Product Hunt** | PH API | New products launching = founders with budget | Medium |
| **G2/Capterra** | Review scraping | People leaving competitors = ready to switch | Critical |
| **Domain Signals** | BuiltWith | Tech stack = buying signals (using Salesforce = enterprise budget) | High |
| **Email Warm** | Google Maps, Yelp | Local businesses = easier to reach | Medium |
| **Apollo/Clay** | Apollo API | Verified email + phone + LinkedIn | Critical |
| **Bombora** | Bombora API | Intent data — companies actively researching your category | High |
| **6sense** | 6sense API | Predictive buying stage — who's in-market right now | High |

### The Outreach Sequence

```
DISCOVERY
  ├── Run all signal sources in parallel
  ├── Deduplicate against CRM (never contact same company twice)
  ├── Score each lead (0.0–1.0) using dual-LLM scoring
  └── Filter: score >= 0.6 only

RESEARCH
  ├── LinkedIn profile deep dive (role, tenure, posts, connections)
  ├── Company page: headcount growth, recent posts, job openings
  ├── News: what happened at their company in last 30 days
  └── PKM: detect defense mode, select bypass strategy

PERSONALIZATION
  ├── Write email using PKM defense mode bypass
  ├── Subject line A/B test (2 variants)
  ├── Call to action: specific, low-friction (15-min call, not "let's connect")
  └── Human review gate (Y/N/edit) before any email sends

DELIVERY
  ├── Send via Gmail SMTP / SendGrid / Instantly
  ├── Optimal send time (Tue–Thu, 8–10am local time)
  ├── Track opens/clicks via Instantly
  └── IMAP monitoring for replies

FOLLOW-UP
  ├── Day 3: follow-up with different angle + fresh signal
  ├── Day 7: break-up email ("should I close this file?")
  ├── Reply detected → route to human immediately
  └── Positive reply → book via Cal.com link

LEARNING
  ├── Every outcome (opened/replied/booked/ghosted) → brain
  ├── Pattern: which signal source converts best per vertical?
  ├── Pattern: which PKM bypass works for which role?
  └── Agent rewrites its own scoring weights based on real data
```

---

## Per-Employee AI — The Customization Model

Every employee gets a Claude instance that knows:
- Their **role** (CEO, Sales Rep, Support Agent, Dev)
- Their **tools** (which apps they use, which APIs they have access to)
- Their **style** (formal vs casual, brief vs detailed)
- Their **current projects** (pulled from Notion/Linear/Jira)
- Their **calendar** (what meetings are coming, what needs prep)
- Their **past wins** (what worked for them, their playbook)

```
Employee Profile = {
    role: "Senior Sales Rep",
    tone: "confident, data-driven, brief",
    tools: [CRM, Cal.com, Gmail, LinkedIn, Slack],
    current_deals: [from CRM],
    calendar_today: [from Google Calendar],
    playbook: [from MemoryMesh — their personal wins],
    defense_mode_bypasses: [from PKM — what works for their prospects],
    escalate_to: "VP Sales for deals > $50K"
}
```

Each login loads their profile. The AI opens with context, not a blank slate.

**Example interactions by role:**

```
CEO logs in:
  AI: "Good morning. 3 items need your attention:
       1. Acme Corp replied — they want a proposal by Friday
       2. CSAT dropped to 8.2 at BuilderPro — risk of churn
       3. Your 2pm investor call: here's a 3-slide brief on ask + traction"

Sales Rep logs in:
  AI: "Your pipeline: 12 leads, 3 hot (score >0.8). Outreach ran at 7am:
       sent 23 emails, 2 replies. Sarah at TechCorp asked for a demo.
       Want me to book it and prep a company brief?"

HR Manager logs in:
  AI: "4 new applicants for Senior Dev role. 2 meet all requirements.
       I've pre-screened and ranked them. Want me to schedule first rounds?"

IT Support logs in:
  AI: "14 open tickets. 9 are Tier 1 (I can resolve these).
       5 need you: 2 are VPN setup, 3 are access escalations."
```

---

## The WeWork Deployment Flow

```
1. SALE
   Sales agent finds building management company (CBRE, JLL, Industrious, WeWork)
   Outreach: "Your 500 members pay $50/month for AI tools they barely use.
              We'll give you an AI OS for your building for $500/month.
              They'll use it 3x/day. It becomes a reason to stay."

2. HARDWARE DEPLOYMENT
   Ship Mac Studio M4 Max 64GB to building IT room
   On-site setup: 2 hours
   Cloudflare Tunnel: 30 minutes
   System running: same day

3. MEMBER ONBOARDING
   QR code on every desk → mobile-friendly web portal
   Members create account (SSO with building management system)
   First login: AI asks 5 questions → profile built
   Day 1: fully personalized AI workspace

4. BUILDING MANAGEMENT DASHBOARD
   Total users, daily active, queries per day
   Per-member usage (anonymized)
   Monthly report → show the ROI
   CSAT of the AI itself (how useful is it?)

5. BILLING
   Building pays: $500/month flat
   AONXI cost: $15/month electricity
   Margin: 97%
   Optional: per-member upsell ($29/month for premium tier)
```

---

## The Data Flywheel — Predictions and Forecasting

With owned data across tenants (anonymized), AONXI builds:

### Prediction Models

| Model | Input | Output | Business Value |
|-------|-------|--------|---------------|
| **Lead Conversion Predictor** | Company size, funding stage, tech stack, signal source | P(close in 30 days) | Route sales effort to highest-value leads |
| **Churn Predictor** | CSAT trend, usage frequency, support ticket rate | P(churn in 60 days) | Flag at-risk clients for intervention |
| **MRR Forecaster** | Pipeline, conversion rate, churn rate, seasonality | MRR in 3/6/12 months | Board-ready revenue projections |
| **Employee Productivity** | Queries/day, task types, time-to-response | Which employees get the most from AI | Identify training needs |
| **Agent Improvement Score** | Cross-repo patterns, shared kernel usage, CSAT delta | Which agent improvements raised fleet CSAT | Prioritize engineering work |

All models run locally on your Mac. No data leaves. The predictions improve as more clients use the system.

---

## The Internet Access Architecture

```
Mac Mini / Mac Studio (your location)
    │
    ├── Ollama (port 11434) — LLM server
    ├── FastAPI gateway (port 8080) — web interface + API
    ├── MemoryMesh (SQLite) — local memory
    └── Qdrant (port 6333) — vector search
         │
         ▼
    Cloudflare Tunnel (cloudflared daemon)
         │
         ▼
    your-company.aonxi.com (HTTPS, globally accessible)
         │
    ┌────┴────────────────────────────────────┐
    │          USERS ANYWHERE IN WORLD         │
    │  Phone · Laptop · Tablet · Any Browser  │
    │  No app download. No VPN. Just login.   │
    └─────────────────────────────────────────┘
```

**Security:**
- JWT tokens (expire in 8h, refresh required)
- RBAC: Admin / Manager / Employee / Guest
- Tenant isolation: each company's data is separate
- All traffic: Cloudflare TLS (end-to-end encrypted)
- Local data: AES-256 at rest (macOS FileVault)
- No data to Cloudflare: tunnel is encrypted, CF cannot read content

---

## The File Structure

```
super-brain/
├── AONXI_OS.md                     # This document
├── index.html                      # Sales page
│
├── src/
│   ├── brain.py                    # V2: Memory + orchestration SDK
│   ├── orchestrator.py             # Ecosystem scan + improvement engine
│   ├── company.py                  # Company OS: sales + delivery + CSAT
│   ├── evals.py                    # Agent evaluation framework — compound intelligence scoring
│   ├── local_brain.py              # MemoryMesh local memory layer
│   │
│   ├── gateway.py                  # FastAPI web server (internet-facing)
│   ├── employee.py                 # Per-employee AI profiles + customization
│   ├── billing.py                  # Usage tracking + Stripe billing
│   ├── omni_outreach.py            # All-channel outreach agent
│   │
│   ├── agents/
│   │   ├── hr_agent.py             # HR: resumes, scheduling, policies, onboarding
│   │   ├── it_helpdesk.py          # IT: tickets, access, VPN, troubleshooting
│   │   ├── support_agent.py        # Customer support: inbound, escalation, retention
│   │   ├── finance_agent.py        # Finance: invoices, categorization, forecasting
│   │   └── custom_agent.py         # Template for building new domain agents
│   │
│   ├── saas_engine/
│   │   ├── connector.py            # API adapters for CRM, support, marketing, finance, etc.
│   │   ├── observer.py             # Workflow observation — watches how you use each tool
│   │   ├── pattern_learner.py      # Extracts your specific workflow patterns
│   │   ├── local_builder.py        # Generates local equivalents with cross-tool intelligence
│   │   ├── validator.py            # Parallel run comparison — local vs SaaS
│   │   └── migration.py            # Cutover control + subscription cancellation tracking
│   │
│   ├── intelligence/
│   │   ├── predictor.py            # Lead conversion, churn, MRR forecasting
│   │   ├── pkm.py                  # Persuasion Knowledge Model — all 10 defense modes
│   │   └── signal_scorer.py        # Scores any lead signal 0.0–1.0
│   │
│   ├── mem0_push.sh                # Push memories to Mem0 cloud
│   ├── mem0_search.sh              # Search the brain
│   └── mem0_hook.sh                # Claude Code PostToolUse auto-learning hook
│
├── config/
│   ├── repos.yaml                  # Complete registry of all 50+ repos
│   ├── categories.json             # Memory category taxonomy
│   ├── claude_hooks.json           # Claude Code hook config
│   └── agents.yaml                 # Agent fleet config: models, timeouts, tools
│
├── infra/
│   ├── tunnel.sh                   # Cloudflare Tunnel setup (one command)
│   ├── install.sh                  # Full AONXI OS install: Ollama + models + all deps
│   ├── nginx.conf                  # Reverse proxy config (if not using CF tunnel)
│   └── systemd/                    # Service files for auto-start on boot
│       ├── aonxi-gateway.service
│       ├── aonxi-ollama.service
│       └── aonxi-orchestrator.service
│
├── data/
│   ├── company.db                  # SQLite: clients, pipeline, CSAT, revenue
│   ├── evals.db                    # SQLite: weekly eval snapshots + compound scores
│   ├── tenants.db                  # SQLite: multi-tenant data
│   └── usage.db                    # SQLite: per-user query log for billing
│
└── reports/                        # Auto-generated: improvement reports + dashboards
```

---

## The Evaluation Framework (`evals.py`)

Every agent type is measured on its own axis. The eval system runs weekly, scores each agent, and produces a **compound intelligence score** that tracks whether the fleet is getting smarter over time.

### How Each Agent Type Is Measured

| Agent Type | Eval Dimensions | Key Metric | Pass Threshold |
|------------|----------------|------------|----------------|
| **Outreach** | Reply rate, meeting book rate, lead quality score, personalization accuracy | Meetings booked per 100 emails | >= 3.0 |
| **Delivery** | CSAT score, time-to-value, resolution rate, escalation rate | CSAT average | >= 9.0 |
| **HR** | Resume screen accuracy, time-to-hire, candidate NPS | Screen precision | >= 85% |
| **IT Helpdesk** | Auto-resolve rate, first-response time, ticket reopen rate | Auto-resolve % | >= 60% |
| **Support** | Resolution time, customer effort score, escalation rate | Effort score | <= 2.0 |
| **Finance** | Categorization accuracy, forecast error, anomaly detection | Forecast error | <= 5% |
| **Research** | Insight-to-shipped ratio, citation accuracy, novelty score | Insights shipped | >= 3/week |
| **Sales Pipeline** | Stage conversion rates, forecast accuracy, deal velocity | Weighted pipeline accuracy | >= 80% |

### The Compound Intelligence Score

The compound score is a single number (0.0-100.0) that captures how well the entire fleet is performing and whether agents are making each other better:

```
Compound Intelligence Score =
    0.30 * avg(agent_scores)           # Individual agent performance
  + 0.25 * cross_improvement_rate      # How much agents improved each other
  + 0.20 * pattern_detection_rate      # New patterns discovered this week
  + 0.15 * research_to_product_rate    # Research insights that shipped
  + 0.10 * memory_growth_rate          # Brain knowledge compounding
```

A score above **70** means the fleet is healthy and improving. Below **60** triggers an alert.

### Week-over-Week Tracking

Every Sunday at midnight, `evals.py` snapshots the full eval state into `data/evals.db`. The weekly report shows:

- Each agent's score vs. last week (delta + trend arrow)
- Compound intelligence score trend (4-week rolling)
- Top 3 improvements (which agent got better and why)
- Top 3 regressions (which agent got worse and what to fix)
- Cross-improvement events (agent A's output improved agent B)

### CLI Commands

```bash
# Run the full eval suite across all agent types
python3 src/evals.py run-all

# Eval a specific agent type
python3 src/evals.py run --agent outreach
python3 src/evals.py run --agent delivery

# View the current compound intelligence score
python3 src/evals.py score

# Weekly report with deltas and trends
python3 src/evals.py weekly-report

# Compare any two weeks side by side
python3 src/evals.py compare --week 2026-W12 --week 2026-W13

# Export eval history as CSV (for dashboards)
python3 src/evals.py export --format csv --output reports/eval_history.csv
```

---

## The KPIs — What the System Optimizes

```
SALES KPIs (weekly)
  ├── New leads discovered (target: 100+/week)
  ├── Emails sent (target: 50+/week)
  ├── Reply rate (target: 5%+)
  ├── Meetings booked (target: 10+/week)
  └── Pipeline value added (target: $50K+/week)

DELIVERY KPIs (per client)
  ├── CSAT score (hard minimum: 9.0/10)
  ├── Time to value (< 48h from signup to first AI win)
  ├── Daily active users (target: 80%+ of seats)
  ├── Queries per user per day (target: 15+)
  └── Churn flag (trigger: CSAT < 8.5 for 2 weeks)

COMPANY KPIs (monthly)
  ├── MRR (target: grow 15%/month)
  ├── Gross margin (target: 90%+)
  ├── NPS (target: 70+)
  ├── Cost per client (target: < $50/month all-in)
  └── Revenue per employee (maximize — agents ARE the employees)

INTELLIGENCE KPIs
  ├── Agent improvement score (did this week's changes raise CSAT?)
  ├── Cross-repo pattern count (how many new patterns detected?)
  ├── Research-to-product links (how many research insights shipped?)
  └── Memory compound rate (is the brain getting smarter each week?)
```

---

## APIs You Need to Register

**Critical (get these first):**
| API | Purpose | Cost |
|-----|---------|------|
| Cloudflare | Free tunnel to internet | Free |
| Apollo.io | Email + LinkedIn enrichment | $49/mo or pay-as-go |
| Instantly.ai | Email delivery + tracking | $37/mo |
| Cal.com | Meeting booking | Free / $12/mo |
| Stripe | Billing | 2.9% + $0.30/transaction |

**High value (get next):**
| API | Purpose | Cost |
|-----|---------|------|
| LinkedIn Sales Nav | B2B prospecting | $99/mo |
| Hunter.io | Email finding | $49/mo |
| Exa.ai | Web search for AI | $20/mo |
| Google News API | News monitoring | Free tier |
| Crunchbase API | Funding signals | $49/mo |

**Enterprise (add when scaling):**
| API | Purpose | Cost |
|-----|---------|------|
| Bombora | Intent data | Enterprise |
| 6sense | Predictive buying stage | Enterprise |
| ZoomInfo | Full B2B database | Enterprise |
| Meta Ad Library | Competitor ad monitoring | Free |
| Anthropic Claude API | Fallback for complex tasks | Pay-as-go |

**Total monthly API cost at full scale:** ~$350/month
**Revenue at 10 clients at $500/month:** $5,000/month
**Gross margin:** 93%

---

## The Install — One Script

```bash
# On a fresh Mac Mini M4 or Mac Studio M4 Max:
curl -sSL https://raw.githubusercontent.com/originaonxi/super-brain/main/infra/install.sh | bash

# What it does (in 10 minutes):
# 1. Installs Homebrew, Python 3.12, Node.js
# 2. Installs Ollama + pulls Qwen2.5-72B (or smaller based on RAM)
# 3. Installs all Python deps
# 4. Sets up SQLite databases
# 5. Configures Cloudflare Tunnel with your domain
# 6. Starts all services (Ollama, Gateway, Orchestrator)
# 7. Creates first admin account
# 8. Opens browser to your new AI OS

# Result: fully running AONXI OS, accessible from anywhere in the world
```

---

## The Pitch — Selling to WeWork

```
Subject: Your 500 members pay $11,200/month for AI tools they barely use.
         We'll cut that to $500/month and make the AI 10x more useful.

The problem:
  Your members use ChatGPT, Copilot, Claude — each paying individually.
  Total spend per building: $11,200/month.
  Data going to Microsoft, OpenAI servers.
  No memory. No personalization. Every session starts from zero.

Our solution:
  One Mac Studio M4 Max in your IT room.
  Every member gets a personalized AI that knows their job.
  Data stays in the building. GDPR/HIPAA compliant by default.
  $500/month flat. No per-seat pricing.

What your members get:
  → Sales people: AI that books meetings while they sleep
  → HR teams: AI that screens resumes and schedules interviews
  → IT staff: AI that resolves 60% of tickets automatically
  → Everyone else: AI that knows their role, their tools, their history

What you get:
  → New amenity that drives member retention
  → $0 liability (data never leaves your building)
  → Dashboard showing AI usage = proof of value
  → Revenue share opportunity: upsell premium tiers to members

ROI calculation:
  Your cost: $12,900 setup + $500/month
  Member value: each member saves 2hrs/day × $50/hr = $100/day = $2,600/month
  Building ROI: 500 members × $2,600/month = $1.3M/month saved
  Your investment: $500/month
  Your ROI: 2,600x
```

---

*Built by Anmol Sam — CTO, Aonxi*
*github.com/originaonxi/super-brain*
*origin@aonxi.com*
