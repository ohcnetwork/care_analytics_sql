
# Count of Users Linked to Government Facilities 

> Cumulative count of distinct active users linked to government facilities, as of the end of each reporting quarter

## Purpose

Operational metric for tracking user onboarding growth across government facilities. A user is counted if they are a member of any (non-deleted) facility organization belonging to a government facility, and their account was created on or before the snapshot date.

---

## Query

```sql
SELECT
    COUNT(DISTINCT fou.user_id) FILTER (WHERE u.date_joined < DATE '2025-04-01') AS users_until_31_mar_2025,
    COUNT(DISTINCT fou.user_id) FILTER (WHERE u.date_joined < DATE '2026-04-01') AS users_until_31_mar_2026,
    COUNT(DISTINCT fou.user_id) FILTER (WHERE u.date_joined < DATE '2026-07-01') AS users_until_30_jun_2026,
    COUNT(DISTINCT fou.user_id) FILTER (WHERE u.date_joined < DATE '2026-10-01') AS users_until_30_sep_2026
FROM emr_facilityorganizationuser fou
JOIN users_user u
    ON u.id = fou.user_id
   AND u.deleted = FALSE
JOIN emr_facilityorganization fo
    ON fo.id = fou.organization_id
   AND fo.deleted = FALSE
JOIN facility_facility f
    ON f.id = fo.facility_id
   AND f.deleted = FALSE
WHERE fou.deleted = FALSE
  AND f.facility_type < 2999;
```

## Notes

- Government facilities are identified by `facility_facility.facility_type < 2999`.
- Counts are cumulative, based on `users_user.date_joined` — not on when the user was added to the facility organization.
- Users linked to multiple government facilities are counted once (`COUNT(DISTINCT ...)`).
- Deleted users, facility organizations, memberships and facilities are excluded. Current membership is used, so users removed from a facility since the snapshot date are not counted.
- Snapshot dates are hardcoded — add/update the `FILTER` columns for new quarters.

*Last updated: 2026-11-16*

