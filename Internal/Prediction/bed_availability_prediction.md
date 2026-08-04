
# Bed Availability Prediction

> 7-day forward forecast of bed occupancy and vacancies per floor/ward, with bottleneck flagging

## Purpose

Forecasts bed occupancy for each floor/ward over the next 24 hours by combining current occupancy with historical (365-day) day-of-week admission and discharge patterns. Applies tunable multipliers to account for known surges or slowdowns, and flags any ward/day projected to cross an occupancy threshold as a `BOTTLENECK RISK`.

## Parameters

| Variable | Default | Meaning | When to change it |
|----------|---------|---------|--------------------|
| `admission_multiplier` | `1.0` | Scales expected admissions vs. the 365-day average. `1.0` = normal, `1.2` = expect 20% more admissions, `0.8` = expect 20% fewer | Festival/flu season surge → `1.2`–`1.5`. Holiday period with fewer elective admits → `0.7`–`0.9` |
| `turnover_multiplier` | `1.0` | Scales expected discharges. `1.0` = normal discharge pace, `1.2` = faster discharges, `0.8` = slower | Discharge drive/faster turnover initiative → `1.1`–`1.3`. Long weekend when doctors discharge fewer patients → `0.7`–`0.9` |
| `bottleneck_threshold` | `0.90` | Occupancy % (as a fraction) at which a ward gets flagged as `"BOTTLENECK RISK"` | ICU/critical wards may warrant `0.80` (flag earlier). General wards may tolerate `0.95` |

> **Note:** `bottleneck_threshold` is a **fraction**, so enter `0.90`, not `90`. If all three variables are set to `1`, the threshold is effectively `100%`, meaning nothing will flag until a ward is completely full — set it to `0.9` (or your desired fraction) instead.

---

## Query

```sql
WITH capacity AS (
    SELECT
        COALESCE(gp.name, p.name) AS floor,
        p.name AS ward,
        COUNT(*) AS total_beds
    FROM emr_facilitylocation fl
    LEFT JOIN emr_facilitylocation p ON fl.parent_id = p.id
    LEFT JOIN emr_facilitylocation gp ON p.parent_id = gp.id
    WHERE fl.deleted = FALSE AND fl.status = 'active'
      AND fl.form = 'bd' AND fl.root_location_id != 300
    GROUP BY 1, 2
),
current_occ AS (
    SELECT
        COALESCE(gp.name, p.name) AS floor,
        p.name AS ward,
        COUNT(DISTINCT fl.id) AS occupied_beds
    FROM emr_facilitylocationencounter fle
    INNER JOIN emr_facilitylocation fl ON fle.location_id = fl.id
    LEFT JOIN emr_facilitylocation p ON fl.parent_id = p.id
    LEFT JOIN emr_facilitylocation gp ON p.parent_id = gp.id
    WHERE fl.deleted = FALSE AND fl.status = 'active'
      AND fl.form = 'bd' AND fle.deleted = FALSE
      AND fl.root_location_id != 300
      AND fle.start_datetime <= NOW()
      AND (fle.end_datetime IS NULL OR fle.end_datetime > NOW())
    GROUP BY 1, 2
),
dow_occurrences AS (
    SELECT
        EXTRACT(DOW FROM d) AS dow,
        COUNT(*) AS occurrences
    FROM generate_series(
        date_trunc('day', NOW()) - INTERVAL '365 days',
        date_trunc('day', NOW()) - INTERVAL '1 day',
        INTERVAL '1 day'
    ) AS d
    GROUP BY 1
),
patterns AS (
    SELECT
        combined.floor,
        combined.ward,
        combined.dow,
        combined.hr,
        SUM(combined.admit_count)     / docc.occurrences::float AS avg_admits,
        SUM(combined.discharge_count) / docc.occurrences::float AS avg_discharges
    FROM (
        SELECT
            COALESCE(gp_a.name, p_a.name) AS floor,
            p_a.name AS ward,
            EXTRACT(DOW  FROM fle_a.start_datetime) AS dow,
            EXTRACT(HOUR FROM fle_a.start_datetime) AS hr,
            COUNT(*) AS admit_count,
            0 AS discharge_count
        FROM emr_facilitylocationencounter fle_a
        INNER JOIN emr_facilitylocation fl_a ON fle_a.location_id = fl_a.id
        LEFT JOIN emr_facilitylocation p_a ON fl_a.parent_id = p_a.id
        LEFT JOIN emr_facilitylocation gp_a ON p_a.parent_id = gp_a.id
        WHERE fl_a.deleted = FALSE AND fl_a.status = 'active'
          AND fl_a.form = 'bd' AND fle_a.deleted = FALSE
          AND fl_a.root_location_id != 300
          AND fle_a.start_datetime >= date_trunc('day', NOW()) - INTERVAL '365 days'
          AND fle_a.start_datetime <  date_trunc('day', NOW())
        GROUP BY 1, 2, 3, 4

        UNION ALL

        SELECT
            COALESCE(gp_d.name, p_d.name) AS floor,
            p_d.name AS ward,
            EXTRACT(DOW  FROM fle_d.end_datetime) AS dow,
            EXTRACT(HOUR FROM fle_d.end_datetime) AS hr,
            0 AS admit_count,
            COUNT(*) AS discharge_count
        FROM emr_facilitylocationencounter fle_d
        INNER JOIN emr_facilitylocation fl_d ON fle_d.location_id = fl_d.id
        LEFT JOIN emr_facilitylocation p_d ON fl_d.parent_id = p_d.id
        LEFT JOIN emr_facilitylocation gp_d ON p_d.parent_id = gp_d.id
        WHERE fl_d.deleted = FALSE AND fl_d.status = 'active'
          AND fl_d.form = 'bd' AND fle_d.deleted = FALSE
          AND fl_d.root_location_id != 300
          AND fle_d.end_datetime IS NOT NULL
          AND fle_d.end_datetime >= date_trunc('day', NOW()) - INTERVAL '365 days'
          AND fle_d.end_datetime <  date_trunc('day', NOW())
        GROUP BY 1, 2, 3, 4
    ) combined
    JOIN dow_occurrences docc ON docc.dow = combined.dow
    GROUP BY 1, 2, 3, 4, docc.occurrences
),

next24 AS (
    SELECT generate_series(
        date_trunc('hour', NOW()),
        date_trunc('hour', NOW()) + INTERVAL '23 hours',
        INTERVAL '1 hour'
    ) AS slot
),

net_flow_24h AS (
    SELECT
        c.floor,
        c.ward,
        SUM(
            COALESCE(pt.avg_admits, 0)     * {{admission_multiplier}}
          - COALESCE(pt.avg_discharges, 0) * {{turnover_multiplier}}
        ) AS net_flow
    FROM capacity c
    CROSS JOIN next24 n
    LEFT JOIN patterns pt
        ON pt.floor = c.floor AND pt.ward = c.ward
       AND pt.dow = EXTRACT(DOW  FROM n.slot)
       AND pt.hr  = EXTRACT(HOUR FROM n.slot)
    GROUP BY 1, 2
),
forecast_rounded AS (
    SELECT
        c.floor,
        c.ward,
        NOW() + INTERVAL '24 hours' AS prediction_for,
        c.total_beds,
        COALESCE(co.occupied_beds, 0) AS current_occupied,
        ROUND(LEAST(GREATEST(
            COALESCE(co.occupied_beds, 0) + COALESCE(nf.net_flow, 0), 0
        ), c.total_beds)::numeric) AS predicted_occupied
    FROM capacity c
    LEFT JOIN current_occ co ON co.floor = c.floor AND co.ward = c.ward
    LEFT JOIN net_flow_24h nf ON nf.floor = c.floor AND nf.ward = c.ward
)
SELECT
    floor,
    ward,
    prediction_for,
    total_beds,
    current_occupied,
    predicted_occupied,
    total_beds - predicted_occupied                               AS predicted_vacancies,
    ROUND((100.0 * predicted_occupied / total_beds)::numeric, 1) AS predicted_occupancy_pct,
    CASE WHEN predicted_occupied / total_beds::float >= {{bottleneck_threshold}}
         THEN 'BOTTLENECK RISK' ELSE 'OK' END                    AS status
FROM forecast_rounded
ORDER BY floor, ward;
```

## Notes

- **Tunable variables:** See the Parameters table above.
  - `admission_multiplier` and `turnover_multiplier` scale the historical daily averages to reflect expected surges/slowdowns.
  - `bottleneck_threshold` is compared against the *fraction* `(occupied_beds + cum_net_flow) / total_beds`, so it must be entered as a decimal fraction (e.g. `0.90` for 90%), not a whole number.
- Results are ordered by floor, then ward, then forecast day — giving a 7-day trend per ward.

*Last updated: 2026-07-24*
