# Total Medication Return Value - SSMM

> Cost value of medications returned by patients in the current financial year up to a selected date

## Purpose

Calculates the total purchase (cost) value of medications returned by patients between the start of the financial year (1 April 2026) and the selected date. 

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `selected_date` | date | **Required.** Upper bound (inclusive) for delivery `created_date` | `2026-09-30` |

---

## Query

```sql
SELECT
    CASE
        WHEN {{selected_date}} < DATE '2026-04-01' THEN NULL
        ELSE COALESCE(SUM(ep.purchase_price * esd.supplied_item_quantity), 0)
    END AS total_return
FROM emr_supplydelivery esd
JOIN emr_deliveryorder edo ON esd.order_id = edo.id
JOIN emr_product ep ON esd.supplied_item_id = ep.id
WHERE esd.status = 'completed'
  AND edo.patient_id IS NOT NULL
  AND esd.deleted = FALSE
  AND edo.deleted = FALSE
  AND ep.purchase_price IS NOT NULL
  AND DATE(esd.created_date) >= DATE '2026-04-01'
  AND DATE(esd.created_date) <= {{selected_date}};
```

## Notes

- **Patient returns:** A delivery is treated as a medication return when its delivery order has a `patient_id`.
- **Cost value, not refund value:** Each return is valued at `purchase_price × supplied_item_quantity`, so the total reflects stock cost rather than the amount refunded to the patient.
- **All locations:** There is no location filter, so returns into every location are included.
- **Hardcoded financial year:** The start date `2026-04-01` is fixed in two places; update both when the financial year changes.
- **Before the financial year:** If `selected_date` is earlier than 1 April 2026, the result is `NULL`.
- **Required variable:** `selected_date` is not wrapped in optional `[[...]]` brackets, so the query needs a value to return a meaningful total.
- Output is a single row with one value.

*Last updated: 2026-10-13*
