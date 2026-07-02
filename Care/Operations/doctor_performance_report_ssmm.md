
# Doctor Performance Report - SSMM

> Per-doctor / category / issue-date charge item summary with quantity, gross price, and net amount

## Purpose

Summarises billed / paid charge items at SSMM grouped by resource category, invoice issue date, and the performer (doctor). For each group it reports the total quantity, total gross price, and a net `amount` calculated as `total_price + discount − CGST − SGST - IGST` 

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
    + COALESCE(price_components.discount_amount, 0)
    - COALESCE(price_components.cgst_amount, 0)
    - COALESCE(price_components.sgst_amount, 0)
    - COALESCE(price_components.igst_amount, 0)
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
    SELECT 
        SUM(CASE WHEN elem ->> 'monetary_component_type' = 'discount' 
            THEN (elem ->> 'amount')::numeric ELSE 0 END) AS discount_amount,
        SUM(CASE WHEN elem ->> 'monetary_component_type' = 'tax' 
            AND elem -> 'code' ->> 'code' = 'cgst' 
            THEN (elem ->> 'amount')::numeric ELSE 0 END) AS cgst_amount,
        SUM(CASE WHEN elem ->> 'monetary_component_type' = 'tax' 
            AND elem -> 'code' ->> 'code' = 'sgst' 
            THEN (elem ->> 'amount')::numeric ELSE 0 END) AS sgst_amount,
        SUM(CASE WHEN elem ->> 'monetary_component_type' = 'tax' 
            AND elem -> 'code' ->> 'code' = 'igst' 
            THEN (elem ->> 'amount')::numeric ELSE 0 END) AS igst_amount
    FROM jsonb_array_elements(emr_chargeitem.total_price_components) AS elem
) price_components ON TRUE
WHERE emr_chargeitem.deleted = FALSE
  AND emr_chargeitem.status IN ('paid','billed')
  AND emr_invoice.status IN ('issued','balanced')
  --[[AND emr_invoice.issue_date >= {{start_date}} + INTERVAL '5 hours 30 minutes']]
  --[[AND emr_invoice.issue_date < {{end_date}} + INTERVAL '1 day' + INTERVAL '5 hours 30 minutes']]
  --[[AND TRIM(COALESCE(u.prefix || ' ', '') || u.first_name || ' ' || u.last_name) = {{doctor}}]]
  --[[AND emr_resourcecategory.title IN ({{category}})]]
GROUP BY 
    emr_resourcecategory.title,
    emr_invoice.issue_date,
    TRIM(COALESCE(u.prefix || ' ', '') || u.first_name || ' ' || u.last_name)
ORDER BY total_price DESC;
```

## Notes

- **`amount` formula:** `total_price + discount − CGST − SGST - IGST`. The discount is *added back* (it is stored as a negative-style component), and the CGST/SGST tax portions are subtracted to isolate the net revenue contribution.
- Results are ordered by `total_price DESC` so the highest-revenue groups surface first.

*Last updated: 2026-06-29*
