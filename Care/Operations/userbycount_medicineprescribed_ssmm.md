# User by Count - Medicine Prescribed

> Number of medication prescribed by each user, ordered by activity level

## Purpose

This query tracks medication prescription activity by user, showing how many prescriptions each staff member has created. It's useful for measuring prescriber productivity, workload distribution, and identifying the most active prescribers in the system.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `medicationrequestprescription_date` | DATE | Filters prescriptions by creation date | `DATE(emr_medicationrequestprescription.created_date) = '2026-01-06'` |
| `user_name` | TEXT | Filters by user name  | `'John'` |

---

## Query

```sql
SELECT
    CONCAT(u.first_name, ' ', u.last_name) AS user_name,
    COUNT(mrp.id) AS total_medicationrequestprescription
FROM emr_medicationrequestprescription mrp
JOIN users_user u ON mrp.prescribed_by_id = u.id
WHERE mrp.deleted = FALSE
--   [[AND {{medicationrequestprescription_date}}]]
--   [[AND CONCAT(u.first_name, ' ', u.last_name) = {{user_name}}]]
GROUP BY u.first_name, u.last_name
ORDER BY total_medicationrequestprescription DESC;
```



## Notes

- Only includes active prescriptions (deleted = FALSE)
- Results are ordered by prescription count (highest to lowest) to show most active prescribers first


*Last updated: 2026-01-06*
