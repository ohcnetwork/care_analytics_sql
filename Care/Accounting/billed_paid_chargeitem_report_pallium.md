
# Billed / Paid Charge Item Report - Pallium

> List of charge items currently in `billed` or `paid` status with patient, item, modifier and pricing details

## Purpose

 Shows every charge item that has been billed or paid, along with the patient (and their Pallium ID), the charge item title and quantity, total price, when it was last modified and by whom.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `DATE` | DATE / range | Metabase date filter (typically bound to `ci.modified_date`) | `'2026-05-28'` |
| `chargeitem` | TEXT (multi) | Filter by one or more charge item titles | `'Consultation', 'X-Ray'` |

---

## Query

```sql
SELECT
    p.name AS patient_name,
    pi.value AS ssmm_id,
    ci.modified_date,
    ci.status,
    ci.title,
    ci.quantity,
    TRIM(modified_user.first_name || ' ' || COALESCE(modified_user.last_name, '')) AS modified_by,
    ci.total_price
FROM emr_chargeitem ci
JOIN emr_patient p ON ci.patient_id = p.id
LEFT JOIN emr_patientidentifier pi ON p.id = pi.patient_id AND pi.config_id = 4
LEFT JOIN users_user modified_user ON ci.updated_by_id = modified_user.id
WHERE ci.status IN ('billed', 'paid')
  --[[AND {{DATE}}]]
  --[[AND ci.title IN ({{chargeitem}})]]
ORDER BY ci.modified_date DESC;
```


## Notes

- **Hardcoded values:**
  - `pi.config_id = 4` — the identifier config representing the Pallium ID. Update if the config ID changes.
- **Metabase filters:**
  - `[[AND {{DATE}}]]` is a field filter — bind it to `ci.modified_date` (or `ci.created_date`) in the Metabase variable settings.
  - `[[AND ci.title IN ({{chargeitem}})]]` accepts a multi-select list of charge item titles.
- **Ordering** — most recently modified first.

*Last updated: 2026-05-28*

````

