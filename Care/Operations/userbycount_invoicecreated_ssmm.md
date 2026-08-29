# User by Count - Invoice Created

> Number of invoices created by each user with status breakdown, ordered by activity level

## Purpose

This query tracks invoice creation activity by user, showing how many invoices each staff member has created along with a breakdown by status (draft, balanced, issued). It's useful for measuring billing staff productivity, workload distribution, and understanding invoice processing stages.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `invoice_date` | DATE | Filters invoices by creation date | `DATE(emr_invoice.created_date) = '2026-01-06'` |
| `user_name` | TEXT | Filters by user name | `'John'` |

---

## Query

```sql
SELECT
    CONCAT(u.first_name, ' ', u.last_name) AS user_name,
    COUNT(inv.id) AS total_invoices,
    SUM(CASE WHEN inv.status = 'draft' THEN 1 ELSE 0 END) AS draft_count,
    SUM(CASE WHEN inv.status = 'balanced' THEN 1 ELSE 0 END) AS balanced_count,
    SUM(CASE WHEN inv.status = 'issued' THEN 1 ELSE 0 END) AS issued_count
FROM emr_invoice inv
JOIN users_user u ON inv.created_by_id = u.id
WHERE inv.deleted = FALSE
--   [[AND {{invoice_date}}]]
--   [[AND CONCAT(u.first_name, ' ', u.last_name) = {{user_name}}]]
GROUP BY u.first_name, u.last_name
ORDER BY total_invoices DESC;
```


## Notes

- Only includes active invoices (deleted = FALSE)
- Results are ordered by invoice count (highest to lowest) to show most active users first


*Last updated: 2026-01-06*
