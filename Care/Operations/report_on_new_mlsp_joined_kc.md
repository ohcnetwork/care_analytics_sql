
# Report on New MLSP Joined
> Active users belonging to a JAK facility organization with their join date

## Purpose

Lists distinct active users who are assigned to a facility organization whose name contains **"jak"** (case-insensitive) — used to track newly on-boarded MLSP staff at JAK-linked organizations. Each row shows the user id, full name, and the `date_joined` timestamp.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date_joined` | DATE / range | Metabase date filter (typically bound to `users_user.date_joined`) | `'2026-06-01'` |

---

## Query

```sql
SELECT DISTINCT
    users_user.id,
    users_user.first_name || ' ' || users_user.last_name AS full_name,
    users_user.date_joined
FROM users_user
 JOIN emr_facilityorganizationuser
    ON users_user.id = emr_facilityorganizationuser.user_id
 JOIN emr_facilityorganization
    ON emr_facilityorganizationuser.organization_id = emr_facilityorganization.id
WHERE users_user.is_active = TRUE
  AND LOWER(emr_facilityorganization.name) LIKE '%jak%'
  --[[AND {{date_joined}}]]
ORDER BY full_name;
```

## Notes

- **Organization filter:** `LOWER(emr_facilityorganization.name) LIKE '%jak%'` matches any facility organization whose name contains the substring "jak" (case-insensitive). Update the pattern if the naming convention changes.
- **Metabase filter:**
  - `[[AND {{date_joined}}]]` is a field filter — bind it to `users_user.date_joined` in the Metabase variable settings.
- Results are ordered alphabetically by `full_name`.

*Last updated: 2026-07-06*
