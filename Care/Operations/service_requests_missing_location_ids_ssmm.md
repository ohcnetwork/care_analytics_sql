
# Service Requests Missing Location IDs - SSMM

> Completed service requests that have no associated facility location IDs

## Purpose

Lists completed (`status = 'completed'`) service requests at SSMM where the `locations` array is empty.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE / range | Metabase date filter (typically bound to `sr.created_date`) | `'2026-06-01'` |

---

## Query

```sql
SELECT
    sr.id,
    sr.created_date,
    sr.title,
    sr.category,
    sr.status,
    sr.locations
FROM emr_servicerequest sr
WHERE sr.deleted = FALSE
  AND sr.status = 'completed'
   AND sr.locations = '{}'
  --[[AND {{date}}]]
ORDER BY sr.created_date DESC;
```

## Notes

- **Metabase filters:**
  - `[[AND {{date}}]]` is a field filter — bind it to `sr.created_date` in the Metabase variable settings.
- Results are ordered by most recent `created_date` first so the latest data-quality issues surface at the top.

*Last updated: 2026-06-19*
