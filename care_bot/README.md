# CARE Report Bot

A privacy-preserving chat bot that turns plain-language questions into CARE HMIS reports. Users chat; the bot writes and runs the SQL against Metabase; results appear as cards in the chat. **The LLM never sees patient data.**

## Privacy architecture

```
user question ──▶ LLM  (sees: question + schema knowledge — NEVER patient rows)
                    │ generates SQL
                    ▼
              this server runs it via the Metabase API
                    │
   ┌────────────────┴─────────────────────┐
   ▼                                      ▼
discovery query                     final report query
(config tables only — server-       (rows are sent DIRECTLY to the
 guarded; results DO return          user's browser; the LLM receives
 to the LLM: facility lists,         only row_count + column names)
 questionnaire lists, etc.)
```

Enforced server-side (`sql_guard` in [server.py](server.py)):
- Read-only: `SELECT`/`WITH` only, single statement
- Discovery queries may not reference `emr_patient` / `emr_patientidentifier` or personal columns
- Database error messages are sanitised (quoted values stripped) before reaching the LLM
- Every executed query is appended to `audit.jsonl` (who/when/what/outcome)

The bot's knowledge comes from [../CARE_SQL_ASSISTANT_SKILL.md](../CARE_SQL_ASSISTANT_SKILL.md) (loaded read-only at startup) plus [bot_instructions.md](bot_instructions.md).

## Setup

```bash
cd care_bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env with your real keys
```

`.env` needs:
| Variable | Value |
|---|---|
| `METABASE_URL` | `https://metabase.ohc.network` |
| `METABASE_API_KEY` | A Metabase API key (ideally from a **read-only** Metabase user) |
| `METABASE_DATABASE_ID` | `3` |
| `GEMINI_API_KEY` | From https://aistudio.google.com/apikey (free tier) |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` (default) |

## Run

```bash
uvicorn server:app --host 127.0.0.1 --port 8080
```

Open http://127.0.0.1:8080 and ask: *"How many appointments were booked this month?"*

## Notes & limitations

- **Sessions are in-memory** — restarting the server clears conversations. Fine for a pilot; add Redis/DB persistence for production.
- **No authentication** — bind to localhost or put it behind your org's SSO/reverse proxy before sharing. Anyone who can reach the port can query.
- The Metabase API key should belong to a **read-only** Metabase user, so even a bad query cannot write.
- To move to Slack/WhatsApp later: keep `server.py`'s agent loop and guards; swap the FastAPI `/chat` + HTML UI for the platform's webhook — the privacy model is in the loop, not the UI.
- Costs: each question makes 1–4 LLM calls (more if discovery is needed). The skill file (~15k tokens) is sent as the system prompt on every call; enable prompt caching in production to cut this sharply.
