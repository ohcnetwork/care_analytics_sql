# Users by Count - Diagnostic Report

> Number of diagnostic reports created by each user, ordered by activity level

## Purpose

This query tracks diagnostic report creation activity by user, showing how many diagnostic reports each staff member has created. It's useful for measuring lab staff productivity, reporting workload distribution, and identifying the most active report creators in the system.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `servicerequest_date` | DATE | Filters diagnostic reports by creation date | `DATE(emr_diagnosticreport.created_date) = '2026-01-06'` |
| `user_name` | TEXT | Filters by user name | `'John'` |

---

## Query

```sql
SELECT
    CONCAT(u.first_name, ' ', u.last_name) AS user_name,
    COUNT(dr.id) AS total_diagnosticrequest
FROM emr_diagnosticreport dr
JOIN users_user u ON dr.created_by_id = u.id
WHERE dr.deleted = FALSE
--   [[AND {{servicerequest_date}}]]
--   [[AND CONCAT(u.first_name, ' ', u.last_name) = {{user_name}}]]
GROUP BY u.first_name, u.last_name
ORDER BY total_diagnosticrequest DESC;
```



## Notes

- Only includes active diagnostic reports (deleted = FALSE)
- Results are ordered by report count (highest to lowest) to show most active users first


*Last updated: 2026-01-06*
