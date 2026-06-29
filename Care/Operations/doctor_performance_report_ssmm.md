
# Doctor Performance Report - SSMM

> Per-doctor / category / issue-date charge item summary with quantity, gross price, and net amount

## Purpose

Summarises billed / paid charge items at SSMM grouped by resource category, invoice issue date (in IST), and the performer (doctor). For each group it reports the total quantity, total gross price, and a net `amount` calculated as `total_price + discount − CGST − SGST` 

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `start_date` | DATE | Inclusive lower bound on the IST-adjusted invoice issue date | `'2026-06-01'` |
| `end_date` | DATE | Inclusive upper bound on the IST-adjusted invoice issue date (filter is `< end_date + 1 day`) | `'2026-06-30'` |
| `doctor` | TEXT | Filter by full doctor name (exact match on `prefix + first_name + last_name`) | `'Dr. John Doe'` |
| `category` | TEXT (multi) | Filter by one or more resource category titles | `'Consultation', 'Procedure'` |

---

## Query

```sql
SELECT
    emr_resourcecategory.title AS category,
    emr_invoice.issue_date - INTERVAL '5 hours 30 minutes' AS issue_date,
    TRIM(COALESCE(u.prefix || ' ', '') || u.first_name || ' ' || u.last_name) AS requested,
    SUM(emr_chargeitem.quantity) AS total_quantity,
    SUM(emr_chargeitem.total_price) AS total_price,
    SUM(
        emr_chargeitem.total_price
      + COALESCE(discount_component.amount, 0)
      - COALESCE(cgst_component.amount, 0)
      - COALESCE(sgst_component.amount, 0)
    ) AS amount
FROM emr_chargeitem
JOIN emr_chargeitemdefinition
    ON emr_chargeitem.charge_item_definition_id = emr_chargeitemdefinition.id
JOIN emr_resourcecategory
    ON emr_chargeitemdefinition.category_id = emr_resourcecategory.id
LEFT JOIN users_user u
    ON emr_chargeitem.performer_actor_id = u.id
JOIN emr_invoice
    ON emr_chargeitem.paid_invoice_id = emr_invoice.id
LEFT JOIN LATERAL (
    SELECT (elem ->> 'amount')::numeric AS amount
    FROM jsonb_array_elements(emr_chargeitem.total_price_components) AS elem
    WHERE elem ->> 'monetary_component_type' = 'discount'
    LIMIT 1
) discount_component ON TRUE
LEFT JOIN LATERAL (
    SELECT (elem ->> 'amount')::numeric AS amount
    FROM jsonb_array_elements(emr_chargeitem.total_price_components) AS elem
    WHERE elem ->> 'monetary_component_type' = 'tax'
      AND elem -> 'code' ->> 'code' = 'cgst'
    LIMIT 1
) cgst_component ON TRUE
LEFT JOIN LATERAL (
    SELECT (elem ->> 'amount')::numeric AS amount
    FROM jsonb_array_elements(emr_chargeitem.total_price_components) AS elem
    WHERE elem ->> 'monetary_component_type' = 'tax'
      AND elem -> 'code' ->> 'code' = 'sgst'
    LIMIT 1
) sgst_component ON TRUE
WHERE emr_chargeitem.status IN ('paid','billed')
  AND emr_invoice.status IN ('issued','balanced')
  --[[AND (emr_invoice.issue_date - INTERVAL '5 hours 30 minutes') >= {{start_date}}]]
  --[[AND (emr_invoice.issue_date - INTERVAL '5 hours 30 minutes') <  {{end_date}} + INTERVAL '1 day']]
  --[[AND TRIM(COALESCE(u.prefix || ' ', '') || u.first_name || ' ' || u.last_name) = {{doctor}}]]
  --[[AND emr_resourcecategory.title IN ({{category}})]]
GROUP BY
    emr_resourcecategory.title,
    emr_invoice.issue_date - INTERVAL '5 hours 30 minutes',
    TRIM(COALESCE(u.prefix || ' ', '') || u.first_name || ' ' || u.last_name)
ORDER BY total_price DESC;
```

## Notes

- **IST conversion:** `emr_invoice.issue_date - INTERVAL '5 hours 30 minutes'` shifts the stored UTC timestamp into IST so the report groups and filters align with the local business day.
- **`amount` formula:** `total_price + discount − CGST − SGST`. The discount is *added back* (it is stored as a negative-style component), and the CGST/SGST tax portions are subtracted to isolate the net revenue contribution.
- Results are ordered by `total_price DESC` so the highest-revenue groups surface first.

*Last updated: 2026-06-29*
