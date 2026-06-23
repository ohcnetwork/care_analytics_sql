# First Consultation Revenue Per Doctor

> Track first-time consultations with patient count and revenue

## Purpose

This query identifies first-time consultations for each patient helping to measure new patient acquisition and initial consultation revenue. It's useful for understanding which consultation services are attracting new patients and their revenue contribution.

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
    COUNT(DISTINCT patient_id) AS total_patients,
    SUM(total_price) AS total_revenue
FROM patient_consultation_order
WHERE consultation_order = 1
GROUP BY charge_item_name
ORDER BY total_revenue DESC;
```


## Notes

- Only includes active charge items (deleted = FALSE)
- Uses ROW_NUMBER() to identify first consultation per patient for each consultation type
- Results are ordered by revenue (highest to lowest)
- Patients are counted distinctly to avoid duplication
- The consultation_order = 1 filter ensures only first-time consultations are included

*Last updated: 2025-12-29*
