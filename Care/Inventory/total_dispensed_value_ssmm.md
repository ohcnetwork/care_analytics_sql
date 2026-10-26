# Total Dispensed Value - SSMM

> Cost value of medications dispensed in the current financial year up to a selected date

## Purpose

Calculates the total purchase (cost) value of medications dispensed between the start of the financial year (1 April 2026) and the selected date.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `selected_date` | date | **Required.** Upper bound (inclusive) for dispense `created_date` | `2026-09-30` |

---

## Query

```sql
SELECT
    CASE
        WHEN {{selected_date}} < DATE '2026-04-01' THEN NULL
        ELSE COALESCE(SUM(ep.purchase_price * emd.quantity), 0)
    END AS total_dispensed
FROM emr_medicationdispense emd
LEFT JOIN emr_dispenseorder edo ON edo.id = emd.order_id
JOIN emr_inventoryitem eii ON eii.id = emd.item_id
JOIN emr_product ep ON eii.product_id = ep.id
WHERE emd.status NOT IN ('cancelled', 'entered_in_error', 'stopped', 'declined')
  AND emd.deleted = FALSE
  AND edo.deleted = FALSE
  AND ep.purchase_price IS NOT NULL
  AND DATE(emd.created_date) >= DATE '2026-04-01'
  AND DATE(emd.created_date) <= {{selected_date}};
```

## Notes

- **Cost value, not sale value:** Each dispense is valued at `purchase_price × quantity`, so the total reflects stock cost rather than billed revenue.
- **Status filter:** Dispenses that are `cancelled`, `entered_in_error`, `stopped`, or `declined` are excluded; all other statuses (e.g. `preparation`, `in_progress`, `completed`) are counted.
- **All locations:** There is no location filter, so dispenses from every pharmacy/location are included.
- **Hardcoded financial year:** The start date `2026-04-01` is fixed in two places; update both when the financial year changes.
- **Before the financial year:** If `selected_date` is earlier than 1 April 2026, the result is `NULL`.
- **Required variable:** `selected_date` is not wrapped in optional `[[...]]` brackets, so the query needs a value to return a meaningful total.
- Output is a single row with one value.

*Last updated: 2026-10-13*
