# Active Invoices 

> Detailed view of active invoices with patient zone, invoice status breakdown, and charge item details

## Purpose

This query provides a comprehensive overview of active patient accounts and their associated invoices, including invoice status distribution (draft, balanced, issued), financial metrics, and charge item details. It's useful for monitoring outstanding invoices, tracking payment status, and analyzing billing patterns across different zones.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE | Filters invoices by modification date | `'2025-12-29'` |
| `zone_filter` | TEXT | Filters by patient zone | `'Zone A'` |
| `staff_name` | TEXT | Filters by staff member who updated the invoice | `'John'` |

---

## Query

```sql
WITH patient_tags AS (
    SELECT
        p.id AS patient_id,
        STRING_AGG(CASE WHEN et.parent_id = 55 THEN et.display END, ', ') AS zone
    FROM emr_patient p
    LEFT JOIN LATERAL unnest(p.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig et ON et.id = tag_id
        AND et.deleted = FALSE
        AND et.parent_id = 55
    GROUP BY p.id
)

SELECT
    acc.name AS account_name,
    p.meta -> 'identifiers' -> 0 ->> 'value' AS adm_number,  
    pt.zone,
    COUNT(inv.id) AS number_of_invoices,
    SUM(CASE WHEN inv.status = 'draft' THEN 1 ELSE 0 END) AS draft_count,
    SUM(CASE WHEN inv.status = 'balanced' THEN 1 ELSE 0 END) AS balanced_count,
    SUM(CASE WHEN inv.status = 'issued' THEN 1 ELSE 0 END) AS issued_count,
    acc.total_balance AS total_due,
    acc.total_paid AS total_paid,
    acc.total_gross AS billed_gross,
    inv.modified_date,
    inv.number::text AS invoice_numbers,
    u.first_name AS staff_name,
    SUM(inv.total_net) AS invoice_amount_due,
    cic.charge_items_names AS all_charge_item_names 

FROM emr_account acc
LEFT JOIN emr_patient p ON p.id = acc.patient_id 
LEFT JOIN emr_invoice inv ON inv.account_id = acc.id
LEFT JOIN users_user u ON u.id = inv.updated_by_id

-- Unnest each invoice's charge items array and get charge item names
LEFT JOIN LATERAL (
    SELECT STRING_AGG(cid.title, ', ') AS charge_items_names
    FROM unnest(inv.charge_items) AS chargeitem_id
    JOIN emr_chargeitem ci ON ci.id = chargeitem_id
    JOIN emr_chargeitemdefinition cid ON ci.charge_item_definition_id = cid.id
) cic ON TRUE

LEFT JOIN patient_tags pt ON pt.patient_id = acc.patient_id

WHERE
    acc.status = 'active'
    AND acc.facility_id = 2
    -- [[AND {{date}}]]
    -- [[AND (pt.zone) = ({{zone_filter}})]]
    -- [[AND {{staff_name}}]]

GROUP BY
    acc.id,
    acc.name,
    acc.total_balance,
    acc.total_paid,
    acc.total_gross,
    pt.zone,
    u.first_name,
    inv.modified_date,
    p.meta,
    inv.number,
    cic.charge_items_names

ORDER BY acc.name;
```

## Notes

- Query is filtered to `facility_id = 2` - update this value as needed
- Only includes active accounts (status = 'active')
- Patient zones are extracted from tags with parent_id = 55
- Uses LATERAL joins to unnest JSONB arrays for tags and charge items


*Last updated: 2025-12-29*
