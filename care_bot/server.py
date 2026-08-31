"""
CARE Report Bot — privacy-preserving analytics chat bot.

Architecture:
    user question ──▶ LLM (sees: question + schema knowledge, NEVER patient rows)
                          │ generates SQL
                          ▼
                  this server runs it via the Metabase API
                          │
        ┌─────────────────┴──────────────────┐
        ▼                                    ▼
  discovery query                      final report query
  (config tables only —                (results go DIRECTLY to the
   guarded; results DO                  user's browser; the LLM only
   return to the LLM)                   receives row_count + columns)
"""

import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

METABASE_URL = os.environ["METABASE_URL"].rstrip("/")
METABASE_API_KEY = os.environ["METABASE_API_KEY"]
DATABASE_ID = int(os.environ.get("METABASE_DATABASE_ID", "3"))

# Gemini's free tier, accessed via its OpenAI-compatible endpoint.
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

MAX_HISTORY_MESSAGES = 40          # cap conversation growth
MAX_DISCOVERY_ROWS = 200           # rows of config data returned to the LLM
MAX_RESULT_ROWS = 1000             # rows of report data sent to the browser
AUDIT_LOG = BASE_DIR / "audit.jsonl"

# ---------------------------------------------------------------- system prompt

SKILL_FILE = BASE_DIR.parent / "CARE_SQL_ASSISTANT_SKILL.md"
BOT_INSTRUCTIONS = (BASE_DIR / "bot_instructions.md").read_text(encoding="utf-8")
SYSTEM_PROMPT = (
    BOT_INSTRUCTIONS
    + "\n\n---\n\n# KNOWLEDGE BASE (CARE HMIS SQL Assistant Skill)\n\n"
    + SKILL_FILE.read_text(encoding="utf-8")
)

# ---------------------------------------------------------------- tools

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_discovery_query",
            "description": (
                "Run a read-only CONFIGURATION lookup (facilities, identifier configs, tag "
                "configs, questionnaires, value sets, organisations, information_schema, "
                "SELECT DISTINCT status checks). Results ARE returned to you. MUST NOT touch "
                "emr_patient / emr_patientidentifier tables or personal columns — the server "
                "rejects violations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "The SELECT query to run."},
                    "purpose": {"type": "string", "description": "One line: what you are looking up."},
                },
                "required": ["sql", "purpose"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_final_query",
            "description": (
                "Run the FINAL report query. The result rows are sent DIRECTLY to the user's "
                "chat — you never see them. You receive only row_count and column names."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "The final SELECT query."},
                    "title": {"type": "string", "description": "Short business-friendly title for the result card."},
                    "display": {
                        "type": "string",
                        "enum": ["number", "table", "line", "bar", "pie"],
                        "description": "Recommended visualisation for the result.",
                    },
                },
                "required": ["sql", "title", "display"],
            },
        },
    },
]

# ---------------------------------------------------------------- guards

SELECT_ONLY = re.compile(r"^\s*(--[^\n]*\n|\s)*(select|with)\b", re.IGNORECASE)
PATIENT_TABLES = re.compile(r"\bemr_patient\b|\bemr_patientidentifier\b", re.IGNORECASE)
PERSONAL_COLUMNS = re.compile(r"\bphone_number\b|\bdate_of_birth\b|\baddress\b", re.IGNORECASE)


def sql_guard(sql: str, discovery: bool) -> str | None:
    """Return an error string if the SQL violates policy, else None."""
    if not SELECT_ONLY.match(sql):
        return "Rejected: only SELECT/WITH queries are allowed."
    if ";" in sql.rstrip().rstrip(";"):
        return "Rejected: multiple statements are not allowed."
    if discovery:
        if PATIENT_TABLES.search(sql):
            return (
                "Rejected: discovery queries must not reference emr_patient or "
                "emr_patientidentifier. Use run_final_query for report data."
            )
        if PERSONAL_COLUMNS.search(sql):
            return "Rejected: discovery queries must not select personal columns."
    return None


def sanitize_error(message: str) -> str:
    """Strip quoted data values from DB errors before they reach the LLM."""
    cleaned = re.sub(r"'[^']*'", "'…'", str(message))
    return cleaned[:500]


# ---------------------------------------------------------------- metabase client

def run_metabase_query(sql: str) -> dict:
    response = httpx.post(
        f"{METABASE_URL}/api/dataset",
        headers={"X-API-KEY": METABASE_API_KEY, "Content-Type": "application/json"},
        json={"database": DATABASE_ID, "type": "native", "native": {"query": sql}},
        timeout=120,
    )
    body = response.json()
    if response.status_code >= 400 or body.get("status") == "failed":
        return {"error": sanitize_error(body.get("error") or body)}
    data = body.get("data", {})
    columns = [col.get("display_name") or col.get("name") for col in data.get("cols", [])]
    return {"columns": columns, "rows": data.get("rows", [])}


def audit(session_id: str, kind: str, sql: str, outcome: str) -> None:
    entry = {
        "at": datetime.now(timezone.utc).isoformat(),
        "session": session_id,
        "kind": kind,
        "sql": sql,
        "outcome": outcome,
    }
    with open(AUDIT_LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


app = FastAPI(title="CARE Report Bot")


# ---------------------------------------------------------------- saved queries & dashboards
#
# Simple JSON-file-backed storage (no database needed for this pilot). Lets the
# user re-run a query later, or build a lightweight "dashboard" (a named group
# of saved queries) without needing to touch Metabase directly.

SAVED_QUERIES_FILE = BASE_DIR / "saved_queries.json"
DASHBOARDS_FILE = BASE_DIR / "dashboards.json"
TEMPLATE_TAG_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def load_store(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def save_store(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


saved_queries: dict[str, dict] = load_store(SAVED_QUERIES_FILE)
dashboards: dict[str, dict] = load_store(DASHBOARDS_FILE)


def build_template_tags(sql: str) -> dict:
    """Metabase requires any {{variable}} in a native query to be declared as a
    template tag before the card can be saved via the API."""
    tags = {}
    for name in set(TEMPLATE_TAG_RE.findall(sql)):
        tag_type = "date" if "date" in name.lower() else "text"
        tags[name] = {
            "id": str(uuid.uuid4()),
            "name": name,
            "display-name": name.replace("_", " ").title(),
            "type": tag_type,
        }
    return tags


def create_metabase_question(name: str, sql: str) -> dict:
    template_tags = build_template_tags(sql)
    payload = {
        "name": name,
        "dataset_query": {
            "type": "native",
            "native": {"query": sql, "template-tags": template_tags},
            "database": DATABASE_ID,
        },
        "display": "table",
        "visualization_settings": {},
    }
    response = httpx.post(
        f"{METABASE_URL}/api/card",
        headers={"X-API-KEY": METABASE_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=sanitize_error(response.text))
    body = response.json()
    return {
        "id": body["id"],
        "url": f"{METABASE_URL}/question/{body['id']}",
        "has_date_filter": any(tag["type"] == "date" for tag in template_tags.values()),
    }


class RunSqlRequest(BaseModel):
    sql: str


class SaveLocalRequest(BaseModel):
    name: str
    sql: str


class SaveMetabaseRequest(BaseModel):
    name: str
    sql: str


class CreateDashboardRequest(BaseModel):
    name: str


class DashboardQueryRequest(BaseModel):
    query_id: str


@app.post("/run_sql")
def run_sql(request: RunSqlRequest):
    """Re-execute a previously-generated SQL query (e.g. re-running a saved
    query). Used by the frontend's Saved-queries list, not by the LLM."""
    outcome = run_metabase_query(request.sql)
    if "error" in outcome:
        return {"error": outcome["error"], "sql": request.sql}
    return {
        "title": "Result",
        "display": "table",
        "columns": outcome["columns"],
        "rows": outcome["rows"][:MAX_RESULT_ROWS],
        "sql": request.sql,
    }


@app.get("/saved")
def list_saved_queries():
    return {"items": list(saved_queries.values())}


@app.post("/saved")
def save_query_locally(request: SaveLocalRequest):
    query_id = str(uuid.uuid4())
    entry = {
        "id": query_id,
        "name": request.name,
        "sql": request.sql,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    saved_queries[query_id] = entry
    save_store(SAVED_QUERIES_FILE, saved_queries)
    return entry


@app.delete("/saved/{query_id}")
def delete_saved_query(query_id: str):
    saved_queries.pop(query_id, None)
    save_store(SAVED_QUERIES_FILE, saved_queries)
    changed = False
    for dash in dashboards.values():
        if query_id in dash["query_ids"]:
            dash["query_ids"].remove(query_id)
            changed = True
    if changed:
        save_store(DASHBOARDS_FILE, dashboards)
    return {"deleted": True}


@app.post("/save_to_metabase")
def save_query_to_metabase(request: SaveMetabaseRequest):
    return create_metabase_question(request.name, request.sql)


@app.get("/dashboards")
def list_dashboards():
    return {"items": list(dashboards.values())}


@app.post("/dashboards")
def create_dashboard(request: CreateDashboardRequest):
    dashboard_id = str(uuid.uuid4())
    entry = {
        "id": dashboard_id,
        "name": request.name,
        "query_ids": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    dashboards[dashboard_id] = entry
    save_store(DASHBOARDS_FILE, dashboards)
    return entry


@app.delete("/dashboards/{dashboard_id}")
def delete_dashboard(dashboard_id: str):
    dashboards.pop(dashboard_id, None)
    save_store(DASHBOARDS_FILE, dashboards)
    return {"deleted": True}


@app.post("/dashboards/{dashboard_id}/queries")
def add_query_to_dashboard(dashboard_id: str, request: DashboardQueryRequest):
    dashboard = dashboards.get(dashboard_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    if request.query_id not in dashboard["query_ids"]:
        dashboard["query_ids"].append(request.query_id)
        save_store(DASHBOARDS_FILE, dashboards)
    return dashboard


@app.delete("/dashboards/{dashboard_id}/queries/{query_id}")
def remove_query_from_dashboard(dashboard_id: str, query_id: str):
    dashboard = dashboards.get(dashboard_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    if query_id in dashboard["query_ids"]:
        dashboard["query_ids"].remove(query_id)
        save_store(DASHBOARDS_FILE, dashboards)
    return dashboard


# ---------------------------------------------------------------- agent loop

llm_client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    timeout=30,       # fail fast instead of hanging on Gemini overload (default is 10 minutes)
    max_retries=2,
)
sessions: dict[str, list] = {}


class ChatRequest(BaseModel):
    session_id: str
    message: str


def trim_history(history: list, max_messages: int) -> None:
    """Trim in place, but only at a 'user' message boundary. Gemini rejects a
    conversation where a tool call/response pair is split across the cut, or where
    the history doesn't start on a user turn — a plain history[-N:] slice can do both."""
    if len(history) <= max_messages:
        return
    cutoff = len(history) - max_messages
    for i in range(cutoff, len(history)):
        if history[i].get("role") == "user":
            del history[:i]
            return
    # No user-role boundary found in the trim window — leave history untouched
    # rather than risk corrupting the tool-call structure.


@app.post("/chat")
def chat(request: ChatRequest):
    history = sessions.setdefault(request.session_id, [])
    history.append({"role": "user", "content": request.message})
    trim_history(history, MAX_HISTORY_MESSAGES)

    results_for_user: list[dict] = []

    for _ in range(12):  # hard cap on tool round-trips per turn
        response = llm_client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            tools=TOOLS,
            max_tokens=4096,
        )
        message = response.choices[0].message
        tool_calls = [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.function.name, "arguments": call.function.arguments},
                # Gemini 3+ models require this to be resent verbatim on the next turn,
                # or replaying the tool call fails with a thought_signature error.
                **({"extra_content": call.extra_content} if getattr(call, "extra_content", None) else {}),
            }
            for call in (message.tool_calls or [])
        ]
        history.append(
            {
                "role": "assistant",
                "content": message.content,
                **({"tool_calls": tool_calls} if tool_calls else {}),
            }
        )

        if not tool_calls:
            return {"reply": message.content or "", "results": results_for_user}

        for call in message.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            sql = (args.get("sql") or "").strip()

            if call.function.name == "run_discovery_query":
                violation = sql_guard(sql, discovery=True)
                if violation:
                    outcome = {"error": violation}
                else:
                    outcome = run_metabase_query(sql)
                    if "rows" in outcome:
                        outcome["rows"] = outcome["rows"][:MAX_DISCOVERY_ROWS]
                audit(request.session_id, "discovery", sql, "error" if "error" in outcome else "ok")
                history.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(outcome, default=str)[:30000],
                    }
                )

            elif call.function.name == "run_final_query":
                violation = sql_guard(sql, discovery=False)
                if violation:
                    outcome_meta: dict = {"error": violation}
                else:
                    outcome = run_metabase_query(sql)
                    if "error" in outcome:
                        outcome_meta = {"error": outcome["error"]}
                    else:
                        # Rows go to the USER only — the LLM gets metadata.
                        results_for_user.append(
                            {
                                "title": args.get("title", "Result"),
                                "display": args.get("display", "table"),
                                "columns": outcome["columns"],
                                "rows": outcome["rows"][:MAX_RESULT_ROWS],
                                "sql": sql,
                            }
                        )
                        outcome_meta = {
                            "status": "ok",
                            "row_count": len(outcome["rows"]),
                            "columns": outcome["columns"],
                            "note": "Rows were delivered directly to the user; you cannot see them.",
                        }
                audit(request.session_id, "final", sql, "error" if "error" in outcome_meta else "ok")
                history.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(outcome_meta, default=str),
                    }
                )

    return {
        "reply": "Sorry — I could not complete that request. Please try rephrasing it.",
        "results": results_for_user,
    }


@app.get("/")
def index():
    # no-cache: this file changes often during development; avoid stale JS/CSS
    # surviving a normal refresh in the browser.
    return FileResponse(
        BASE_DIR / "static" / "index.html",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
