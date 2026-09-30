# Invoices with Duplicate Discounts on Charge Items - SSMM

> Invoices containing at least one charge item with more than one discount component applied

## Purpose

Lists invoices where any linked charge item has two or more `discount` entries in its unit price components, along with a direct link to the invoice in CARE.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| *(none)* | - | Query runs as a static report with fixed filters | - |

---

## Query

```sql
SELECT DISTINCT
    i.number AS invoice_number,
    'https://care-public.ssmmhospital.com/facility/9bef54be-70b1-4210-adb5-37a0183ee5f9/billing/invoices/'
        || i.external_id::text AS invoice_link,
    i.created_date AS invoice_date
FROM emr_invoice i
WHERE i.deleted = FALSE
  AND EXISTS (
      SELECT 1
      FROM emr_chargeitem eci
      CROSS JOIN LATERAL jsonb_array_elements(eci.unit_price_components::jsonb) AS comp
      WHERE eci.paid_invoice_id = i.id
        AND eci.deleted = FALSE
        AND comp ->> 'monetary_component_type' = 'discount'
      GROUP BY eci.id
      HAVING COUNT(*) > 1
  )
ORDER BY invoice_date DESC;
```

## Notes
- Results are sorted by most recent invoice first.

*Last updated: 2026-09-30*
