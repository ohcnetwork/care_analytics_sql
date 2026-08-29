# Total Registrations and Revenue

> Summary of total registration fee revenue

## Purpose

This query provides aggregate metrics for patient registrations, showing the total number of registrations and cumulative revenue from registration fees. It's useful for tracking registration volumes and revenue trends over time.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE | Filters registration charge item by creation date | `DATE = '2025-12-29'` |

---

## Query

```sql
SELECT
  COUNT(*) AS total_registrations,
  SUM(emr_chargeitem.total_price) AS total_revenue
FROM emr_chargeitem
WHERE emr_chargeitem.deleted = FALSE
  AND emr_chargeitem.title = 'Registration Fee'
--   [[AND {{date}}]];
```


## Notes

- Only includes active charge items (deleted = FALSE)
- Filters specifically for 'Registration Fee' title

*Last updated: 2025-12-29*
