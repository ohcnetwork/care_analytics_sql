
# Facility Location - SSMM

> Lookup of facility location IDs and names for SSMM

## Purpose

Returns the list of selected facility location records (`emr_facilitylocation`) for the curated set of SSMM locations.

---

## Query

```sql
select id,name from emr_facilitylocation fl where fl.deleted = FALSE
   AND fl.status = 'active'
   AND fl.id IN (
     287, 296, 286, 284, 288, 239, 285, 291, 289, 282,
     293, 292, 269, 20, 642, 55, 49, 290, 12, 9,
     283, 295, 281, 294)
```

## Notes

- The hardcoded list of IDs corresponds to the SSMM locations — update this list if locations are added, removed, or renumbered in the SSMM environment.
- Results are ordered alphabetically by `name` for easier scanning.

*Last updated: 2026-06-16*
