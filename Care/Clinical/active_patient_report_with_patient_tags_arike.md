
# Active Patient Report with Patient Tags 

> Currently active patients at Arike with zone / place-of-care tags with the most relevant encounter or upcoming appointment date

## Purpose

Identifies the set of **currently active patients** at Arike and their zone and place-of-care , plus a single `date` column that reflects either their most recent encounter (within the last 100 days) or their earliest upcoming appointment (within the next 100 days).

An "active patient" is defined as one who:

- is **not deceased**, and
- does **not** carry the exclusion tag (`tag_id = 70`), and
- either has an encounter at facility 2 in the last 100 days, **or** has an upcoming booked / checked-in / in-consultation appointment at facility 2 in the next 100 days.



## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `zone_filter` | TEXT | Filter by resolved zone tag display (exact match) | `'Zone A'` |
| `place_of_care` | TEXT | Filter by resolved place-of-care tag display (exact match) | `'Home'` |

---

## Query

```sql
WITH active_patients AS (
    SELECT DISTINCT
        ep.id AS patient_id,
        ep.name AS patient_name,
        ep.gender,
        ep.phone_number,
        pi.value AS adm,
        ep.instance_tags
    FROM emr_patient ep
    LEFT JOIN emr_patientidentifier pi
        ON ep.id = pi.patient_id
       AND pi.config_id = 2
    WHERE ep.deceased_datetime IS NULL
      AND NOT (70 = ANY(ep.instance_tags))
      AND (
          EXISTS (
              SELECT 1
              FROM emr_encounter ee
              WHERE ee.patient_id   = ep.id
                AND ee.created_date >= CURRENT_DATE - INTERVAL '100 days'
                AND ee.facility_id  = 2
                AND ee.deleted      = FALSE
          )
          OR
          EXISTS (
              SELECT 1
              FROM emr_tokenbooking tb
              JOIN emr_tokenslot ts
                  ON tb.token_slot_id = ts.id
              JOIN emr_schedulableresource sbr
                  ON ts.resource_id = sbr.id
              WHERE tb.patient_id      = ep.id
                AND ts.start_datetime >= CURRENT_DATE
                AND ts.start_datetime  < CURRENT_DATE + INTERVAL '100 days'
                AND sbr.facility_id    = 2
                AND tb.deleted         = FALSE
                AND ts.deleted         = FALSE
                AND tb.status IN ('booked', 'checked_in', 'in_consultation')
          )
      )
),
patient_tags AS (
    SELECT
        ap.patient_id,
        COALESCE(MAX(CASE WHEN et.parent_id = 55 THEN et.display END), 'unassigned') AS zone,
        COALESCE(MAX(CASE WHEN et.parent_id = 71 THEN et.display END), 'unassigned') AS place_of_care
    FROM active_patients ap
    LEFT JOIN LATERAL unnest(ap.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig et
        ON et.id = tag_id
       AND et.deleted = FALSE
    GROUP BY ap.patient_id
)
SELECT
    ap.patient_name,
    ap.phone_number,
    ap.adm,
    ap.gender,
    pt.zone,
    pt.place_of_care,
    COALESCE(
        (SELECT MAX(ee.created_date)
         FROM emr_encounter ee
         WHERE ee.patient_id   = ap.patient_id
           AND ee.created_date >= CURRENT_DATE - INTERVAL '100 days'
           AND ee.facility_id  = 2),
        (SELECT MIN(ts.start_datetime)
         FROM emr_tokenbooking tb
         JOIN emr_tokenslot ts
             ON tb.token_slot_id = ts.id
         JOIN emr_schedulableresource sbr
             ON ts.resource_id = sbr.id
         WHERE tb.patient_id      = ap.patient_id
           AND ts.start_datetime >= CURRENT_DATE
           AND ts.start_datetime  < CURRENT_DATE + INTERVAL '100 days'
           AND sbr.facility_id    = 2
           AND tb.deleted         = FALSE
           AND ts.deleted         = FALSE
           AND tb.status IN ('booked', 'checked_in', 'in_consultation'))
    ) AS date
FROM active_patients ap
LEFT JOIN patient_tags pt
    ON pt.patient_id = ap.patient_id
WHERE 1=1
    --[[AND pt.zone = {{zone_filter}}]]
    --[[AND pt.place_of_care = {{place_of_care}}]]
ORDER BY ap.patient_name;
```

## Notes

- **Active-patient definition:** Encoded in the `active_patients` CTE — not deceased, not carrying tag `70`, and either has a recent encounter (last 100 days) **or** an upcoming appointment (next 100 days) at `facility_id = 2` (Arike).
- **Hardcoded IDs:**
  - `facility_id = 2` — Arike facility.
  - `pi.config_id = 2` — ADM patient identifier configuration.
  - `70` — exclusion instance tag (patients carrying this tag are omitted).
  - `parent_id = 55` — parent tag for **zone**.
  - `parent_id = 71` — parent tag for **place of care**.
  Update any of these if the underlying configuration changes.
- **Metabase filters:**
  - `[[AND pt.zone = {{zone_filter}}]]` and `[[AND pt.place_of_care = {{place_of_care}}]]` — exact-match filters applied on the resolved tag columns.
- Results are ordered alphabetically by patient name.

*Last updated: 2026-07-07*
