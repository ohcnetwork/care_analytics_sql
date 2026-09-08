
# List of Users with Manager Role Assigned to Specific Organizations

> Staff members with a specific role assignment at a specific organization

## Purpose

Lists users assigned to the manager role (`role_id = 100`) for the selected organization (`organization_id = 101`), including the staff member's display name, organization name, and role name.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| *(none)* | - | Query uses hardcoded role and organization ids | - |

---

## Query

```sql
SELECT
	TRIM(COALESCE(u.prefix || ' ', '') || u.first_name || ' ' || u.last_name) AS staff_name,
	o.name AS organization_name,
	r.name AS role_name
FROM emr_organizationuser ou
INNER JOIN users_user u
	ON u.id = ou.user_id
INNER JOIN emr_organization o
	ON o.id = ou.organization_id
INNER JOIN security_rolemodel r
	ON r.id = ou.role_id
WHERE ou.role_id = 100
  AND ou.organization_id = 101
  AND ou.deleted = FALSE
  AND u.deleted = FALSE
  AND r.deleted = FALSE
ORDER BY staff_name;
```

## Notes

- **Hardcoded filters:** `ou.role_id = 100` and `ou.organization_id = 101` are fixed in the query. Update these values if you want to inspect a different role or organization.
- **No Metabase variables:** The query currently has no optional `[[...]]` filters and runs as a static lookup.
- Results are ordered alphabetically by staff name.

*Last updated: 2026-08-31*
