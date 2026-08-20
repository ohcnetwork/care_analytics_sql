
# Patients With Medication Due

> Count of patients whose latest 15-day medication course is overdue for renewal

## Purpose

Counts patients whose most recent medication request with a 15-day duration has already passed its due date. Useful for identifying how many patients may now be due for medication review, refill, or follow-up.

---

## Query

```sql
WITH latest_15_day_per_patient AS (
		SELECT DISTINCT ON (emr_medicationrequest.patient_id)
				emr_medicationrequest.patient_id,
				emr_medicationrequest.authored_on::date AS last_prescribed_on
		FROM emr_medicationrequest
		WHERE  emr_medicationrequest.status != 'entered_in_error'
			AND EXISTS (
					SELECT 1
					FROM jsonb_array_elements(emr_medicationrequest.dosage_instruction) AS dosage_element
					WHERE dosage_element->'timing'->'repeat'->'bounds_duration'->>'unit' = 'd'
						AND (dosage_element->'timing'->'repeat'->'bounds_duration'->>'value')::int = 15
			)
		ORDER BY emr_medicationrequest.patient_id, emr_medicationrequest.authored_on DESC
)
SELECT COUNT(*) AS due_patient_count
FROM latest_15_day_per_patient
WHERE CURRENT_DATE > (latest_15_day_per_patient.last_prescribed_on + INTERVAL '15 days')::date;
```

## Notes

- **Overdue rule:** A patient is counted when `CURRENT_DATE` is strictly greater than `last_prescribed_on + 15 days`, meaning the full 15-day course has elapsed.
- **Hardcoded duration filter:** This query only considers medication requests with a 15-day duration. If you need 7-day, 30-day, or mixed-duration tracking, adjust the JSONB filter logic.
- **No Metabase filters:** This query currently has no Metabase variables and always evaluates against `CURRENT_DATE` at runtime.

*Last updated: 2026-08-11*
