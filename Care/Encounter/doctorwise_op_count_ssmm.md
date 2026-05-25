
# Doctor-wise OP Count - SSMM

> Per-doctor count of new vs. revisit OP consultations for yesterday, with a Total row

## Purpose

Daily operational report showing each doctor's OP load for the previous day, split into:

- **New** — first ever consultation between that patient and that doctor.
- **Revisit** — any subsequent consultation between the same patient and doctor.


## Parameters

*No parameters — the report is always for `CURRENT_DATE − 1 day` (yesterday).*

---

## Query

```sql
WITH visits_ordered AS (
    SELECT
        tb.id AS booking_id,
        ci.patient_id,
        TRIM(COALESCE(u.prefix || ' ', '') || u.first_name || ' ' || COALESCE(u.last_name, '')) AS doctor_name,
        ts.start_datetime,
        ROW_NUMBER() OVER (PARTITION BY ci.patient_id, ci.performer_actor_id ORDER BY ts.start_datetime) AS visit_num
    FROM emr_tokenbooking tb
    JOIN emr_tokenslot ts ON tb.token_slot_id = ts.id
    JOIN emr_chargeitem ci ON tb.charge_item_id = ci.id
    JOIN emr_chargeitemdefinition cd ON ci.charge_item_definition_id = cd.id
    JOIN users_user u ON ci.performer_actor_id = u.id
    WHERE ci.status IN ('paid', 'billed')
      AND ci.performer_actor_id != 336
      AND ci.service_resource = 'appointment'
      AND ci.performer_actor_id IS NOT NULL
      AND tb.status IN ('checked_in', 'in_consultation', 'fulfilled')
)

SELECT * FROM (
    SELECT
        doctor_name,
        COUNT(*) FILTER (WHERE visit_num = 1) AS new,
        COUNT(*) FILTER (WHERE visit_num > 1) AS revisit
    FROM visits_ordered
    WHERE start_datetime::date = CURRENT_DATE - INTERVAL '1 day'
    GROUP BY doctor_name
    
    UNION ALL
    
    SELECT
        'Total',
        COUNT(*) FILTER (WHERE visit_num = 1),
        COUNT(*) FILTER (WHERE visit_num > 1)
    FROM visits_ordered
    WHERE start_datetime::date = CURRENT_DATE - INTERVAL '1 day'
) AS final_result
ORDER BY CASE WHEN doctor_name = 'Total' THEN 1 ELSE 0 END, doctor_name;
```


## Notes

- **Date filter** — only bookings whose **slot** `start_datetime` falls on `CURRENT_DATE − 1` are counted.
- **Hardcoded values:**
  - `ci.performer_actor_id != 336` — excludes a specific user (casualty). Update or remove if that user changes.

*Last updated: 2026-05-25*


`````
