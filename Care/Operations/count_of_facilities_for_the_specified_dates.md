# Count of Facilities for the Specified Dates

> Cumulative number of facilities created on or before each created date

## Purpose

Returns the total number of facilities on the specified created dates (financial year ends and quarter ends).

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| *(none)* | - | Cut-off dates are hardcoded in the query | - |

---

## Query

```sql
SELECT
    COUNT(*) FILTER (WHERE DATE(created_date) <= DATE '2024-03-31') AS as_of_31_mar_2024,
    COUNT(*) FILTER (WHERE DATE(created_date) <= DATE '2025-03-31') AS as_of_31_mar_2025,
    COUNT(*) FILTER (WHERE DATE(created_date) <= DATE '2026-03-31') AS as_of_31_mar_2026,
    COUNT(*) FILTER (WHERE DATE(created_date) <= DATE '2026-06-30') AS as_of_30_jun_2026,
    COUNT(*) FILTER (WHERE DATE(created_date) <= DATE '2026-09-30') AS as_of_30_sep_2026
FROM facility_facility
WHERE deleted = FALSE;
```

## Notes

- **Cumulative counts:** Each column counts all facilities created on or before that date, not just the ones added in that period. Subtract adjacent columns to get new facilities per period.
- Output is a single row with one column per cut-off date.

*Last updated: 2026-10-12*
