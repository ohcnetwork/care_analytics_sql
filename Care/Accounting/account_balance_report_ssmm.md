
# Account Balance Report - SSMM

> Per-account outstanding balance with patient, encounter, and tags

## Purpose

Returns the current balance for each patient account at SSMM along with the SSMM patient ID, patient name, primary encounter class, billing/account status, and aggregated tag labels for both the account and the patient.


## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `encounter_class` | TEXT | Filter by primary encounter class (exact match on `emr_encounter.encounter_class`) | `'IMP'` |
| `ssmm_id` | TEXT | Filter by patient SSMM ID (exact match on `emr_patientidentifier.value`) | `'SSMM-1023'` |

---

## Query

```sql
WITH account_tag_agg AS (
    SELECT
        a.id AS account_id,
        STRING_AGG(DISTINCT tc.display, ', ') AS account_tags
    FROM emr_account a
    LEFT JOIN LATERAL unnest(a.tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig tc
      ON tc.id = tag_id
     AND tc.deleted = FALSE
    GROUP BY a.id
),
patient_tag_agg AS (
    SELECT
        p.id AS patient_id,
        STRING_AGG(DISTINCT tc.display, ', ') AS patient_tags
    FROM emr_patient p
    LEFT JOIN LATERAL unnest(p.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig tc
      ON tc.id = tag_id
     AND tc.deleted = FALSE
    GROUP BY p.id
)
SELECT
    pi.value AS ssmm_id,
    p.name AS patient_name,
    e.encounter_class,
    a.total_balance,
    a.billing_status,
    a.status,
    ata.account_tags,
    pta.patient_tags
FROM emr_account a
JOIN emr_patient p
  ON a.patient_id = p.id
LEFT JOIN emr_patientidentifier pi
  ON p.id = pi.patient_id
 AND pi.config_id = 21
JOIN emr_encounter e
  ON a.primary_encounter_id = e.id
LEFT JOIN account_tag_agg ata
  ON a.id = ata.account_id
LEFT JOIN patient_tag_agg pta
  ON p.id = pta.patient_id
WHERE 1=1
  --[[AND e.encounter_class = {{encounter_class}}]]
  --[[AND pi.value = {{ssmm_id}}]]
ORDER BY total_balance DESC;
```

## Notes

- `pi.config_id = 21` is hardcoded for the SSMM patient identifier configuration — update if the config id changes.
- The join on `emr_encounter` uses `a.primary_encounter_id`, so the report only includes accounts that have a primary encounter set. 
- Results are ordered by `total_balance` descending so the largest outstanding balances appear first.

*Last updated: 2026-06-19*
