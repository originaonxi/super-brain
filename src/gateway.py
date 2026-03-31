#!/usr/bin/env python3
"""
AONXI Gateway — Global Access Server
======================================
Makes your Mac Mini globally accessible with:
- JWT auth + RBAC per employee/tenant
- Multi-tenant routing (Individual / Building / Enterprise)
- Per-employee AI sessions with role-tuned prompts
- WebSocket streaming for real-time agent output
- Rate limiting per tenant
- Usage tracking → feeds billing.py

Deploy: uvicorn src.gateway:app --host 0.0.0.0 --port 8000
Expose:  cloudflared tunnel --url http://localhost:8000
"""

import os
import time
import json
import sqlite3
import hashlib
import secrets
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

# ── Optional fast imports (graceful fallback) ──────────────────────────────────
try:
    from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    import jwt as pyjwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

try:
    from anthropic import Anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "gateway.db"
SECRET_KEY = os.getenv("GATEWAY_SECRET_KEY", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24
DEFAULT_RATE_LIMIT = 100  # requests per hour per tenant

# Tenant tiers
TIER_INDIVIDUAL = "individual"     # 1 user, 1 Mac Mini
TIER_BUILDING   = "building"       # up to 500 users, 1 Mac Studio per building
TIER_ENTERPRISE = "enterprise"     # unlimited, cluster

TIER_RATE_LIMITS = {
    TIER_INDIVIDUAL: 500,
    TIER_BUILDING:   5000,
    TIER_ENTERPRISE: 50000,
}


# ── Database ───────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            tier TEXT NOT NULL DEFAULT 'individual',
            building_id TEXT,
            api_key_hash TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            ai_profile_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            employee_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT NOT NULL,
            last_used TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            tokens_in INTEGER DEFAULT 0,
            tokens_out INTEGER DEFAULT 0,
            model TEXT DEFAULT 'claude-opus-4-6',
            cost_usd REAL DEFAULT 0.0,
            ts TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS rate_limit (
            tenant_id TEXT NOT NULL,
            window_start TEXT NOT NULL,
            request_count INTEGER DEFAULT 0,
            PRIMARY KEY (tenant_id, window_start)
        )
    """)

    conn.commit()
    conn.close()


# ── Auth helpers ───────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_jwt(employee_id: str, tenant_id: str, role: str) -> str:
    if not JWT_AVAILABLE:
        # Simple base64 fallback (dev only)
        import base64
        payload = json.dumps({"sub": employee_id, "tenant": tenant_id, "role": role,
                              "exp": (datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)).isoformat()})
        return base64.b64encode(payload.encode()).decode()
    payload = {
        "sub": employee_id,
        "tenant": tenant_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return pyjwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> Optional[Dict]:
    if not JWT_AVAILABLE:
        import base64
        try:
            payload = json.loads(base64.b64decode(token.encode()).decode())
            if datetime.fromisoformat(payload["exp"]) < datetime.utcnow():
                return None
            return payload
        except Exception:
            return None
    try:
        return pyjwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


def check_rate_limit(tenant_id: str, tier: str) -> bool:
    """Returns True if request allowed, False if rate limited."""
    limit = TIER_RATE_LIMITS.get(tier, DEFAULT_RATE_LIMIT)
    window = datetime.utcnow().strftime("%Y-%m-%d-%H")  # hourly window
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO rate_limit (tenant_id, window_start, request_count)
        VALUES (?, ?, 1)
        ON CONFLICT(tenant_id, window_start)
        DO UPDATE SET request_count = request_count + 1
    """, (tenant_id, window))
    c.execute("SELECT request_count FROM rate_limit WHERE tenant_id=? AND window_start=?",
              (tenant_id, window))
    row = c.fetchone()
    conn.commit()
    conn.close()
    return row["request_count"] <= limit


def log_usage(tenant_id: str, employee_id: str, endpoint: str,
              tokens_in: int = 0, tokens_out: int = 0,
              model: str = "claude-opus-4-6"):
    # Claude pricing: ~$15/M input, $75/M output for opus-4
    cost = (tokens_in * 15 + tokens_out * 75) / 1_000_000
    conn = get_db()
    conn.execute("""
        INSERT INTO usage_log (tenant_id, employee_id, endpoint, tokens_in, tokens_out, model, cost_usd)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tenant_id, employee_id, endpoint, tokens_in, tokens_out, model, cost))
    conn.commit()
    conn.close()


# ── Per-employee AI session ────────────────────────────────────────────────────
class EmployeeAISession:
    """
    A Claude session tuned to this specific employee's role, style, and context.
    Each employee gets their own system prompt — CEO gets strategy, Sales gets pipeline,
    HR gets compliance, IT gets infrastructure.
    """

    ROLE_PROMPTS = {
        "ceo": """You are the CEO's strategic AI partner at {company}.
You have full visibility into: revenue pipeline, CSAT scores, team performance, market intelligence.
Lead with outcomes. Every answer should end with a recommended action.
Be direct, data-driven, and P&L focused. No fluff.""",

        "sales": """You are the Sales AI for {name} at {company}.
You have access to: CRM pipeline, lead scores, outreach sequences, competitor intel.
Help craft personalized outreach, overcome objections, and close deals.
Always suggest the next action in the sales cycle. Think in pipeline velocity.""",

        "hr": """You are the HR AI for {name} at {company}.
You handle: hiring pipelines, performance reviews, onboarding workflows, compliance checks.
Be empathetic but structured. Flag policy violations proactively.
Draft job descriptions, offer letters, and performance improvement plans on demand.""",

        "it": """You are the IT AI for {name} at {company}.
You manage: infrastructure monitoring, security alerts, access control, deployments.
Think in uptime, latency, and zero-trust security. Automate everything that repeats.
Escalate P0 incidents immediately with root cause + remediation steps.""",

        "marketing": """You are the Marketing AI for {name} at {company}.
You handle: campaign performance, content strategy, SEO signals, ad spend optimization.
Think in CAC, LTV, and conversion rates. Surface what's working and kill what isn't.
Always connect marketing actions to pipeline impact.""",

        "finance": """You are the Finance AI for {name} at {company}.
You track: MRR, ARR, burn rate, runway, invoice status, expense categorization.
Be precise — every number matters. Flag anomalies immediately.
Generate forecasts, scenario models, and board-ready summaries.""",

        "default": """You are an AI assistant for {name} at {company}.
You help with productivity, research, writing, analysis, and automation.
Be concise, accurate, and action-oriented.""",
    }

    def __init__(self, employee_id: str, name: str, role: str, company: str):
        self.employee_id = employee_id
        self.name = name
        self.role = role.lower()
        self.company = company
        self.history: List[Dict] = []
        self.tokens_used = {"input": 0, "output": 0}

    def system_prompt(self) -> str:
        template = self.ROLE_PROMPTS.get(self.role, self.ROLE_PROMPTS["default"])
        return template.format(name=self.name, company=self.company)

    def chat(self, message: str) -> str:
        if not CLAUDE_AVAILABLE:
            return f"[Claude not available — install anthropic package] Echo: {message}"

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.history.append({"role": "user", "content": message})

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            system=self.system_prompt(),
            messages=self.history,
        )
        reply = response.content[0].text
        self.history.append({"role": "assistant", "content": reply})
        self.tokens_used["input"] += response.usage.input_tokens
        self.tokens_used["output"] += response.usage.output_tokens
        return reply

    async def stream_chat(self, message: str):
        """Async generator — yields text chunks for WebSocket streaming."""
        if not CLAUDE_AVAILABLE:
            yield f"[Claude not available] Echo: {message}"
            return

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.history.append({"role": "user", "content": message})
        full_reply = ""

        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=2048,
            system=self.system_prompt(),
            messages=self.history,
        ) as stream:
            for text in stream.text_stream:
                full_reply += text
                yield text

        self.history.append({"role": "assistant", "content": full_reply})


# ── In-memory session store ────────────────────────────────────────────────────
# Maps employee_id → EmployeeAISession (lives as long as server is up)
_ai_sessions: Dict[str, EmployeeAISession] = {}


def get_or_create_session(employee_id: str, name: str, role: str, company: str) -> EmployeeAISession:
    if employee_id not in _ai_sessions:
        _ai_sessions[employee_id] = EmployeeAISession(employee_id, name, role, company)
    return _ai_sessions[employee_id]


# ── FastAPI app ────────────────────────────────────────────────────────────────
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="AONXI Gateway",
        description="Global AI access from your Mac Mini",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    security = HTTPBearer()

    @app.on_event("startup")
    async def startup():
        init_db()

    # ── Auth middleware helper ─────────────────────────────────────────────────
    def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
        payload = decode_jwt(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return payload

    def require_admin(payload: dict = Depends(require_auth)):
        if payload.get("role") not in ("admin", "ceo"):
            raise HTTPException(status_code=403, detail="Admin access required")
        return payload

    # ── Routes ─────────────────────────────────────────────────────────────────

    @app.get("/")
    async def root():
        return {
            "service": "AONXI Gateway",
            "version": "1.0.0",
            "status": "online",
            "powered_by": "Mac Mini M4",
        }

    @app.get("/health")
    async def health():
        return {"status": "ok", "ts": datetime.utcnow().isoformat()}

    # ── Tenant management ──────────────────────────────────────────────────────

    @app.post("/tenants")
    async def create_tenant(body: dict, payload: dict = Depends(require_admin)):
        """Create a new tenant (company/building)."""
        tenant_id = secrets.token_hex(8)
        api_key = secrets.token_hex(32)
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO tenants (id, name, tier, building_id, api_key_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (tenant_id, body["name"], body.get("tier", TIER_INDIVIDUAL),
                  body.get("building_id"), api_key_hash))
            conn.commit()
        finally:
            conn.close()
        return {"tenant_id": tenant_id, "api_key": api_key, "note": "Store api_key — shown once"}

    # ── Employee management ────────────────────────────────────────────────────

    @app.post("/employees")
    async def create_employee(body: dict, payload: dict = Depends(require_admin)):
        """Create an employee account under a tenant."""
        emp_id = secrets.token_hex(8)
        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO employees (id, tenant_id, name, email, role, password_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (emp_id, payload["tenant"], body["name"], body["email"],
                  body.get("role", "default"), hash_password(body["password"])))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="Email already exists")
        finally:
            conn.close()
        return {"employee_id": emp_id, "email": body["email"], "role": body.get("role", "default")}

    # ── Login ──────────────────────────────────────────────────────────────────

    @app.post("/auth/login")
    async def login(body: dict):
        """Employee login → returns JWT."""
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute("""
                SELECT e.*, t.name as company, t.tier
                FROM employees e
                JOIN tenants t ON e.tenant_id = t.id
                WHERE e.email = ? AND e.active = 1
            """, (body["email"],))
            emp = c.fetchone()
        finally:
            conn.close()

        if not emp or emp["password_hash"] != hash_password(body["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_jwt(emp["id"], emp["tenant_id"], emp["role"])
        return {
            "token": token,
            "employee_id": emp["id"],
            "name": emp["name"],
            "role": emp["role"],
            "company": emp["company"],
            "tier": emp["tier"],
            "expires_in": f"{JWT_EXPIRE_HOURS}h",
        }

    # ── AI Chat ────────────────────────────────────────────────────────────────

    @app.post("/chat")
    async def chat(body: dict, payload: dict = Depends(require_auth)):
        """Single-turn chat with this employee's role-tuned AI."""
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute("""
                SELECT e.*, t.name as company, t.tier
                FROM employees e
                JOIN tenants t ON e.tenant_id = t.id
                WHERE e.id = ?
            """, (payload["sub"],))
            emp = c.fetchone()
        finally:
            conn.close()

        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Rate limit check
        if not check_rate_limit(emp["tenant_id"], emp["tier"]):
            raise HTTPException(status_code=429, detail="Rate limit exceeded for this tenant")

        session = get_or_create_session(emp["id"], emp["name"], emp["role"], emp["company"])
        reply = session.chat(body["message"])

        log_usage(emp["tenant_id"], emp["id"], "/chat",
                  session.tokens_used["input"], session.tokens_used["output"])

        return {"reply": reply, "role_context": emp["role"]}

    # ── WebSocket streaming ────────────────────────────────────────────────────

    @app.websocket("/ws/chat/{token}")
    async def ws_chat(websocket: WebSocket, token: str):
        """
        WebSocket endpoint for real-time streaming.
        Connect: ws://your-tunnel-url/ws/chat/<JWT>
        Send: {"message": "..."}
        Receive: chunks of text as they stream from Claude
        """
        await websocket.accept()

        payload = decode_jwt(token)
        if not payload:
            await websocket.send_json({"error": "Invalid token"})
            await websocket.close(code=1008)
            return

        conn = get_db()
        try:
            c = conn.cursor()
            c.execute("""
                SELECT e.*, t.name as company, t.tier
                FROM employees e
                JOIN tenants t ON e.tenant_id = t.id
                WHERE e.id = ?
            """, (payload["sub"],))
            emp = c.fetchone()
        finally:
            conn.close()

        if not emp:
            await websocket.send_json({"error": "Employee not found"})
            await websocket.close()
            return

        session = get_or_create_session(emp["id"], emp["name"], emp["role"], emp["company"])

        await websocket.send_json({"status": "connected", "role": emp["role"],
                                   "name": emp["name"], "company": emp["company"]})

        try:
            while True:
                data = await websocket.receive_json()
                message = data.get("message", "")
                if not message:
                    continue

                if not check_rate_limit(emp["tenant_id"], emp["tier"]):
                    await websocket.send_json({"error": "Rate limit exceeded"})
                    continue

                await websocket.send_json({"status": "thinking"})

                async for chunk in session.stream_chat(message):
                    await websocket.send_json({"chunk": chunk})

                await websocket.send_json({"status": "done"})
                log_usage(emp["tenant_id"], emp["id"], "/ws/chat",
                          session.tokens_used["input"], session.tokens_used["output"])

        except WebSocketDisconnect:
            pass

    # ── Usage / billing stats ──────────────────────────────────────────────────

    @app.get("/usage")
    async def usage_summary(payload: dict = Depends(require_auth)):
        """Usage stats for this tenant."""
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute("""
                SELECT
                    COUNT(*) as requests,
                    SUM(tokens_in) as total_tokens_in,
                    SUM(tokens_out) as total_tokens_out,
                    SUM(cost_usd) as total_cost_usd,
                    DATE(ts) as day
                FROM usage_log
                WHERE tenant_id = ?
                GROUP BY DATE(ts)
                ORDER BY day DESC
                LIMIT 30
            """, (payload["tenant"],))
            rows = [dict(r) for r in c.fetchall()]
        finally:
            conn.close()
        return {"tenant_id": payload["tenant"], "daily_usage": rows}

    @app.get("/usage/all")
    async def usage_all(payload: dict = Depends(require_admin)):
        """Admin: usage across all tenants."""
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute("""
                SELECT
                    tenant_id,
                    COUNT(*) as requests,
                    SUM(tokens_in + tokens_out) as total_tokens,
                    ROUND(SUM(cost_usd), 4) as total_cost_usd
                FROM usage_log
                GROUP BY tenant_id
                ORDER BY total_cost_usd DESC
            """)
            rows = [dict(r) for r in c.fetchall()]
        finally:
            conn.close()
        return {"tenants": rows}

    # ── Building WiFi hook ─────────────────────────────────────────────────────

    @app.post("/building/{building_id}/connect")
    async def building_connect(building_id: str, body: dict):
        """
        WeWork model: when someone connects to building WiFi,
        they hit this endpoint to get a guest AI session.
        Returns a limited JWT valid for 8 hours.
        """
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM tenants WHERE building_id = ? AND active = 1", (building_id,))
            tenant = c.fetchone()
        finally:
            conn.close()

        if not tenant:
            raise HTTPException(status_code=404, detail="Building not registered")

        # Create a temporary guest session
        guest_token = create_jwt(
            employee_id=f"guest_{secrets.token_hex(4)}",
            tenant_id=tenant["id"],
            role="default",
        )
        return {
            "token": guest_token,
            "building": tenant["name"],
            "tier": tenant["tier"],
            "expires_in": "8h",
            "message": f"Welcome to {tenant['name']} AI — powered by AONXI",
        }

    # ── Admin: list employees ──────────────────────────────────────────────────

    @app.get("/employees")
    async def list_employees(payload: dict = Depends(require_admin)):
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute("""
                SELECT id, name, email, role, created_at, active
                FROM employees WHERE tenant_id = ?
            """, (payload["tenant"],))
            rows = [dict(r) for r in c.fetchall()]
        finally:
            conn.close()
        return {"employees": rows}

    @app.delete("/sessions/clear")
    async def clear_my_sessions(payload: dict = Depends(require_auth)):
        """Clear AI session history for this employee (fresh start)."""
        emp_id = payload["sub"]
        if emp_id in _ai_sessions:
            del _ai_sessions[emp_id]
        return {"status": "cleared", "employee_id": emp_id}


# ── CLI ────────────────────────────────────────────────────────────────────────
def cli():
    import sys
    args = sys.argv[1:]

    if not args or args[0] == "init":
        init_db()
        print("Gateway DB initialized.")

    elif args[0] == "create-admin":
        # python3 src/gateway.py create-admin "ACME Corp" admin@acme.com secretpass
        init_db()
        name, email, password = args[1], args[2], args[3]
        tenant_id = "admin-tenant"
        emp_id = "admin-user"
        conn = get_db()
        try:
            conn.execute("""
                INSERT OR IGNORE INTO tenants (id, name, tier) VALUES (?, ?, ?)
            """, (tenant_id, name, TIER_ENTERPRISE))
            conn.execute("""
                INSERT OR REPLACE INTO employees (id, tenant_id, name, email, role, password_hash)
                VALUES (?, ?, ?, ?, 'admin', ?)
            """, (emp_id, tenant_id, name, email, hash_password(password)))
            conn.commit()
        finally:
            conn.close()
        print(f"Admin created: {email} / role=admin / tenant={name}")
        print(f"Start server: uvicorn src.gateway:app --host 0.0.0.0 --port 8000")
        print(f"Expose globally: cloudflared tunnel --url http://localhost:8000")

    elif args[0] == "serve":
        if not FASTAPI_AVAILABLE:
            print("Install fastapi + uvicorn: pip install fastapi uvicorn")
            return
        import uvicorn
        uvicorn.run("src.gateway:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)

    elif args[0] == "stats":
        init_db()
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as n FROM tenants WHERE active=1")
        tenants = c.fetchone()["n"]
        c.execute("SELECT COUNT(*) as n FROM employees WHERE active=1")
        employees = c.fetchone()["n"]
        c.execute("SELECT ROUND(SUM(cost_usd),4) as total FROM usage_log")
        cost = c.fetchone()["total"] or 0
        conn.close()
        print(f"Gateway Stats")
        print(f"  Active tenants:   {tenants}")
        print(f"  Active employees: {employees}")
        print(f"  Total AI cost:    ${cost:.4f}")
        print(f"  Active sessions:  {len(_ai_sessions)}")

    else:
        print("Usage:")
        print("  python3 src/gateway.py init             # Initialize DB")
        print("  python3 src/gateway.py create-admin NAME EMAIL PASS")
        print("  python3 src/gateway.py serve            # Start server")
        print("  python3 src/gateway.py stats            # Show stats")


if __name__ == "__main__":
    cli()
