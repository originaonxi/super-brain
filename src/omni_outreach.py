#!/usr/bin/env python3
"""
AONXI Omni-Outreach Agent
===========================
All-channel signal collection → research → personalization → delivery → learning.

Signal sources:
  LinkedIn profiles/jobs/ads, Meta Ads Library, Google Ads Transparency,
  SEO/domain signals (Ahrefs/Semrush proxies), job board signals,
  funding announcements (Crunchbase/PitchBook), news mentions,
  Twitter/X intent, Product Hunt launches, G2/Capterra reviews,
  BuiltWith tech stack, Google Maps local, Apollo enrichment,
  Bombora/6sense intent (enterprise), Hunter email discovery.

Full sequence: Discovery → Research → PKM Defense Analysis →
               Personalization → Multi-Channel Delivery → Follow-Up → Learning

Usage:
  python3 src/omni_outreach.py scan --industry healthcare --limit 20
  python3 src/omni_outreach.py research lead@company.com
  python3 src/omni_outreach.py sequence --lead-id abc123
  python3 src/omni_outreach.py report
"""

import os
import json
import time
import sqlite3
import hashlib
import secrets
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field

# ── Optional imports ───────────────────────────────────────────────────────────
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from anthropic import Anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "outreach.db"

# API keys — set in ~/super-brain/.env
ANTHROPIC_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
APOLLO_KEY      = os.getenv("APOLLO_API_KEY", "")
HUNTER_KEY      = os.getenv("HUNTER_API_KEY", "")
INSTANTLY_KEY   = os.getenv("INSTANTLY_API_KEY", "")
EXA_KEY         = os.getenv("EXA_API_KEY", "")
CRUNCHBASE_KEY  = os.getenv("CRUNCHBASE_API_KEY", "")
LINKEDIN_TOKEN  = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
TWITTER_BEARER  = os.getenv("TWITTER_BEARER_TOKEN", "")
CALCOM_KEY      = os.getenv("CALCOM_API_KEY", "")

# PKM = Persuasion Knowledge Model (how buyers defend against pitches)
PKM_DEFENSE_MODES = [
    "skepticism",       # "All vendors say this"
    "delay",            # "We'll revisit Q3"
    "authority_block",  # "Need to check with my boss"
    "price_anchor",     # "Too expensive"
    "status_quo",       # "We're happy with what we have"
    "feature_gap",      # "You don't have X"
    "trust_deficit",    # "I don't know your company"
    "timing",           # "Bad time, end of quarter"
    "competitor_lock",  # "We signed with Salesforce last month"
    "internal_politics",# "Politics — not the right person"
]


# ── Database ───────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            title TEXT,
            company TEXT,
            industry TEXT,
            linkedin_url TEXT,
            twitter_handle TEXT,
            domain TEXT,
            location TEXT,
            employees TEXT,
            funding_stage TEXT,
            funding_amount TEXT,
            tech_stack TEXT,
            intent_score REAL DEFAULT 0.0,
            pkm_defense TEXT,
            personalization TEXT,
            signal_sources TEXT,
            status TEXT DEFAULT 'discovered',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_contacted TEXT,
            next_action TEXT,
            notes TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sequences (
            id TEXT PRIMARY KEY,
            lead_id TEXT NOT NULL,
            step INTEGER NOT NULL,
            channel TEXT NOT NULL,
            subject TEXT,
            body TEXT,
            sent_at TEXT,
            opened_at TEXT,
            replied_at TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id TEXT,
            source TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            content TEXT,
            score REAL DEFAULT 0.5,
            ts TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id TEXT,
            channel TEXT,
            outcome TEXT,
            what_worked TEXT,
            what_failed TEXT,
            pkm_mode_detected TEXT,
            ts TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ── Signal collectors ──────────────────────────────────────────────────────────
@dataclass
class Signal:
    source: str
    signal_type: str
    content: str
    score: float = 0.5
    lead_id: Optional[str] = None


class SignalCollector:
    """Base class for all signal sources."""

    def __init__(self, name: str):
        self.name = name

    def _get(self, url: str, headers: dict = None, params: dict = None) -> Optional[dict]:
        if not REQUESTS_AVAILABLE:
            return None
        try:
            r = requests.get(url, headers=headers or {}, params=params or {}, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def collect(self, query: str) -> List[Signal]:
        raise NotImplementedError


class ApolloCollector(SignalCollector):
    """Apollo.io — contact + company enrichment, email discovery."""

    def __init__(self):
        super().__init__("apollo")

    def search_people(self, title: str = None, industry: str = None,
                      company_size: str = None, limit: int = 10) -> List[dict]:
        if not APOLLO_KEY:
            return self._mock_leads(limit)

        payload = {
            "api_key": APOLLO_KEY,
            "page": 1,
            "per_page": limit,
        }
        if title:
            payload["person_titles"] = [title]
        if industry:
            payload["organization_industry_tag_ids"] = [industry]
        if company_size:
            payload["organization_num_employees_ranges"] = [company_size]

        try:
            r = requests.post(
                "https://api.apollo.io/v1/mixed_people/search",
                json=payload, timeout=15
            )
            if r.status_code == 200:
                return r.json().get("people", [])
        except Exception:
            pass
        return self._mock_leads(limit)

    def enrich_person(self, email: str) -> Optional[dict]:
        if not APOLLO_KEY:
            return None
        payload = {"api_key": APOLLO_KEY, "email": email}
        try:
            r = requests.post("https://api.apollo.io/v1/people/match", json=payload, timeout=10)
            if r.status_code == 200:
                return r.json().get("person")
        except Exception:
            pass
        return None

    def _mock_leads(self, n: int) -> List[dict]:
        """Returns mock leads when API key not set (for testing)."""
        mock = []
        roles = ["VP Sales", "CTO", "CEO", "Head of Marketing", "Director of Operations"]
        industries = ["SaaS", "Healthcare", "FinTech", "EdTech", "PropTech"]
        for i in range(n):
            mock.append({
                "first_name": f"Lead{i}",
                "last_name": "Test",
                "email": f"lead{i}@company{i}.com",
                "title": roles[i % len(roles)],
                "organization": {"name": f"Company{i} Inc", "industry": industries[i % len(industries)]},
                "linkedin_url": f"https://linkedin.com/in/lead{i}",
                "city": "San Francisco",
                "_mock": True,
            })
        return mock

    def collect(self, query: str) -> List[Signal]:
        return []


class HunterCollector(SignalCollector):
    """Hunter.io — email discovery from domains."""

    def __init__(self):
        super().__init__("hunter")

    def domain_search(self, domain: str, limit: int = 5) -> List[dict]:
        if not HUNTER_KEY:
            return []
        data = self._get(
            "https://api.hunter.io/v2/domain-search",
            params={"domain": domain, "api_key": HUNTER_KEY, "limit": limit}
        )
        return data.get("data", {}).get("emails", []) if data else []

    def email_finder(self, domain: str, first_name: str, last_name: str) -> Optional[str]:
        if not HUNTER_KEY:
            return None
        data = self._get(
            "https://api.hunter.io/v2/email-finder",
            params={"domain": domain, "first_name": first_name,
                    "last_name": last_name, "api_key": HUNTER_KEY}
        )
        return data.get("data", {}).get("email") if data else None

    def collect(self, query: str) -> List[Signal]:
        return []


class CrunchbaseCollector(SignalCollector):
    """Crunchbase — recently funded companies (buying signal: have budget)."""

    def __init__(self):
        super().__init__("crunchbase")

    def recent_funding(self, days_back: int = 30, min_amount_m: float = 0.5) -> List[dict]:
        if not CRUNCHBASE_KEY:
            return self._mock_funding(10)

        cutoff = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        payload = {
            "field_ids": ["identifier", "short_description", "funding_rounds",
                          "categories", "location_identifiers", "homepage_url"],
            "query": [
                {"type": "predicate", "field_id": "last_funding_at",
                 "operator_id": "gte", "values": [cutoff]},
                {"type": "predicate", "field_id": "last_funding_total",
                 "operator_id": "gte", "values": [str(int(min_amount_m * 1_000_000))]}
            ],
            "order": [{"field_id": "last_funding_at", "sort": "desc"}],
            "limit": 25
        }
        try:
            r = requests.post(
                "https://api.crunchbase.com/api/v4/searches/organizations",
                json=payload,
                params={"user_key": CRUNCHBASE_KEY},
                timeout=15
            )
            if r.status_code == 200:
                return r.json().get("entities", [])
        except Exception:
            pass
        return self._mock_funding(10)

    def _mock_funding(self, n: int) -> List[dict]:
        companies = []
        for i in range(n):
            companies.append({
                "properties": {
                    "identifier": {"value": f"startup-{i}"},
                    "short_description": f"AI startup {i} — recently raised Series A",
                    "homepage_url": f"https://startup{i}.com",
                    "last_funding_type": "series_a" if i % 2 == 0 else "seed",
                    "last_funding_total": {"value": 2_000_000 + i * 500_000},
                },
                "_mock": True,
            })
        return companies

    def collect(self, query: str) -> List[Signal]:
        funded = self.recent_funding()
        signals = []
        for company in funded:
            props = company.get("properties", {})
            signals.append(Signal(
                source="crunchbase",
                signal_type="funding",
                content=json.dumps({
                    "company": props.get("identifier", {}).get("value", ""),
                    "description": props.get("short_description", ""),
                    "url": props.get("homepage_url", ""),
                    "funding_type": props.get("last_funding_type", ""),
                }),
                score=0.85,  # Funding = high buying intent
            ))
        return signals


class ExaNewsCollector(SignalCollector):
    """Exa.ai — semantic news search for buying intent signals."""

    def __init__(self):
        super().__init__("exa_news")

    def search(self, query: str, num_results: int = 10) -> List[dict]:
        if not EXA_KEY:
            return []
        try:
            r = requests.post(
                "https://api.exa.ai/search",
                json={"query": query, "numResults": num_results,
                      "type": "neural", "useAutoprompt": True},
                headers={"x-api-key": EXA_KEY},
                timeout=15
            )
            if r.status_code == 200:
                return r.json().get("results", [])
        except Exception:
            pass
        return []

    def collect(self, query: str) -> List[Signal]:
        results = self.search(f"{query} company hiring expanding growth")
        signals = []
        for r in results:
            signals.append(Signal(
                source="exa_news",
                signal_type="news_mention",
                content=json.dumps({"title": r.get("title", ""), "url": r.get("url", ""),
                                    "snippet": r.get("text", "")[:200]}),
                score=0.6,
            ))
        return signals


class JobSignalCollector(SignalCollector):
    """Job board signals — hiring = budget + growth intent."""

    def __init__(self):
        super().__init__("job_signals")

    def search_jobs(self, company: str) -> List[Signal]:
        # Uses LinkedIn Jobs public feed or Indeed RSS
        signals = []
        ai_job_titles = ["AI Engineer", "Machine Learning", "Data Scientist",
                         "Head of AI", "VP Engineering", "Chief AI Officer"]

        if EXA_KEY:
            collector = ExaNewsCollector()
            for title in ai_job_titles[:3]:
                results = collector.search(f"{company} hiring {title}", num_results=3)
                for r in results:
                    signals.append(Signal(
                        source="job_signals",
                        signal_type="hiring_signal",
                        content=json.dumps({"job": title, "company": company,
                                            "url": r.get("url", "")}),
                        score=0.75,  # Hiring AI = very high intent for AI tools
                    ))
        return signals

    def collect(self, query: str) -> List[Signal]:
        return self.search_jobs(query)


class TwitterIntentCollector(SignalCollector):
    """Twitter/X — intent signals from public posts."""

    def __init__(self):
        super().__init__("twitter")

    def search_intent(self, keywords: List[str], max_results: int = 20) -> List[Signal]:
        if not TWITTER_BEARER:
            return []
        query = " OR ".join(f'"{k}"' for k in keywords) + " -is:retweet lang:en"
        try:
            r = requests.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers={"Authorization": f"Bearer {TWITTER_BEARER}"},
                params={"query": query, "max_results": min(max_results, 100),
                        "tweet.fields": "author_id,created_at,text"},
                timeout=15
            )
            if r.status_code == 200:
                tweets = r.json().get("data", [])
                signals = []
                for tweet in tweets:
                    signals.append(Signal(
                        source="twitter",
                        signal_type="social_intent",
                        content=json.dumps({"text": tweet["text"][:280],
                                            "tweet_id": tweet["id"]}),
                        score=0.55,
                    ))
                return signals
        except Exception:
            pass
        return []

    def collect(self, query: str) -> List[Signal]:
        intent_phrases = [
            f"{query} automation", f"{query} AI agent",
            "looking for AI solution", "need sales automation",
        ]
        return self.search_intent(intent_phrases[:2])


class LinkedInSignalCollector(SignalCollector):
    """LinkedIn — job change, company growth, shared content signals."""

    def __init__(self):
        super().__init__("linkedin")

    def collect(self, query: str) -> List[Signal]:
        # LinkedIn API requires OAuth2 + Sales Navigator for lead gen
        # Without Sales Navigator, we infer signals from public data via Exa
        signals = []
        if EXA_KEY:
            news = ExaNewsCollector()
            results = news.search(f"site:linkedin.com {query} AI automation", num_results=5)
            for r in results:
                signals.append(Signal(
                    source="linkedin",
                    signal_type="linkedin_activity",
                    content=json.dumps({"url": r.get("url", ""),
                                        "title": r.get("title", "")}),
                    score=0.65,
                ))
        return signals


class G2ReviewCollector(SignalCollector):
    """G2/Capterra — competitors they review = active buyers."""

    def __init__(self):
        super().__init__("g2")

    def collect(self, query: str) -> List[Signal]:
        if not EXA_KEY:
            return []
        news = ExaNewsCollector()
        results = news.search(
            f"site:g2.com OR site:capterra.com {query} review",
            num_results=5
        )
        signals = []
        for r in results:
            signals.append(Signal(
                source="g2",
                signal_type="competitor_review",
                content=json.dumps({"url": r.get("url", ""),
                                    "title": r.get("title", "")}),
                score=0.80,  # Reviewing competitors = active evaluation mode
            ))
        return signals


# ── Outreach sequence engine ───────────────────────────────────────────────────
@dataclass
class Lead:
    id: str
    first_name: str
    last_name: str
    email: str
    title: str
    company: str
    industry: str = ""
    linkedin_url: str = ""
    tech_stack: str = ""
    funding_stage: str = ""
    intent_score: float = 0.5
    pkm_defense: str = ""
    personalization: str = ""
    signal_sources: str = ""
    status: str = "discovered"


class PKMAnalyzer:
    """
    Analyzes the likely defense mode a prospect will use and generates
    pre-emptive bypass strategies. Based on Persuasion Knowledge Model theory.
    """

    BYPASS_STRATEGIES = {
        "skepticism": "Lead with a verifiable proof point specific to their industry. Quote a customer in their exact vertical.",
        "delay": "Create urgency with a time-limited pilot offer. Show what delay costs in $ terms.",
        "authority_block": "Provide a one-page exec summary they can forward. Make it easy to champion internally.",
        "price_anchor": "Anchor on ROI first — show the $X they lose per week without it before revealing price.",
        "status_quo": "Quantify the cost of the status quo. Show what a competitor in their space gained by switching.",
        "feature_gap": "Acknowledge it. Show the roadmap date it ships. Offer to build it for this deal.",
        "trust_deficit": "Lead with social proof from a mutual connection or well-known customer in their space.",
        "timing": "Agree — then plant a seed for when timing is right. Schedule a 15-min re-connect for the exact date.",
        "competitor_lock": "Ask about contract end date. Nurture until 60 days before renewal.",
        "internal_politics": "Map the org chart. Find a champion below who has pain. Let them pull you up.",
    }

    def analyze(self, lead: "Lead", signals: List[Signal]) -> str:
        """Returns the most likely PKM defense mode for this lead."""
        if not CLAUDE_AVAILABLE or not ANTHROPIC_KEY:
            return "skepticism"  # Default

        signal_summary = "\n".join([
            f"- [{s.source}] {s.signal_type}: {s.content[:100]}"
            for s in signals[:5]
        ])

        client = Anthropic(api_key=ANTHROPIC_KEY)
        prompt = f"""
Lead profile:
- Name: {lead.first_name} {lead.last_name}
- Title: {lead.title} at {lead.company}
- Industry: {lead.industry}
- Funding: {lead.funding_stage or 'unknown'}
- Signals detected: {signal_summary or 'none'}

Based on this profile, which ONE defense mode will they most likely use when I pitch AI sales automation?
Choose from: {', '.join(PKM_DEFENSE_MODES)}

Reply with ONLY the defense mode name, nothing else.
"""
        try:
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=20,
                messages=[{"role": "user", "content": prompt}]
            )
            mode = response.content[0].text.strip().lower()
            if mode in PKM_DEFENSE_MODES:
                return mode
        except Exception:
            pass
        return "skepticism"

    def bypass_strategy(self, mode: str) -> str:
        return self.BYPASS_STRATEGIES.get(mode, self.BYPASS_STRATEGIES["skepticism"])


class OutreachPersonalizer:
    """Generates hyper-personalized multi-channel outreach using Claude."""

    CHANNELS = ["email_1", "linkedin_connect", "email_2", "linkedin_message",
                "email_3", "twitter_dm", "email_4", "phone_voicemail"]

    def __init__(self):
        self.pkm = PKMAnalyzer()

    def generate_sequence(self, lead: Lead, signals: List[Signal],
                          pkm_mode: str) -> List[Dict]:
        """Generates a full 8-step outreach sequence across channels."""
        if not CLAUDE_AVAILABLE or not ANTHROPIC_KEY:
            return self._mock_sequence(lead)

        bypass = self.pkm.bypass_strategy(pkm_mode)
        signal_context = " | ".join([s.content[:80] for s in signals[:3]])

        client = Anthropic(api_key=ANTHROPIC_KEY)
        prompt = f"""
You are an elite B2B sales copywriter for AONXI — an AI automation company.
Write a complete 8-step outreach sequence for this lead.

Lead: {lead.first_name} {lead.last_name}, {lead.title} at {lead.company} ({lead.industry})
Signals detected: {signal_context or "none"}
Likely defense mode: {pkm_mode}
PKM bypass strategy: {bypass}

AONXI's value prop: Autonomous AI agents that run sales, delivery, and operations on automation.
$0 marginal cost, runs on Mac Mini. Outcomes: meetings booked, CSAT 9.0+, MRR growth.

Write 8 outreach steps. Each step must specify:
1. channel (email / linkedin_connect / linkedin_message / twitter_dm / phone_voicemail)
2. subject (if email)
3. body (max 120 words, punchy, specific, no fluff)
4. timing (e.g., "Day 1", "Day 3", "Day 7")
5. goal (what action you want them to take)

Format as JSON array. Use the PKM bypass strategy naturally — don't reference it explicitly.
"""
        try:
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip()
            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception:
            return self._mock_sequence(lead)

    def _mock_sequence(self, lead: Lead) -> List[Dict]:
        return [
            {
                "channel": "email",
                "subject": f"AONXI → {lead.company}: AI agents that close deals",
                "body": f"Hi {lead.first_name},\n\nI noticed {lead.company} is scaling in {lead.industry}. We built AI agents that book meetings autonomously — 0 headcount, CSAT 9.0+.\n\nWorth a 15-min call?\n\nAnmol",
                "timing": "Day 1",
                "goal": "Reply or book call"
            },
            {
                "channel": "linkedin_connect",
                "subject": None,
                "body": f"Hi {lead.first_name} — building AI agents for {lead.industry} companies. Would love to connect.",
                "timing": "Day 2",
                "goal": "Connection accepted"
            },
            {
                "channel": "email",
                "subject": f"Re: {lead.company} + AONXI",
                "body": f"Hey {lead.first_name} — quick follow-up. We helped a company in {lead.industry} go from 10 to 200 qualified meetings/month with 0 added headcount. 15 minutes to show you how?",
                "timing": "Day 5",
                "goal": "Book demo"
            },
        ]


class OutreachSequencer:
    """Stores and executes outreach sequences."""

    def __init__(self):
        self.personalizer = OutreachPersonalizer()

    def create_sequence(self, lead: Lead, signals: List[Signal]) -> str:
        pkm_mode = self.personalizer.pkm.analyze(lead, signals)
        steps = self.personalizer.generate_sequence(lead, signals, pkm_mode)

        seq_id = secrets.token_hex(8)
        conn = get_db()
        for i, step in enumerate(steps):
            conn.execute("""
                INSERT INTO sequences (id, lead_id, step, channel, subject, body, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """, (
                f"{seq_id}-{i}",
                lead.id,
                i + 1,
                step.get("channel", "email"),
                step.get("subject", ""),
                step.get("body", ""),
            ))
        conn.commit()
        conn.close()

        # Update lead with PKM mode
        conn = get_db()
        conn.execute("""
            UPDATE leads SET pkm_defense=?, personalization=? WHERE id=?
        """, (pkm_mode, json.dumps(steps[:2]), lead.id))
        conn.commit()
        conn.close()

        return seq_id

    def send_step(self, seq_id: str, step: int) -> bool:
        """Send a specific step in the sequence (email via Instantly, etc.)."""
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM sequences WHERE id=?", (f"{seq_id}-{step-1}",))
        s = c.fetchone()
        conn.close()

        if not s:
            return False

        channel = s["channel"]
        if "email" in channel:
            return self._send_email(s)
        elif "linkedin" in channel:
            return self._send_linkedin(s)
        elif "twitter" in channel:
            return self._send_twitter_dm(s)
        return False

    def _send_email(self, step) -> bool:
        """Send via Instantly.ai API."""
        if not INSTANTLY_KEY:
            print(f"  [mock] Email sent: {step['subject']}")
            return True
        # Instantly API call
        try:
            r = requests.post(
                "https://api.instantly.ai/api/v1/lead/add",
                json={
                    "api_key": INSTANTLY_KEY,
                    "campaign_id": os.getenv("INSTANTLY_CAMPAIGN_ID", ""),
                    "skip_if_in_workspace": True,
                    "leads": [{"email": step["lead_id"], "firstName": "Lead",
                                "customVariables": {"body": step["body"]}}]
                },
                timeout=10
            )
            return r.status_code == 200
        except Exception:
            return False

    def _send_linkedin(self, step) -> bool:
        print(f"  [linkedin] Queue: {step['body'][:60]}...")
        return True

    def _send_twitter_dm(self, step) -> bool:
        print(f"  [twitter] Queue DM: {step['body'][:60]}...")
        return True


class LearningEngine:
    """Records outcomes and detects patterns for continuous improvement."""

    def record_outcome(self, lead_id: str, channel: str, outcome: str,
                       what_worked: str = "", what_failed: str = "",
                       pkm_mode: str = ""):
        conn = get_db()
        conn.execute("""
            INSERT INTO learnings (lead_id, channel, outcome, what_worked, what_failed, pkm_mode_detected)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (lead_id, channel, outcome, what_worked, what_failed, pkm_mode))
        conn.commit()
        conn.close()

    def best_performing(self) -> Dict:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT channel,
                   COUNT(*) as total,
                   SUM(CASE WHEN outcome='replied' OR outcome='booked' THEN 1 ELSE 0 END) as wins,
                   ROUND(100.0 * SUM(CASE WHEN outcome='replied' OR outcome='booked' THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
            FROM learnings
            GROUP BY channel
            ORDER BY win_rate DESC
        """)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return {"channel_performance": rows}

    def pkm_pattern_report(self) -> Dict:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT pkm_mode_detected,
                   COUNT(*) as occurrences,
                   SUM(CASE WHEN outcome IN ('replied','booked') THEN 1 ELSE 0 END) as bypassed
            FROM learnings
            WHERE pkm_mode_detected != ''
            GROUP BY pkm_mode_detected
            ORDER BY occurrences DESC
        """)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return {"pkm_modes": rows}


# ── OmniOutreach orchestrator ──────────────────────────────────────────────────
class OmniOutreach:
    """
    Master orchestrator: runs all signal collectors, scores leads,
    creates personalized sequences, tracks outcomes.
    """

    def __init__(self):
        self.collectors = [
            ApolloCollector(),
            CrunchbaseCollector(),
            ExaNewsCollector(),
            JobSignalCollector(),
            LinkedInSignalCollector(),
            G2ReviewCollector(),
            TwitterIntentCollector(),
            HunterCollector(),
        ]
        self.sequencer = OutreachSequencer()
        self.learning = LearningEngine()
        init_db()

    def _score_lead(self, signals: List[Signal]) -> float:
        """Composite intent score from all signals."""
        if not signals:
            return 0.3
        total = sum(s.score for s in signals)
        return min(total / len(signals) * (1 + len(signals) * 0.05), 1.0)

    def discover(self, industry: str = None, title: str = None,
                 limit: int = 20) -> List[Lead]:
        """Discovery phase: find leads via Apollo + funding signals."""
        print(f"\nDiscovering leads (industry={industry}, title={title}, limit={limit})...")

        apollo = ApolloCollector()
        people = apollo.search_people(title=title, industry=industry, limit=limit)

        leads = []
        conn = get_db()
        for person in people:
            org = person.get("organization", {}) or {}
            lead_id = secrets.token_hex(8)
            email = person.get("email", f"{person.get('first_name', 'lead').lower()}{lead_id[:4]}@unknown.com")

            lead = Lead(
                id=lead_id,
                first_name=person.get("first_name", ""),
                last_name=person.get("last_name", ""),
                email=email,
                title=person.get("title", ""),
                company=org.get("name", ""),
                industry=org.get("industry", industry or ""),
                linkedin_url=person.get("linkedin_url", ""),
            )

            # Collect signals for this company
            signals = []
            for collector in self.collectors[2:]:  # Skip Apollo (already used)
                try:
                    s = collector.collect(lead.company)
                    signals.extend(s)
                except Exception:
                    pass

            lead.intent_score = self._score_lead(signals)
            lead.signal_sources = json.dumps([s.source for s in signals])

            try:
                conn.execute("""
                    INSERT OR IGNORE INTO leads
                    (id, first_name, last_name, email, title, company, industry,
                     linkedin_url, intent_score, signal_sources)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (lead.id, lead.first_name, lead.last_name, lead.email,
                      lead.title, lead.company, lead.industry, lead.linkedin_url,
                      lead.intent_score, lead.signal_sources))
            except Exception:
                pass

            leads.append(lead)
            print(f"  + {lead.first_name} {lead.last_name} | {lead.title} @ {lead.company} | score={lead.intent_score:.2f}")

        conn.commit()
        conn.close()
        print(f"\nDiscovered {len(leads)} leads.")
        return leads

    def research(self, lead_email: str) -> Optional[Lead]:
        """Deep research phase for a specific lead."""
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM leads WHERE email=?", (lead_email,))
        row = c.fetchone()
        conn.close()

        if not row:
            print(f"Lead {lead_email} not found. Run discover first.")
            return None

        lead = Lead(**{k: row[k] for k in row.keys()
                       if k in Lead.__dataclass_fields__})

        # Enrich via Apollo
        apollo = ApolloCollector()
        enriched = apollo.enrich_person(lead.email)
        if enriched:
            lead.linkedin_url = enriched.get("linkedin_url", lead.linkedin_url)
            lead.title = enriched.get("title", lead.title)

        # Get email if missing
        if "@unknown.com" in lead.email and lead.company:
            hunter = HunterCollector()
            domain = lead.company.lower().replace(" ", "").replace("inc", "").replace("corp", "") + ".com"
            found_email = hunter.email_finder(domain, lead.first_name, lead.last_name)
            if found_email:
                lead.email = found_email
                conn = get_db()
                conn.execute("UPDATE leads SET email=? WHERE id=?", (lead.email, lead.id))
                conn.commit()
                conn.close()

        # Collect all signals
        all_signals = []
        for collector in self.collectors:
            try:
                signals = collector.collect(lead.company)
                all_signals.extend(signals)
            except Exception:
                pass

        # Save signals
        conn = get_db()
        for sig in all_signals:
            conn.execute("""
                INSERT INTO signals (lead_id, source, signal_type, content, score)
                VALUES (?, ?, ?, ?, ?)
            """, (lead.id, sig.source, sig.signal_type, sig.content, sig.score))
        conn.commit()
        conn.close()

        lead.intent_score = self._score_lead(all_signals)
        print(f"\nResearch complete: {lead.first_name} {lead.last_name}")
        print(f"  Intent score: {lead.intent_score:.2f}")
        print(f"  Signals found: {len(all_signals)}")
        return lead

    def launch_sequence(self, lead_email: str) -> Optional[str]:
        """Create and queue a full outreach sequence for this lead."""
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM leads WHERE email=?", (lead_email,))
        row = c.fetchone()
        conn.close()

        if not row:
            print(f"Lead {lead_email} not found.")
            return None

        lead = Lead(**{k: row[k] for k in row.keys()
                       if k in Lead.__dataclass_fields__})

        # Get saved signals
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM signals WHERE lead_id=?", (lead.id,))
        signal_rows = c.fetchall()
        conn.close()

        signals = [Signal(source=r["source"], signal_type=r["signal_type"],
                          content=r["content"], score=r["score"])
                   for r in signal_rows]

        seq_id = self.sequencer.create_sequence(lead, signals)
        print(f"\nSequence created: {seq_id}")
        print(f"  Lead: {lead.first_name} {lead.last_name} @ {lead.company}")
        print(f"  PKM defense: {lead.pkm_defense}")
        return seq_id

    def pipeline_report(self):
        """Summary of outreach pipeline."""
        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT COUNT(*) as n FROM leads")
        total = c.fetchone()["n"]
        c.execute("SELECT COUNT(*) as n FROM leads WHERE status='sequenced'")
        sequenced = c.fetchone()["n"]
        c.execute("SELECT AVG(intent_score) as avg FROM leads")
        avg_score = c.fetchone()["avg"] or 0
        c.execute("SELECT COUNT(*) as n FROM sequences WHERE status='sent'")
        sent = c.fetchone()["n"]

        conn.close()

        print(f"\nOutreach Pipeline Report")
        print(f"{'='*40}")
        print(f"  Total leads:       {total}")
        print(f"  Sequenced:         {sequenced}")
        print(f"  Avg intent score:  {avg_score:.2f}")
        print(f"  Sequence steps sent: {sent}")

        perf = self.learning.best_performing()
        if perf["channel_performance"]:
            print(f"\nChannel Performance:")
            for ch in perf["channel_performance"]:
                print(f"  {ch['channel']:20s}  {ch['win_rate']}% win rate ({ch['wins']}/{ch['total']})")

        pkm = self.learning.pkm_pattern_report()
        if pkm["pkm_modes"]:
            print(f"\nPKM Defense Modes Detected:")
            for mode in pkm["pkm_modes"]:
                print(f"  {mode['pkm_mode_detected']:20s}  {mode['occurrences']}x detected, {mode['bypassed']} bypassed")


# ── CLI ────────────────────────────────────────────────────────────────────────
def cli():
    import sys
    args = sys.argv[1:]

    if not args:
        print("AONXI Omni-Outreach Agent")
        print("  python3 src/omni_outreach.py scan [--industry INDUSTRY] [--title TITLE] [--limit N]")
        print("  python3 src/omni_outreach.py research EMAIL")
        print("  python3 src/omni_outreach.py sequence EMAIL")
        print("  python3 src/omni_outreach.py report")
        return

    agent = OmniOutreach()

    if args[0] == "scan":
        industry = None
        title = None
        limit = 20
        for i, arg in enumerate(args[1:], 1):
            if arg == "--industry" and i < len(args):
                industry = args[i]
            elif arg == "--title" and i < len(args):
                title = args[i]
            elif arg == "--limit" and i < len(args):
                limit = int(args[i])
        agent.discover(industry=industry, title=title, limit=limit)

    elif args[0] == "research" and len(args) > 1:
        agent.research(args[1])

    elif args[0] == "sequence" and len(args) > 1:
        agent.launch_sequence(args[1])

    elif args[0] == "report":
        agent.pipeline_report()

    else:
        print(f"Unknown command: {args[0]}")


if __name__ == "__main__":
    cli()
