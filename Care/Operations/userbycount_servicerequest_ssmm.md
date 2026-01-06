# User by Count - Service Request

> Number of service requests created by each user, ordered by activity level

## Purpose

This query tracks service request activity by user, showing how many service requests each staff member has created. It's useful for measuring staff productivity, workload distribution, and identifying the most active service requesters in the system.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `servicerequest_date` | DATE | Filters service requests by creation date | `DATE(emr_servicerequest.created_date) = '2026-01-06'` |
| `user_name` | TEXT | Filters by user name | `'John'` |

---

## Query

```sql
SELECT
    CONCAT(u.first_name, ' ', u.last_name) AS user_name,
    COUNT(sr.id) AS total_servicerequest
FROM emr_servicerequest sr
JOIN users_user u ON sr.created_by_id = u.id
WHERE sr.deleted = FALSE
--   [[AND {{servicerequest_date}}]]
--   [[AND CONCAT(u.first_name, ' ', u.last_name) = {{user_name}}]]
GROUP BY u.first_name, u.last_name
ORDER BY total_servicerequest DESC;
```



## Notes

- Only includes active service requests (deleted = FALSE)
- Results are ordered by request count (highest to lowest) to show most active users first


*Last updated: 2026-01-06*
