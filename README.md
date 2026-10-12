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

**Branch naming matters:** the bot finds the requirement via the branch name, which must be the JIRA ticket ID (e.g. `ENG-909`). No ticket in the branch name → the bot flags the missing linkage and reviews without requirement context. If you reuse a branch after its PR was merged (say, a follow-up on the same ticket), rebase it onto `main` first: otherwise GitHub shows the whole file as new and the PR conflicts (the bot detects this, reviews only the real change, and asks for a rebase).

**Talking to it:** reply to any of its inline comments, or mention `@github-actions` anywhere on the PR, and it will answer. Each run answers every reply still waiting on it, so a burst of replies is handled together. While a PR has merge conflicts, GitHub doesn't deliver review-thread replies to the bot; they're answered on the next push (or @-mention it in the conversation). It stops re-reviewing after 6 rounds per PR unless summoned with an @-mention. To silence it for a PR, mark the PR as draft.

**Approvals:** when a PR clears its bar (ticket fetched and delivered, no open Critical/High findings, clean lint, no conflicts), the bot approves. `main` requires two approvals and drops them on every push, so the bot's approval is one of the two and a human must still review and approve. It never requests changes.

**Prerequisites (admin setup):**
- Branch protection on `main`: **2** required approvals, **dismiss stale approvals** when new commits are pushed, and **require approval of the most recent push**. The bot's approvals are only safe with these. If you ever lower the count to 1, first set `allowed-events` back to `[COMMENT]` in the workflow, or the bot's approval alone could satisfy the merge rule.
- Settings → Actions → General → **Allow GitHub Actions to create and approve pull requests** turned on.
- Repo secrets `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` — for fetching ticket context. For Atlassian API tokens **with scopes**, `JIRA_BASE_URL` must be `https://api.atlassian.com/ex/jira/<cloudId>`; only unscoped tokens work against `https://<site>.atlassian.net`. Discover the cloudId with `curl -s https://<site>.atlassian.net/_edge/tenant_info` (public endpoint, no credentials needed). The workflow auto-recovers from a `*.atlassian.net` base URL by doing that lookup itself, and otherwise writes a self-diagnosing note into the review context. Without these secrets the bot still runs, minus the requirement-fidelity lens.
- Org-level `COPILOT_GITHUB_TOKEN` — the Copilot engine credential already used by [care_fe's reviewer](https://github.com/ohcnetwork/care_fe/blob/develop/.github/workflows/care-review.md).
