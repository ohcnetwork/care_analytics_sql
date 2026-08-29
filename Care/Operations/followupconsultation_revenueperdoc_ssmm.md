# Follow-up Consultation Revenue Per Doctor

> Track follow-up consultations with patient visit count and revenue

## Purpose

This query identifies follow-up consultations (excluding first visits) for each patient, helping to measure patient retention and recurring revenue. It's useful for understanding which consultation services have strong patient follow-through and their revenue contribution from repeat visits.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE | Filters consultation charge item by creation date | `DATE = '2025-12-29'` |

---

## Query

```sql
WITH patient_consultation_order AS (
    SELECT
        emr_chargeitem.id,
        emr_chargeitem.patient_id,
        emr_chargeitem.title AS charge_item_name,
        emr_chargeitem.total_price,
        emr_chargeitem.created_date,
        ROW_NUMBER() OVER (
            PARTITION BY emr_chargeitem.patient_id, emr_chargeitem.title 
            ORDER BY emr_chargeitem.created_date
        ) AS consultation_order
    FROM emr_chargeitem
    WHERE emr_chargeitem.deleted = FALSE
        AND emr_chargeitem.title ILIKE 'consultation fee%'
        -- [[AND {{date}}]]
)

SELECT
    charge_item_name,
    COUNT(*) AS total_patients,
    SUM(total_price) AS total_revenue
FROM patient_consultation_order
WHERE consultation_order > 1
GROUP BY charge_item_name
ORDER BY total_revenue DESC;
```


## Notes

- Only includes active charge items (deleted = FALSE)
- Uses ROW_NUMBER() to identify consultation sequence per patient for each consultation type
- The consultation_order > 1 filter excludes first-time consultations, capturing only follow-ups
- Results are ordered by revenue (highest to lowest)
- total_patients represents the count of follow-up visits, not unique patients (same patient can have multiple follow-ups)

*Last updated: 2025-12-29*
