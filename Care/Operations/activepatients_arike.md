# Active Patients List - Arike

> List of active patients with recent encounters or upcoming appointments, including tags and F10 questionnaire status

## Purpose

This query identifies active patients in Arike by combining two criteria: patients with encounters in the last 100 days OR patients with upcoming appointments in the next 101 days. It provides comprehensive patient information including demographics, appointment status, classification tags (zone, alerts, visit frequency, etc.), and F10 questionnaire completion status. Useful for patient management, care planning, and tracking patient engagement.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `zone_filter` | TEXT | Filters by patient zone tag | `'Zone A'` |
| `alerts_filter` | TEXT | Filters by patient alerts tag | `'High Priority'` |
| `frequency_filter` | TEXT | Filters by frequency of visit tag | `'Weekly'` |
| `special_visit_filter` | TEXT | Filters by special visit tag | `'Home Visit'` |
| `cross_subsided_model_filter` | TEXT | Filters by cross-subsidized model tag | `'Subsidized'` |
| `Others_filter` | TEXT | Filters by other tags | `'Special Care'` |
| `appointment_status` | TEXT | Filters by appointment status | `'Has Appointment'` or `'No Appointment'` |

---

## Query

```sql
-- Patients with encounters in last 100 days
WITH 
recent_encounters AS (
    SELECT
        ep.id AS patient_id,
        ep.name AS patient_name,
        ep.gender,
        ep.phone_number,
        ep.year_of_birth,
        pi.value AS adm,
        ee.created_date,
        ep.instance_tags
    FROM emr_patient ep
    JOIN emr_encounter ee 
        ON ep.id = ee.patient_id
    LEFT JOIN emr_patientidentifier pi 
        ON ep.id = pi.patient_id AND pi.config_id = 2
    WHERE ee.created_date >= CURRENT_DATE - INTERVAL '100 days'
      AND ee.facility_id = 2
      AND ep.deleted = FALSE
      AND ee.deleted = FALSE
      AND ep.deceased_datetime IS NULL
),

-- Patients with upcoming appointments
upcoming_appointments_with_next AS (
    SELECT
        ep.id AS patient_id,
        ep.name AS patient_name,
        ep.gender,
        ep.phone_number,
        ep.year_of_birth,
        pi.value AS adm,
        ep.instance_tags,
        MIN(ts.start_datetime) AS next_appointment_date,
        MIN(ts.start_datetime) AS created_date
    FROM emr_tokenbooking tb
    JOIN emr_tokenslot ts 
        ON tb.token_slot_id = ts.id
    JOIN emr_schedulableresource sbr 
        ON ts.resource_id = sbr.id
    JOIN emr_patient ep 
        ON tb.patient_id = ep.id
    LEFT JOIN emr_patientidentifier pi 
        ON ep.id = pi.patient_id AND pi.config_id = 2
    WHERE ts.start_datetime >= CURRENT_DATE
      AND ts.start_datetime < CURRENT_DATE + INTERVAL '101 days'
      AND sbr.facility_id = 2
      AND ep.deleted = FALSE
      AND ts.deleted = FALSE
      AND tb.status = 'booked'
      AND ep.deceased_datetime IS NULL
    GROUP BY ep.id, ep.name, ep.gender, ep.phone_number, ep.year_of_birth, pi.value, ep.instance_tags
),

-- Combine patients
active_patients_combined AS (
    SELECT 
        patient_id, patient_name, gender, phone_number, year_of_birth, 
        adm, created_date, instance_tags,
        NULL AS next_appointment_date
    FROM recent_encounters
    
    UNION ALL
    
    SELECT 
        patient_id, patient_name, gender, phone_number, year_of_birth, 
        adm, created_date, instance_tags,
        next_appointment_date
    FROM upcoming_appointments_with_next
),

-- Get latest record per patient with next appointment
active_patients AS (
    SELECT DISTINCT ON (patient_id)
        patient_id, 
        patient_name, 
        gender, 
        phone_number, 
        year_of_birth,
        adm, 
        instance_tags,
        next_appointment_date
    FROM active_patients_combined
    ORDER BY patient_id, created_date DESC, next_appointment_date DESC NULLS LAST
),

-- Extract patient tags
patient_tags AS (
    SELECT
        ap.patient_id,
        COALESCE(MAX(CASE WHEN et.parent_id = 55 THEN et.display END), 'Unassigned') AS zone,
        MAX(CASE WHEN et.parent_id = 47 THEN et.display END) AS alerts,
        COALESCE(MAX(CASE WHEN et.parent_id = 18 THEN et.display END), 'Unassigned') AS frequency_of_visit,
        MAX(CASE WHEN et.parent_id = 22 THEN et.display END) AS special_visit,
        COALESCE(MAX(CASE WHEN et.parent_id = 26 THEN et.display END), 'Unassigned') AS cross_subsided_model,
        MAX(CASE WHEN et.id IN (66, 67, 68) THEN et.display END) AS others
    FROM active_patients ap
    LEFT JOIN LATERAL unnest(ap.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig et 
        ON et.id = tag_id 
        AND et.deleted = FALSE
    GROUP BY ap.patient_id
),

-- calculate f10_filled
f10_filled_patients AS (
    SELECT DISTINCT patient_id
    FROM emr_questionnaireresponse
    WHERE questionnaire_id = 16
      AND deleted = FALSE
      AND patient_id IN (SELECT patient_id FROM active_patients)
)

SELECT 
    ap.patient_name,
    ap.gender,
    ap.phone_number,
    ap.year_of_birth,
    ap.adm,
    ap.next_appointment_date AS upcoming_appointment,
    CASE 
        WHEN ap.next_appointment_date IS NOT NULL THEN 'Has Appointment'
        ELSE 'No Appointment'
    END AS appointment_status,
    pt.zone,
    pt.alerts,
    pt.frequency_of_visit,
    pt.special_visit,
    pt.cross_subsided_model,
    pt.others,
    CASE 
        WHEN f10.patient_id IS NOT NULL THEN 'Yes'
        ELSE 'No'
    END AS f10_filled
FROM active_patients ap
LEFT JOIN patient_tags pt ON pt.patient_id = ap.patient_id
LEFT JOIN f10_filled_patients f10 ON f10.patient_id = ap.patient_id
WHERE 1=1
    -- [[AND pt.zone = {{zone_filter}}]]
    -- [[AND pt.alerts = {{alerts_filter}}]]
    -- [[AND pt.frequency_of_visit = {{frequency_filter}}]]
    -- [[AND pt.special_visit = {{special_visit_filter}}]]
    -- [[AND pt.cross_subsided_model = {{cross_subsided_model_filter}}]]
    -- [[AND pt.others = {{Others_filter}}]]
    -- [[AND CASE 
    --     WHEN {{appointment_status}} = 'Has Appointment' THEN ap.next_appointment_date IS NOT NULL  
    --     WHEN {{appointment_status}} = 'No Appointment' THEN ap.next_appointment_date IS NULL
    --     ELSE TRUE
    -- END]]
ORDER BY ap.patient_name;
```


## Notes

- Query is filtered to `facility_id = 2` - update this value as needed
- Uses `config_id = 2` for admission number - verify this matches your setup
- F10 questionnaire has `questionnaire_id = 16` - update if different
- Excludes deceased patients (deceased_datetime IS NULL)
- Results are ordered alphabetically by patient name

*Last updated: 2026-01-09*
