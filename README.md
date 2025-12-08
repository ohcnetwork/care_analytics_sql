# Care Analytics

SQL queries used in Care analytics and Metabase dashboards.

## Structure

```
Care/
├── Accouting/       # Financial and billing queries
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
