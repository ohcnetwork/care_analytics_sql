
# Lab Service Requests by Category (External Vendors) - SSMM

> Monthly count of lab service requests grouped by external vendor category and status

## Purpose

Returns the monthly count of lab `emr_servicerequest` records at SSMM, grouped by external vendor resource category and request status. Each row shows the month, vendor category, status, and the number of requests.


## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `service_request_status` | TEXT | Filter by service request status | `'completed'` |
| `category` | TEXT | Filter by resource category title (exact match on `emr_resourcecategory.title`) | `'External Lab - Vendor A'` |
| `date` | DATE / range | Metabase date filter (bound to `sr.created_date`) | `'2026-06-01'` |

---

## Query

```sql
SELECT
    TO_CHAR(DATE_TRUNC('month', sr.created_date), 'YYYY-MM') AS month,
    rc.title AS category,
    sr.status,
    COUNT(sr.id) AS total_requests
FROM emr_servicerequest sr
JOIN emr_activitydefinition ad
    ON ad.id = sr.activity_definition_id
CROSS JOIN LATERAL unnest(ad.charge_item_definitions) AS cid_id
JOIN emr_chargeitemdefinition cid
    ON cid.id = cid_id
JOIN emr_resourcecategory rc
    ON rc.id = cid.category_id
WHERE sr.category = 'laboratory'
  AND rc.id IN (49, 50, 51, 52)
  --[[AND sr.status = {{service_request_status}}]]
  --[[AND rc.title = {{category}}]]
  --[[AND {{date}}]]
GROUP BY month, rc.title, sr.status
ORDER BY month DESC, rc.title, sr.status;
```

## Notes

- `rc.id IN (49, 50, 51, 52)` is hardcoded — these correspond to the SSMM external lab vendor resource categories. Update this list if category IDs change or new vendors are added.
- Months are formatted as `YYYY-MM` for easy grouping and sorting; results are ordered with the most recent month first.

*Last updated: 2026-06-19*
