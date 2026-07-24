
# Bed Availability Prediction

> 7-day forward forecast of bed occupancy and vacancies per floor/ward, with bottleneck flagging

## Purpose

Forecasts bed occupancy for each floor/ward over the next 7 days by combining current occupancy with historical (90-day) day-of-week admission and discharge patterns. Applies tunable multipliers to account for known surges or slowdowns, and flags any ward/day projected to cross an occupancy threshold as a `BOTTLENECK RISK`.

## Parameters

| Variable | Default | Meaning | When to change it |
|----------|---------|---------|--------------------|
| `admission_multiplier` | `1.0` | Scales expected admissions vs. the 90-day average. `1.0` = normal, `1.2` = expect 20% more admissions, `0.8` = expect 20% fewer | Festival/flu season surge → `1.2`–`1.5`. Holiday period with fewer elective admits → `0.7`–`0.9` |
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
        COUNT(DISTINCT fle.id) AS occupied_beds
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
patterns AS (
    SELECT
        floor,
        ward,
        dow,
        SUM(admit_count) / 13.0 AS avg_admits,
        SUM(discharge_count) / 13.0 AS avg_discharges
    FROM (
        -- Admissions by admission day-of-week
        SELECT
            COALESCE(gp_a.name, p_a.name) AS floor,
            p_a.name AS ward,
            EXTRACT(DOW FROM fle_a.start_datetime) AS dow,
            COUNT(*) AS admit_count,
            0 AS discharge_count
        FROM emr_facilitylocationencounter fle_a
        INNER JOIN emr_facilitylocation fl_a ON fle_a.location_id = fl_a.id
        LEFT JOIN emr_facilitylocation p_a ON fl_a.parent_id = p_a.id
        LEFT JOIN emr_facilitylocation gp_a ON p_a.parent_id = gp_a.id
        WHERE fl_a.deleted = FALSE AND fl_a.status = 'active'
          AND fl_a.form = 'bd' AND fle_a.deleted = FALSE
          AND fl_a.root_location_id != 300
          AND fle_a.start_datetime > NOW() - INTERVAL '90 days'
        GROUP BY 1, 2, 3
        
        UNION ALL
        
        -- Discharges by discharge day-of-week
        SELECT
            COALESCE(gp_d.name, p_d.name) AS floor,
            p_d.name AS ward,
            EXTRACT(DOW FROM fle_d.end_datetime) AS dow,
            0 AS admit_count,
            COUNT(*) AS discharge_count
        FROM emr_facilitylocationencounter fle_d
        INNER JOIN emr_facilitylocation fl_d ON fle_d.location_id = fl_d.id
        LEFT JOIN emr_facilitylocation p_d ON fl_d.parent_id = p_d.id
        LEFT JOIN emr_facilitylocation gp_d ON p_d.parent_id = gp_d.id
        WHERE fl_d.deleted = FALSE AND fl_d.status = 'active'
          AND fl_d.form = 'bd' AND fle_d.deleted = FALSE
          AND fl_d.root_location_id != 300
          AND fle_d.end_datetime > NOW() - INTERVAL '90 days'
          AND fle_d.end_datetime IS NOT NULL
        GROUP BY 1, 2, 3
    ) combined
    GROUP BY 1, 2, 3
),
days AS (
    SELECT generate_series(
        date_trunc('day', NOW()) + INTERVAL '1 day',
        date_trunc('day', NOW()) + INTERVAL '7 days',
        INTERVAL '1 day'
    ) AS forecast_day
),
forecast AS (
    SELECT
        c.floor,
        c.ward,
        c.total_beds,
        d.forecast_day,
        COALESCE(co.occupied_beds, 0) AS occupied_beds,
        SUM(
            COALESCE(pt.avg_admits, 0)     * {{admission_multiplier}}
          - COALESCE(pt.avg_discharges, 0) * {{turnover_multiplier}}
        ) OVER (PARTITION BY c.floor, c.ward ORDER BY d.forecast_day) AS cum_net_flow
    FROM capacity c
    CROSS JOIN days d
    LEFT JOIN current_occ co ON co.floor = c.floor AND co.ward = c.ward
    LEFT JOIN patterns pt
        ON pt.floor = c.floor AND pt.ward = c.ward
       AND pt.dow = EXTRACT(DOW FROM d.forecast_day)
)
SELECT
    floor,
    ward,
    forecast_day,
    total_beds,
    ROUND(LEAST(GREATEST(occupied_beds + cum_net_flow, 0), total_beds)) AS predicted_occupied,
    total_beds - ROUND(LEAST(GREATEST(occupied_beds + cum_net_flow, 0), total_beds)) AS predicted_vacancies,
    ROUND(100.0 * LEAST(GREATEST(occupied_beds + cum_net_flow, 0), total_beds) / total_beds, 1) AS predicted_occupancy_pct,
    CASE WHEN (occupied_beds + cum_net_flow) / total_beds::float >= {{bottleneck_threshold}}
         THEN 'BOTTLENECK RISK' ELSE 'OK' END AS status
FROM forecast
ORDER BY floor, ward, forecast_day;
```

## Notes

- **Tunable variables:** See the Parameters table above.
  - `admission_multiplier` and `turnover_multiplier` scale the historical daily averages to reflect expected surges/slowdowns.
  - `bottleneck_threshold` is compared against the *fraction* `(occupied_beds + cum_net_flow) / total_beds`, so it must be entered as a decimal fraction (e.g. `0.90` for 90%), not a whole number.
- Results are ordered by floor, then ward, then forecast day — giving a 7-day trend per ward.

*Last updated: 2026-07-24*
