# Users by Count - Medication Dispensed

> Number of medication dispenses recorded by each user, ordered by activity level

## Purpose

This query tracks medication dispensing activity by user, showing how many medication dispenses each staff member has recorded. It's useful for measuring pharmacy staff workload, dispensing patterns, and identifying the most active dispensers in the system.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `medicationdispense_date` | DATE | Filters dispenses by creation date | `DATE(emr_medicationdispense.created_date) = '2026-01-06'` |
| `user_name` | TEXT | Filters by user name | `'John'` |

---

## Query

```sql
SELECT
    CONCAT(u.first_name, ' ', u.last_name) AS user_name,
    COUNT(md.id) AS total_medicationdispense
FROM emr_medicationdispense md
JOIN users_user u ON md.created_by_id = u.id
WHERE md.deleted = FALSE
--   [[AND {{medicationdispense_date}}]]
--   [[AND CONCAT(u.first_name, ' ', u.last_name) = {{user_name}}]]
GROUP BY u.first_name, u.last_name
ORDER BY total_medicationdispense DESC;
```


## Notes

- Only includes active medication dispenses (deleted = FALSE)
- Results are ordered by dispense count (highest to lowest) to show most active staff first


*Last updated: 2026-01-06*
