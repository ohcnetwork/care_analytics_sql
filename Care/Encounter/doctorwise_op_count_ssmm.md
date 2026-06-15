
# Doctor-wise OP Count - SSMM

> Per-doctor count of new vs. revisit OP consultations for yesterday, with a Total row

## Purpose

Daily operational report showing each doctor's OP load for the previous day, split into:

- **New** — first ever consultation between that patient and that doctor.
- **Revisit** — any subsequent consultation between the same patient and doctor.


## Parameters

*No parameters — the report is always for `CURRENT_DATE - INTERVAL '1 day'` (yesterday).*

---

## Query

```sql
WITH yesterday_visits AS (
    SELECT
        ci.patient_id,
        ci.performer_actor_id,
        TRIM(COALESCE(u.prefix || ' ', '') || u.first_name || ' ' || u.last_name) AS doctor_name,
        ts.start_datetime
    FROM emr_tokenbooking tb
    JOIN emr_tokenslot ts
      ON tb.token_slot_id = ts.id
    JOIN emr_chargeitem ci
      ON tb.charge_item_id = ci.id
    JOIN users_user u
      ON ci.performer_actor_id = u.id
    WHERE ci.deleted = FALSE
      AND ci.status IN ('paid', 'billed')
      AND ci.performer_actor_id != 336
      AND ci.service_resource = 'appointment'
      AND tb.status IN ('checked_in', 'in_consultation', 'fulfilled')
      AND ts.start_datetime >= CURRENT_DATE - INTERVAL '1 day'
      AND ts.start_datetime < CURRENT_DATE
),
yesterday_pairs AS (
    SELECT DISTINCT
        patient_id,
        performer_actor_id
    FROM yesterday_visits
),
first_visits AS (
    SELECT
        ci.patient_id,
        ci.performer_actor_id,
        MIN(ts.start_datetime) AS first_visit_datetime
    FROM emr_tokenbooking tb
    JOIN emr_tokenslot ts
      ON tb.token_slot_id = ts.id
    JOIN emr_chargeitem ci
      ON tb.charge_item_id = ci.id
    JOIN yesterday_pairs yp
      ON yp.patient_id = ci.patient_id
     AND yp.performer_actor_id = ci.performer_actor_id
    WHERE ci.deleted = FALSE
      AND ci.status IN ('paid', 'billed')
      AND ci.performer_actor_id != 336
      AND ci.service_resource = 'appointment'
      AND tb.status IN ('checked_in', 'in_consultation', 'fulfilled')
    GROUP BY ci.patient_id, ci.performer_actor_id
)

SELECT *
FROM (
    SELECT
        yv.doctor_name,
        COUNT(*) FILTER (WHERE yv.start_datetime = fv.first_visit_datetime) AS new,
        COUNT(*) FILTER (WHERE yv.start_datetime > fv.first_visit_datetime) AS revisit
    FROM yesterday_visits yv
    JOIN first_visits fv
      ON fv.patient_id = yv.patient_id
     AND fv.performer_actor_id = yv.performer_actor_id
    GROUP BY yv.performer_actor_id, yv.doctor_name

    UNION ALL

    SELECT
        'Total' AS doctor_name,
        COUNT(*) FILTER (WHERE yv.start_datetime = fv.first_visit_datetime) AS new,
        COUNT(*) FILTER (WHERE yv.start_datetime > fv.first_visit_datetime) AS revisit
    FROM yesterday_visits yv
    JOIN first_visits fv
      ON fv.patient_id = yv.patient_id
     AND fv.performer_actor_id = yv.performer_actor_id
) final_result
ORDER BY CASE WHEN doctor_name = 'Total' THEN 1 ELSE 0 END, doctor_name;
```


## Notes

- **Date filter** — only bookings whose **slot** `start_datetime` falls between `CURRENT_DATE - INTERVAL '1 day'` (inclusive) and `CURRENT_DATE` (exclusive) are counted.
- **Hardcoded values:**
  - `ci.performer_actor_id != 336` — excludes a specific user (casualty). Update or remove if that user changes.

*Last updated: 2026-05-25*



