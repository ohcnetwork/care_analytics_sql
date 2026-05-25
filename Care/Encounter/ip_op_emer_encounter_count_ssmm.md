
# IP / OP / Emergency Encounter Count - SSMM

> Daily counts of occupied inpatient beds, ambulatory (OP) encounters and emergency encounters for the current month-to-date (up to yesterday)

## Purpose

Operational dashboard query giving a one-row-per-day view of patient volume at SSMM for the current month:

- **IP load** — number of beds occupied that day (one per patient, latest assignment).
- **OP load** — distinct ambulatory (`amb`) encounters created that day.
- **Emergency load** — distinct emergency (`emer`) encounters created that day.


## Parameters

*No parameters — the window is always `month-to-date − 1 day`.*

---

## Query

```sql
WITH dates AS (
    SELECT generate_series(
        DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 day'),
        CURRENT_DATE - INTERVAL '1 day',
        '1 day'::interval
    )::date AS report_date
),

daily_occupied_beds AS (
    SELECT
        d.report_date AS bed_date,
        COUNT(DISTINCT bed_id) AS occupied_bed_count
    FROM dates d
    CROSS JOIN LATERAL (
        SELECT DISTINCT ON (e.patient_id)
            fl.id AS bed_id
        FROM emr_facilitylocationencounter fle
        INNER JOIN emr_facilitylocation fl ON fle.location_id = fl.id
        INNER JOIN emr_encounter e ON fle.encounter_id = e.id
        WHERE fl.deleted = FALSE
          AND fl.status = 'active'
          AND fl.form = 'bd'
          AND fl.root_location_id != 300
          AND fl.parent_id NOT IN (19, 44)
          AND fle.deleted = FALSE
          AND fle.start_datetime::date <= d.report_date
          AND (fle.end_datetime IS NULL OR fle.end_datetime::date > d.report_date)
        ORDER BY e.patient_id, fle.start_datetime DESC
    ) occupied
    GROUP BY d.report_date
),

encounters AS (
    SELECT
        created_date::date AS encounter_date,
        COUNT(DISTINCT patient_id) FILTER (WHERE encounter_class = 'amb') AS ambulatory_count,
        COUNT(DISTINCT patient_id) FILTER (WHERE encounter_class = 'emer') AS emergency_count
    FROM emr_encounter
    WHERE deleted = FALSE
      AND created_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 day')
      AND created_date::date <= CURRENT_DATE - INTERVAL '1 day'
    GROUP BY created_date::date
)

SELECT
    d.report_date AS encounter_date,
    TO_CHAR(d.report_date, 'DD, Dy') AS date_label,
    COALESCE(dob.occupied_bed_count, 0) AS occupied_bed_count,
    COALESCE(e.ambulatory_count, 0) AS ambulatory_count,
    COALESCE(e.emergency_count, 0) AS emergency_count
FROM dates d
LEFT JOIN daily_occupied_beds dob ON d.report_date = dob.bed_date
LEFT JOIN encounters e ON d.report_date = e.encounter_date
ORDER BY d.report_date;
```

## Notes

- **Date window** — `dates` CTE generates one row per day from the **start of the current month** through **yesterday** (`CURRENT_DATE - INTERVAL '1 day'`). Today is intentionally excluded so the report only shows completed days.
- **Hardcoded values:**
  - `fl.root_location_id != 300` — excludes the fake beds root. Update if the fake-beds root ID changes.
  - `fl.parent_id NOT IN (19, 44)` — excludes specific parent locations. Update if the excluded wards change.
  - `fl.form = 'bd'` and `fl.status = 'active'` — only currently active bed-type locations count.

*Last updated: 2026-05-25*


`````
