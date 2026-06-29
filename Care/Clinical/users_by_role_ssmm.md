
# Users by Role - SSMM

> Lookup of users assigned to a specific facility-organization role

## Purpose

Returns the list of users assigned to a specific role (`emr_facilityorganizationuser.role_id`) at SSMM, along with their formatted display name (`prefix + first_name + last_name`). 

---

## Query

```sql
SELECT
    TRIM(COALESCE(u.prefix || ' ', '') || u.first_name || ' ' || u.last_name, '') AS username,
    efu.role_id
FROM emr_facilityorganizationuser efu
JOIN users_user u
    ON efu.user_id = u.id
WHERE efu.role_id = 3
  AND efu.deleted = FALSE
ORDER BY username;
```

## Notes

- `efu.role_id = 3` is hardcoded — change this value to look up users assigned to a different role.
- Only active (`efu.deleted = FALSE`) role assignments are included.
- Results are ordered alphabetically by `username`.

*Last updated: 2026-06-29*
