# User by Count - Purchase Delivery

> Number of supply deliveries recorded by each user, ordered by activity level

## Purpose

This query tracks supply delivery activity by user, showing how many supply deliveries each staff member has recorded. It's useful for measuring inventory staff workload, delivery processing patterns, and identifying the most active delivery recorders in the system.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `supplydelivery_date` | DATE | Filters deliveries by creation date | `DATE(emr_supplydelivery.created_date) = '2026-01-06'` |
| `user_name` | TEXT | Filters by user name | `'John'` |

---

## Query

```sql
SELECT
    CONCAT(u.first_name, ' ', u.last_name) AS user_name,
    COUNT(sd.id) AS total_supplydelivery
FROM emr_supplydelivery sd
JOIN users_user u ON sd.created_by_id = u.id
WHERE sd.deleted = FALSE
--   [[AND {{supplydelivery_date}}]]
--   [[AND CONCAT(u.first_name, ' ', u.last_name) = {{user_name}}]]
GROUP BY u.first_name, u.last_name
ORDER BY total_supplydelivery DESC;
```


## Notes

- Only includes active supply deliveries (deleted = FALSE)
- Results are ordered by delivery count (highest to lowest) to show most active staff first

*Last updated: 2026-01-06*
