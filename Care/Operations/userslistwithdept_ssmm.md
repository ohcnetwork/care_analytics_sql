# Users List with Departments

> Comprehensive list of active users with their contact details, roles, and department assignments

## Purpose

This query provides a directory of all active users in the system, including their contact information, user type, assigned departments (organizations), and security roles. It's useful for user management, access auditing, and understanding organizational structure.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `full_name` | TEXT | Filters by user's full name  | `'John Doe'` |
| `department` | TEXT | Filters by department/organization name  | `'Cardiology'` |
| `role` | TEXT | Filters by security role name  | `'Doctor'` |

---

## Query

```sql
SELECT 
    CONCAT(u.first_name, ' ', u.last_name) AS full_name,
    u.phone_number,
    u.email,
    u.user_type,
    STRING_AGG(DISTINCT fo.name, ', ') AS departments,
    STRING_AGG(DISTINCT rm.name, ', ') AS roles
FROM users_user u
LEFT JOIN emr_facilityorganizationuser fou
    ON fou.user_id = u.id
LEFT JOIN emr_facilityorganization fo
    ON fo.id = fou.organization_id
LEFT JOIN security_rolemodel rm
    ON rm.id = fou.role_id
WHERE u.deleted = FALSE
    -- [[AND (CONCAT(u.first_name, ' ', u.last_name)) = ({{full_name}}) ]]
    -- [[AND (fo.name) = ({{department}}) ]]
    -- [[AND (rm.name) = ({{role}}) ]]
GROUP BY 
    u.id, full_name, u.phone_number, u.email, u.user_type
ORDER BY full_name;
```


## Notes

- Only includes active users (deleted = FALSE)
- Users with multiple department or role assignments have them aggregated into comma-separated strings
- Left joins ensure users are shown even if they have no department or role assignments
- Results are ordered alphabetically by full name
- Uses STRING_AGG with DISTINCT to avoid duplicate entries when users have multiple organization assignments

*Last updated: 2026-01-06*
