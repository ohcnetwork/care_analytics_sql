# IP Patient Due Report - SSMM

> Accounts with balance linked to an inpatient encounter, with discharge time and tags

## Purpose

Lists every patient account that still has money due and is linked to an inpatient (`imp`) encounter. Each row shows the patient, SSMM ID, account and encounter status, first discharge time, billed/paid/due amounts, and account and patient tags. Useful for following up on unpaid inpatient bills, especially for patients already discharged.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `min_due` | number | Optional. Minimum account balance to include | `1000` |
| `ssmm_id` | text | Optional. Exact SSMM patient ID | `SSMM12345` |
| `encounter_status` | field filter | Optional. Mapped to `emr_encounter.status` | `discharged` |
| `encounter_date` | field filter | Optional. Mapped to `emr_encounter.created_date` | `Last 30 days` |

---

## Query

```sql
WITH acc_enc AS (
    SELECT
        c.account_id,
        COALESCE(c.encounter_id, a.primary_encounter_id) AS encounter_id
    FROM emr_chargeitem c
    JOIN emr_account a ON a.id = c.account_id
    WHERE c.status IN ('paid', 'billed')
    UNION
    SELECT id, primary_encounter_id
    FROM emr_account
    WHERE primary_encounter_id IS NOT NULL
),

first_discharged AS (
    SELECT DISTINCT ON (e.id)
        e.id AS encounter_id,
        (ds->>'moved_at')::timestamp + INTERVAL '5 hours 30 minutes' AS discharged_datetime
    FROM emr_encounter e
    CROSS JOIN LATERAL jsonb_array_elements(e.status_history->'history') AS ds
    WHERE e.encounter_class = 'imp'
      AND e.deleted = FALSE
      AND ds->>'status' = 'discharged'
    ORDER BY e.id, (ds->>'moved_at')::timestamp
)

SELECT *
FROM (
    SELECT DISTINCT ON (a.id)
        p.name AS patient_name,
        pi.value AS ssmm_id,
        a.id AS account_id,
        a.status AS account_status,
        a.billing_status,
        e.id AS encounter_id,
        e.encounter_class,
        e.status AS encounter_status,
        fd.discharged_datetime,
        CASE
            WHEN e.id = a.primary_encounter_id THEN 'primary encounter'
            ELSE 'from charge items'
        END AS encounter_source,
        e.created_date AS encounter_created_date,
        a.created_date AS account_created_date,
        ROUND(a.total_balance) AS account_due,
        ROUND(a.total_gross) AS account_billed_gross,
        ROUND(a.total_paid) AS account_paid,
        (SELECT STRING_AGG(tc.display, ', ') FROM emr_tagconfig tc
          WHERE tc.id = ANY(a.tags) AND NOT tc.deleted) AS account_tags,
        (SELECT STRING_AGG(tc.display, ', ') FROM emr_tagconfig tc
          WHERE tc.id = ANY(p.instance_tags) AND NOT tc.deleted) AS patient_tags
    FROM emr_account a
    JOIN emr_patient p ON p.id = a.patient_id
    LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 21
    JOIN acc_enc ae ON ae.account_id = a.id
    JOIN emr_encounter e ON e.id = ae.encounter_id
    LEFT JOIN first_discharged fd ON fd.encounter_id = e.id
    WHERE ROUND(a.total_balance) > 0
      AND e.encounter_class = 'imp'
    --   [[AND a.total_balance >= {{min_due}}]]
    --   [[AND pi.value = {{ssmm_id}}]]
    --   [[AND {{encounter_status}}]]
    --   [[AND {{encounter_date}}]]
    ORDER BY a.id, (e.id = a.primary_encounter_id) DESC, e.created_date DESC
) t
ORDER BY t.account_due DESC, t.account_id;
```

## Notes

- **Account-to-encounter links (`acc_enc`):** An account is linked to an encounter either through its paid/billed charge items (falling back to the account's primary encounter when the charge item has none) or directly through `primary_encounter_id`.
- **Amounts:** `account_due`, `account_billed_gross`, and `account_paid` are rounded to whole numbers.
- **SSMM ID:** Taken from `emr_patientidentifier` with `config_id = 21`; `ssmm_id` is an exact match.
 - **Field filters:** When enabling the optional filter clauses in Metabase, map `{{encounter_status}}` and `{{encounter_date}}` to `emr_encounter.status` and `emr_encounter.created_date`, respectively. Set their **Table and field alias** values to `e.status` and `e.created_date`.
- **Ordering:** Highest due amount first, then by account id.

*Last updated: 2026-10-29*
