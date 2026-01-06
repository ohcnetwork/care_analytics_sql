# User by Count - Encounters Created

> Number of encounters created by each user

## Purpose

This query tracks encounter creation activity by user, showing how many encounters each staff member has created. It's useful for measuring staff productivity, workload distribution, and identifying the most active users in the system.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `encounter_date` | DATE | Filters encounters by creation date | `DATE(emr_encounter.created_date) = '2026-01-06'` |
| `user_name` | TEXT | Filters by user name | `'John'` |

---

## Query

```sql
SELECT
    CONCAT(users_user.first_name, ' ', users_user.last_name) AS user_name,
    COUNT(emr_encounter.id) AS total_encounter
FROM emr_encounter
JOIN users_user ON emr_encounter.created_by_id = users_user.id
WHERE emr_encounter.deleted = FALSE
--   [[AND {{encounter_date}}]]
--   [[AND CONCAT(users_user.first_name, ' ', users_user.last_name) = {{user_name}}]]
GROUP BY users_user.first_name, users_user.last_name
ORDER BY total_encounter DESC;
```


## Notes

- Only includes active encounters (deleted = FALSE)
- Results are ordered by encounter count (highest to lowest) to show most active users first

*Last updated: 2026-01-06*
