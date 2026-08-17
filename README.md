# Care Analytics

SQL queries used in Care analytics and Metabase dashboards.

## Structure

```
Care/
├── Accounting/      # Financial and billing queries
├── Clinical/        # Clinical data and outcomes
├── Encounter/       # Patient encounters and visits
├── Inventory/       # Stock and inventory management
├── Operations/      # Operational metrics
├── Organisation/    # Facility and org-level queries
├── Patient/         # Patient demographics and records
├── Scheduling/      # Appointments and scheduling
└── Services/        # Services and procedures

Care Apps/
└── Scribe/          # Scribe app queries

Internal/
├── Care HMIS Interview/
└── Leaderboard/
```

## Adding a New Query

Use the [QUERY_TEMPLATE.md](./TEMPLATE.md) as a starting point for new query files.

Each query file should include:
- **Name & Description** — What does it do?
- **Parameters** — Any variables to substitute
- **The SQL** — The actual query
- **Output** — What columns/data to expect
- **Notes** — Gotchas or context

## PR Review Bot

Every pull request is reviewed automatically by an agentic workflow
([`.github/workflows/analytics-review.md`](./.github/workflows/analytics-review.md)). It reviews through four lenses:

1. **Requirement fidelity** — fetches the JIRA ticket named by the PR branch and checks the query delivers exactly what was asked (metric, grain, filters, scope).
2. **SQL correctness** — applies the [care-sql-code-review skill](https://github.com/ohcnetwork/skills/tree/main/care-sql-code-review) (soft-delete/`entered_in_error` traps, facility scoping, join fan-out, sargability), verified against the CARE models.
3. **Documentation** — TEMPLATE.md conformance: sections accurate, magic IDs explained, Parameters table matches the `{{variables}}` actually used.
4. **Repo hygiene** — right domain folder, snake_case filename with deployment suffix (`_ssmm`, `_pallium`, `_kc`), one query per PR.

**Branch naming matters:** the bot finds the requirement via the branch name, which must be the JIRA ticket ID (e.g. `ENG-909`). No ticket in the branch name → the bot flags the missing linkage and reviews without requirement context.

**Talking to it:** reply to any of its inline comments, or @-mention it anywhere on the PR, and it will answer. It stops re-reviewing after 6 rounds per PR unless summoned with an @-mention. To silence it for a PR, mark the PR as draft.

**Prerequisites (admin setup):**
- Repo secrets `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` — for fetching ticket context. Without them the bot still runs, minus the requirement-fidelity lens.
- Org-level `COPILOT_GITHUB_TOKEN` — the Copilot engine credential already used by [care_fe's reviewer](https://github.com/ohcnetwork/care_fe/blob/develop/.github/workflows/care-review.md).
