
# Doctor-wise OP Count - SSMM

> Per-doctor count of new vs. revisit OP consultations for yesterday, with a Total row

## Purpose

Daily operational report showing each doctor's OP load for the previous day, split into:

- **New** — first paid/billed consultation between that patient and that doctor.
- **Revisit** — any subsequent paid/billed consultation between the same patient and doctor.


## Parameters

*No parameters — the report is always for `CURRENT_DATE - INTERVAL '1 day'` (yesterday).*

---

## Query

```sql
WITH yesterday_visits AS (
    SELECT
        emr_chargeitem.patient_id,
        emr_chargeitem.performer_actor_id,
        TRIM(COALESCE(users_user.prefix || ' ', '') || users_user.first_name || ' ' || users_user.last_name) AS doctor_name,
        emr_tokenslot.start_datetime
    FROM emr_tokenbooking
    JOIN emr_tokenslot
      ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
    JOIN emr_chargeitem
      ON emr_tokenbooking.charge_item_id = emr_chargeitem.id
    JOIN users_user
      ON emr_chargeitem.performer_actor_id = users_user.id
    WHERE emr_chargeitem.deleted = FALSE
      AND emr_chargeitem.status IN ('paid', 'billed')
      AND emr_chargeitem.performer_actor_id != 336
      AND emr_chargeitem.service_resource = 'appointment'
      AND emr_tokenbooking.status IN ('checked_in', 'in_consultation', 'fulfilled')
      AND emr_tokenslot.start_datetime >= CURRENT_DATE - INTERVAL '1 day'
      AND emr_tokenslot.start_datetime < CURRENT_DATE
),
yesterday_pairs AS (
    SELECT DISTINCT
        patient_id,
        performer_actor_id
    FROM yesterday_visits
),
first_visits AS (
    SELECT
        emr_chargeitem.patient_id,
        emr_chargeitem.performer_actor_id,
        MIN(emr_tokenslot.start_datetime) AS first_visit_datetime
    FROM emr_tokenbooking
    JOIN emr_tokenslot
      ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
    JOIN emr_chargeitem
      ON emr_tokenbooking.charge_item_id = emr_chargeitem.id
    JOIN yesterday_pairs
      ON yesterday_pairs.patient_id = emr_chargeitem.patient_id
     AND yesterday_pairs.performer_actor_id = emr_chargeitem.performer_actor_id
    WHERE emr_chargeitem.deleted = FALSE
      AND emr_chargeitem.status IN ('paid', 'billed')
      AND emr_chargeitem.performer_actor_id != 336
      AND emr_chargeitem.service_resource = 'appointment'
      AND emr_tokenbooking.status IN ('checked_in', 'in_consultation', 'fulfilled')
    GROUP BY emr_chargeitem.patient_id, emr_chargeitem.performer_actor_id
)

SELECT
    performer_actor_id AS doctor_id,
    doctor_name,
    new,
    revisit
FROM (
    SELECT
        yesterday_visits.performer_actor_id,
        yesterday_visits.doctor_name,
        COUNT(*) FILTER (WHERE yesterday_visits.start_datetime = first_visits.first_visit_datetime) AS new,
        COUNT(*) FILTER (WHERE yesterday_visits.start_datetime > first_visits.first_visit_datetime) AS revisit
    FROM yesterday_visits
    JOIN first_visits
      ON first_visits.patient_id = yesterday_visits.patient_id
     AND first_visits.performer_actor_id = yesterday_visits.performer_actor_id
    GROUP BY yesterday_visits.performer_actor_id, yesterday_visits.doctor_name

    UNION ALL

    SELECT
        NULL AS performer_actor_id,
        'Total' AS doctor_name,
        COUNT(*) FILTER (WHERE yesterday_visits.start_datetime = first_visits.first_visit_datetime) AS new,
        COUNT(*) FILTER (WHERE yesterday_visits.start_datetime > first_visits.first_visit_datetime) AS revisit
    FROM yesterday_visits
    JOIN first_visits
      ON first_visits.patient_id = yesterday_visits.patient_id
     AND first_visits.performer_actor_id = yesterday_visits.performer_actor_id
) final_result
ORDER BY CASE WHEN doctor_name = 'Total' THEN 1 ELSE 0 END, doctor_name, performer_actor_id;
```


## Notes

- **Date filter** — only bookings whose **slot** `start_datetime` falls between `CURRENT_DATE - INTERVAL '1 day'` (inclusive) and `CURRENT_DATE` (exclusive) are counted.
- **Hardcoded values:**
  - `emr_chargeitem.performer_actor_id != 336` — excludes a specific user (casualty). Update or remove if that user changes.

*Last updated: 2026-05-25*



