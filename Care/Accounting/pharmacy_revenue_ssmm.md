
# Pharmacy Revenue - SSMM

> Total revenue from pharmacy

## Purpose

Returns the total pharmacy revenue at SSMM by summing `total_price` of charge items that are linked to a medication dispense and a settled invoice.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `DATE` | DATE | Filter by date range (typically applied to `inv.created_date` or `md.created_date`) | `inv.created_date BETWEEN '2026-04-01' AND '2026-04-30'` |

---

## Query

```sql
SELECT 
    SUM(ci.total_price) AS total_pharmacy_revenue
FROM emr_medicationdispense md
JOIN emr_chargeitem ci ON md.charge_item_id = ci.id
JOIN emr_invoice inv ON ci.paid_invoice_id = inv.id
WHERE md.status NOT IN ('entered_in_error', 'cancelled', 'declined')
  AND ci.status IN ('paid', 'billed')
  AND inv.status IN ('issued', 'balanced')
  --[[AND {{DATE}}]]
;
```


## Notes

- **Status filters** keep only valid revenue:
  - `md.status NOT IN ('entered_in_error', 'cancelled', 'declined')` — exclude these dispenses.
  - `ci.status IN ('paid', 'billed')` — only charge items that have been billed or paid.
  - `inv.status IN ('issued', 'balanced')` — only invoices that have been issued or fully balanced.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards

*Last updated: 2026-05-04*

````
