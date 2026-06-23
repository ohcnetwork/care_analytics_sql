# User by Count - Medication Administered

> Number of medication administrations recorded by each user, ordered by activity level

## Purpose

This query tracks medication administration activity by user, showing how many medication administrations each staff member has recorded. It's useful for measuring staff workload, medication administration patterns, and identifying the most active administrators in the system.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `medicationadministration_date` | DATE | Filters administrations by creation date | `DATE(emr_medicationadministration.created_date) = '2026-01-06'` |
| `user_name` | TEXT | Filters by user name | `'John'` |

---

## Query

```sql
SELECT
    CONCAT(u.first_name, ' ', u.last_name) AS user_name,
    COUNT(ma.id) AS total_medicationadministration
FROM emr_medicationadministration ma
JOIN users_user u ON ma.created_by_id = u.id
WHERE ma.deleted = FALSE
--   [[AND {{medicationadministration_date}}]]
--   [[AND CONCAT(u.first_name, ' ', u.last_name) = {{user_name}}]]
GROUP BY u.first_name, u.last_name
ORDER BY total_medicationadministration DESC;
```


## Notes

- Only includes active medication administrations (deleted = FALSE)
- Results are ordered by administration count (highest to lowest) to show most active staff first


*Last updated: 2026-01-06*
