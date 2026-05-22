
# Bed Occupancy - SSMM (Excluding Fake Beds)

> Total vs. occupied bed counts grouped by floor excluding beds under the fake beds root

## Purpose

Provides a real-time bed occupancy summary at SSMM, broken down by **floor** . For each group it shows the total number of active beds and how many are currently occupied or were occupied. Beds under the fake beds root location (`root_location_id = 300`) are excluded.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `report_date` | DATE | As-of date for occupancy. A bed is considered occupied if its assignment started on/before this date and either has no end date or ended after this date. Defaults to current state when omitted. | `'2026-04-30'` |

---

## Query

```sql
WITH all_beds AS (
    
    SELECT
        parent_loc.name AS level1_name,
        COALESCE(grandparent_loc.name, parent_loc.name) AS floor,
        fl.id AS bed_id
    FROM emr_facilitylocation fl
    LEFT JOIN emr_facilitylocation parent_loc ON fl.parent_id = parent_loc.id  
    LEFT JOIN emr_facilitylocation grandparent_loc ON parent_loc.parent_id = grandparent_loc.id
    WHERE fl.deleted = FALSE
      AND fl.status = 'active'
      AND fl.form = 'bd'
      AND fl.root_location_id != 300
	  AND fl.parent_id NOT IN (19,44)
	  
),
occupied_beds AS (
    
    SELECT DISTINCT ON (e.patient_id)
        parent_loc.name AS level1_name,
        COALESCE(grandparent_loc.name, parent_loc.name) AS floor,
        fl.id AS bed_id
    FROM emr_facilitylocationencounter fle
    INNER JOIN emr_facilitylocation fl ON fle.location_id = fl.id
    LEFT JOIN emr_facilitylocation parent_loc ON fl.parent_id = parent_loc.id  
    LEFT JOIN emr_facilitylocation grandparent_loc ON parent_loc.parent_id = grandparent_loc.id
    INNER JOIN emr_encounter e ON fle.encounter_id = e.id
    WHERE fl.deleted = FALSE
      AND fl.status = 'active'
      AND fl.form = 'bd'
      AND fl.root_location_id != 300
	  AND fl.parent_id NOT IN (19,44)
      AND fle.deleted = FALSE
      --AND DATE(fle.start_datetime) <= {{report_date}}
      --AND (fle.end_datetime IS NULL OR DATE(fle.end_datetime) > {{report_date}})
    ORDER BY e.patient_id, fle.start_datetime DESC
),
bed_stats AS (
    SELECT
        ab.level1_name,
        ab.floor,
        COUNT(DISTINCT ab.bed_id) AS total_bed_count,
        COUNT(DISTINCT ob.bed_id) AS occupied_bed_count
    FROM all_beds ab
    LEFT JOIN occupied_beds ob 
        ON ab.bed_id = ob.bed_id 
        AND ab.level1_name = ob.level1_name 
        AND ab.floor = ob.floor
    GROUP BY ab.level1_name, ab.floor
)

SELECT * FROM (
    SELECT * FROM bed_stats
    
    UNION ALL
    
    SELECT
        'Total' AS level1_name,
        'Total' AS floor,
        SUM(total_bed_count) AS total_bed_count,
        SUM(occupied_bed_count) AS occupied_bed_count
    FROM bed_stats
) AS final_result
ORDER BY CASE WHEN floor = 'Total' THEN 1 ELSE 0 END, floor, level1_name;
```

## Notes

- **`all_beds` CTE** — every active, real bed (`form = 'bd'`, not under the fake root, not deleted, status `active`).
- **`occupied_beds` CTE** — for each patient, the latest bed assignment.
- **Hardcoded values:**
  - `fl.root_location_id != 300` — excludes the fake beds root. Update if the fake-beds root ID changes.
  - `fl.parent_id NOT IN (19, 44)` — excludes specific parent locations (In this case OT and casualty). Update these IDs if the excluded wards change.
  - `fl.form = 'bd'` — only bed-type facility locations.
  - `fl.status = 'active'` — only currently active beds count toward totals.
- **`report_date` filter** — when provided, treats a bed as occupied if `start_datetime <= report_date` and (`end_datetime IS NULL` OR `end_datetime > report_date`).


*Last updated: 2026-05-04*

````
