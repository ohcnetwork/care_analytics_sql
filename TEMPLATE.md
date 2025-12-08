# Query Name

> Brief one-line description of what this query does

## Purpose

Explain the business use case or why this query exists.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `param_name` | TYPE | What it filters | `'example'` |

*Delete this section if no parameters.*

---

## Query

```sql
SELECT 
    column1,
    column2
FROM table_name
WHERE condition = 'value'
  [[AND {{optional_filter}}]];
```

### Output

| Column | Type | Description |
|--------|------|-------------|
| `column1` | TEXT | What this column contains |

---

## Drill-Down Query (Optional)

Returns detailed list when clicking through from the main query.

```sql
SELECT * FROM ...
```

### Output

| Column | Type | Description |
|--------|------|-------------|
| `column1` | TEXT | What this column contains |

---

## Notes

- Any important context, gotchas, or assumptions
- Performance considerations
- Hardcoded values to update (e.g., `facility_id = 2`)

*Last updated: YYYY-MM-DD*
