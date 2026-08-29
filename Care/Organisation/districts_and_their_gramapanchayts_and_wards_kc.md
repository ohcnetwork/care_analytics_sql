# Districts and Their Grama Panchayats and Wards

> Hierarchical mapping of districts to their grama panchayats and wards

## Purpose

Provides a location hierarchy list of government organizations by mapping:
- District -> Grama Panchayat -> Ward


---

## Query

```sql
SELECT
		district.id AS district_id,
		district.name AS district,
		grama.id AS grama_panchayat_id,
		grama.name AS grama_panchayat,
		ward.id AS ward_id,
		ward.name AS ward
FROM emr_organization AS district
JOIN emr_organization AS grama
		ON grama.parent_cache @> ARRAY[district.id::integer]
		AND grama.deleted = false
		AND grama.org_type = 'govt'
		AND grama.metadata->>'govt_org_type' = 'grama_panchayat'
JOIN emr_organization AS ward
		ON ward.parent_id = grama.id
		AND ward.deleted = false
		AND ward.org_type = 'govt'
		AND ward.metadata->>'govt_org_type' = 'ward'
WHERE district.deleted = false
	AND district.org_type = 'govt'
	AND district.level_cache = 1
ORDER BY district.name, grama.name, ward.name;
```

## Notes

- This query has no runtime parameters.
- The district records are represented at `level_cache = 1`.
- Filters only non-deleted government organizations (`org_type = 'govt'`).
- Government subtype filtering is based on `metadata->>'govt_org_type'` values:
	- `grama_panchayat`
	- `ward`

*Last updated: 2026-08-03*
