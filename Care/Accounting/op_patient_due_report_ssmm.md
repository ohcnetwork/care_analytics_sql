# OP Patient Due Report - SSMM

> Accounts with balance linked to a non-inpatient encounter, with tags

## Purpose

Lists every patient account that still has money due and is linked to a non-inpatient encounter (outpatient, emergency, etc.). Each row shows the patient, SSMM ID, account and encounter status, billed/paid/due amounts, and account and patient tags.


## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `min_due` | number | Optional. Minimum account balance to include | `500` |
| `encounter_class` | text | Optional. Exact encounter class (any value except `imp`) | `amb` |
| `encounter_status` | field filter | Optional. Mapped to `emr_encounter.status` | `completed` |
| `ssmm_id` | text | Optional. Exact SSMM patient ID | `SSMM12345` |
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
    WHERE ROUND(a.total_balance) > 0
      AND e.encounter_class != 'imp'
    --   [[AND a.total_balance >= {{min_due}}]]
    --   [[AND e.encounter_class = {{encounter_class}}]]
    --   [[AND {{encounter_status}}]]
    --   [[AND pi.value = {{ssmm_id}}]]
    --   [[AND {{encounter_date}}]]
    ORDER BY a.id, (e.id = a.primary_encounter_id) DESC, e.created_date DESC
) t
ORDER BY t.account_due DESC, t.account_id;
```

## Notes

- **Non-inpatient only:** `e.encounter_class != 'imp'` is applied before `DISTINCT ON`, so an account whose primary encounter is inpatient can still appear here through a non-inpatient encounter from its charge items.
- **`encounter_class` variable:** Narrows to one class such as `amb` or `emer`.
- **Due filter:** Only accounts whose rounded `total_balance` is above `0` are shown. 
- **Amounts:** `account_due`, `account_billed_gross`, and `account_paid` are rounded to whole numbers.
- **SSMM ID:** Taken from `emr_patientidentifier` with `config_id = 21`; `ssmm_id` is an exact match.
 - **Field filters:** When enabling the commented optional clauses in Metabase, map `{{encounter_status}}` to `emr_encounter.status` and set its **Table and field alias** to `e.status`; map `{{encounter_date}}` to `emr_encounter.created_date` and set its **Table and field alias** to `e.created_date`.
- **Ordering:** Highest due amount first, then by account id.

*Last updated: 2026-10-29*
