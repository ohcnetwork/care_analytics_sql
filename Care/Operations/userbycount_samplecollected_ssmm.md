# User by Count - Sample Collected

> Number of specimens collected by each user, ordered by activity level

## Purpose

This query tracks specimen collection activity by user, showing how many available specimens each staff member has collected. It's useful for measuring lab staff productivity, collection workload distribution, and identifying the most active specimen collectors in the system.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `specimen_date` | DATE | Filters specimens by creation date | `DATE(emr_specimen.created_date) = '2026-01-06'` |
| `user_name` | TEXT | Filters by user name | `'John'` |

---

## Query

```sql
SELECT
    CONCAT(u.first_name, ' ', u.last_name) AS user_name,
    COUNT(sp.id) AS total_specimen
FROM emr_specimen sp
JOIN users_user u ON sp.created_by_id = u.id
WHERE sp.deleted = FALSE
  AND sp.status = 'available'
--   [[AND {{specimen_date}}]]
--   [[AND CONCAT(u.first_name, ' ', u.last_name) = {{user_name}}]]
GROUP BY u.first_name, u.last_name
ORDER BY total_specimen DESC;
```



## Notes

- Only includes active specimens (deleted = FALSE)
- Query only counts specimens with status = 'available'
- Results are ordered by specimen count (highest to lowest) to show most active collectors first


*Last updated: 2026-01-06*
