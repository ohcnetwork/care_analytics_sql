
# Candidate Test Performance Table

> Summarizes and reports how each candidate (user) has performed in the test, showing a checklist of completed steps in a simulated healthcare process.

## Purpose

This query generates a table listing users and a series of tasks, indicating whether or not each user has completed each designated step in a simulated healthcare process. It relates candidates to assigned patients and checks for the completion of various clinical and admin tasks, generating a checklist-style output for test evaluation.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `user_external_id` | UUID | Candidate user external ID (hardcoded) | `'1243ce56-f3ae-4dcb-8164-b89dddaa6f5c'` |
| `patient_external_id` | UUID | Assigned patient external ID (hardcoded) | `'9cb1861b-e3e3-4947-bb93-17fa0d36a2a0'` |
| `date_opd_appointment` | DATE | OPD appointment date for Task 2 | `'2025-12-25'` |
| `date_reschedule` | DATE | Practitioner 80 slot rescheduling date for Task 6A | `'2025-12-15'` |
| `date_booking` | DATE | Practitioner 80 slot booking date for Task 6B | `'2025-12-20'` |
| `patient_tag_id` | INTEGER | Patient tag ID for Task 1B | `16` |
| `doctor_role_id` | INTEGER | Role ID for doctor in Task 4 | `1` |
| `questionnaire_id` | INTEGER | Questionnaire ID for Task 3B | `42` |
| `department_names` | TEXT | Department/Organization names | `'Casualty Department'`, `'Cardiology Department'` |
| `medicine_names` | TEXT | Medicines to check for in Task 3C | `'Ambroxol'`, `'Ibuprofen'

---

## Query

```sql
WITH assigned_patients AS (
    SELECT
        uu.id AS user_id,
        uu.last_login,
        uu.first_name || ' ' || uu.last_name AS user_name,
        ep.id AS patient_id,
        ep.name AS patient_name
    FROM (
        VALUES
         ('1243ce56-f3ae-4dcb-8164-b89dddaa6f5c', '9cb1861b-e3e3-4947-bb93-17fa0d36a2a0'),
         ('52bb573a-dc0f-4f30-9d2b-533da0597d8d', '8f694a9d-9cea-4308-909b-6bcb99de906e'),
         ('c0ad5df7-1a20-4d6d-b7ec-9f514d8ac026', '818228f4-e258-415d-8051-9c4c767a0205'),
         ('1c782611-9982-494b-80f0-441bbe062001', '4846c367-16b1-44d4-80a7-acb51fe6d0a9'),
         ('e28b24e9-b4e2-4524-b969-f078fd85aeb0', 'e25300a6-7988-4af3-8d1e-2532e49e900a'),
         ('87cfc7a9-509b-418b-945d-9feacd6da37f', '8c9a9d60-ae19-4444-a138-0a3c60dabf85'),
         ('dc21122e-291a-4f68-9bbf-86373921f145', '7859bf72-f93d-420d-aab4-3d668d141d7a'),
         ('543a4b8a-b327-4d5c-ae58-0487fa391997', 'a8ae9141-11a9-4936-ab6d-9c38ce0e405e'),
         ('64c157c6-2187-415e-a87a-e7b0babcba7e', '17f7eaff-c48f-487d-b62a-dc7737ba6250'),
         ('91ca0f9e-ea1d-4d60-a10f-06bd0cf69e79', '089c5067-ae41-44e5-a1ca-ace5b4c28cef'),
         ('042b61ec-c9ef-4666-b8aa-9f3526b45322', '93acc557-8827-4e8a-ac17-13f99e11bfc3'),
         ('1afb2221-e8e9-4494-9ad1-742be26f84b2', 'a74d4d05-924e-42a8-8ebd-76e25e93321a'),
         ('31be1f77-8590-4bc0-8f3b-18445010202d', 'e308c1a4-0340-4104-8d9b-15a7b45ac065'),
         ('eeda4dc0-e09a-4d06-a6c3-a24cffbafd56', '255cea64-b264-4c23-8f68-f093dcde9f0b'),
         ('f5a761b7-565f-4370-8e40-bb50234ee71d', '6a91f231-2f7e-4ac9-b7e1-134136bde517'),
         ('03f47ac8-5b4e-4970-9476-2d9df812d817', '3aca21f0-a9cc-4d7f-9134-4b50964dd1fb'),
         ('ee7c9003-dbd0-47b2-86c7-c157b4874acc', 'f71d5f71-00c0-4599-b709-3aa48aa70493'),
         ('4182481d-0300-47e6-bb2b-deeb40a54980', '949fd7e1-45d9-4b6a-8b99-601b85ecc163'),
         ('fb5d33e1-e0aa-489e-a69a-4a0302810a21', '14960603-8afe-4c96-bee2-bd811eb12757'),
         ('4a60b5ae-e7e8-4f69-ab64-886bac813887', 'e9488d4e-76ea-4c4c-b105-05a74286ad86'),
         ('9bee5925-177b-4622-8f06-920f15485781', '8f199b4f-d200-40a4-a93f-1925b7bc0467'),
         ('cd15c90c-07de-453a-8476-ccb003789808', '41fc0022-23bc-4645-9b04-a9999f4228f2'),
         ('27104712-d0a6-491c-94a6-c17feea2bb46', 'b26a4e42-0ec6-4ac7-9ac6-f8c7f2e267f4'),
         ('d276e918-7d38-4db4-bda5-e0d1dac43844', '234369ab-a767-428e-9dfe-36057f54f6b5'),
         ('9eae8fda-27fd-4d34-8e79-67f77002fdcb', '59837e94-865c-4682-980e-e5079b93720b'),
         ('879ea595-0c35-4517-b850-1fc5893c1d6d', '10790a32-666b-47f0-97f5-db40e7c36732')
    ) AS mapping(user_external_id, patient_external_id)
    JOIN users_user uu ON uu.external_id = mapping.user_external_id ::uuid
    JOIN emr_patient ep ON ep.external_id = mapping.patient_external_id ::uuid
)
SELECT
    u.id AS user_id,
	u.last_login,
    u.first_name || ' ' || u.last_name AS user_name,

    -- Task 1: Patient registration
    CASE 
        WHEN EXISTS (
            SELECT 1
            FROM emr_patient ep
            WHERE ep.created_by_id = u.id 
              AND ep.deleted = FALSE
			  
        ) THEN '✅'
        ELSE '❌'
    END AS task1A_patient_registration,

   ---Task 1B : Patient tag
       CASE 
        WHEN EXISTS (
            SELECT 1
            FROM emr_patient ep
            LEFT JOIN LATERAL unnest(ep.instance_tags) AS tag_id ON TRUE
            WHERE ep.created_by_id = u.id 
              AND ep.deleted = FALSE
			  AND tag_id = 16
        ) THEN '✅'
        ELSE '❌'
    END AS task1B_patient_tag,
	

    -- Task 2: opd appointment
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM emr_tokenbooking tb
            JOIN emr_tokenslot ts ON tb.token_slot_id = ts.id
            JOIN emr_schedulableresource sr ON ts.resource_id = sr.id
            JOIN emr_healthcareservice hs ON sr.healthcare_service_id = hs.id
            WHERE tb.created_by_id = u.id
              AND tb.status = 'booked'
              AND DATE(ts.start_datetime) = '2025-12-25'
              AND sr.resource_type = 'healthcare_service'
              AND hs.name = 'OPD Department'
        ) THEN '✅'
        ELSE '❌'
    END AS task2_opd_appointment,

    -- Task 3A: emergency encounter
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM assigned_patients ap
            JOIN emr_encounter e ON e.patient_id = ap.patient_id 
            JOIN emr_encounterorganization eo ON eo.encounter_id = e.id
            JOIN emr_facilityorganization fo ON eo.organization_id = fo.id
            WHERE ap.user_id = u.id
              AND e.created_by_id = u.id
              AND e.encounter_class = 'emer'
              AND e.priority = 'emergency'
              AND fo.name = 'Casualty Department'
        ) THEN '✅'
        ELSE '❌'
    END AS task3A_emergency_encounter,

    -- Task 3B: Forms filled
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM assigned_patients ap
            JOIN emr_encounter e ON e.patient_id = ap.patient_id
            JOIN emr_questionnaireresponse qr ON qr.encounter_id = e.id
            WHERE ap.user_id = u.id
              AND e.created_by_id = u.id
              -- AND e.encounter_class = 'emer'
              -- AND e.priority = 'emergency'
              AND qr.questionnaire_id = 42
              
        ) THEN '✅'
        ELSE '❌'
    END AS task3B_doctors_consultation,

    -- Task 3C: prescribed medicine
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM assigned_patients ap
            JOIN emr_encounter e ON e.patient_id = ap.patient_id
            JOIN emr_medicationrequest mr ON mr.encounter_id = e.id
            WHERE ap.user_id = u.id
              AND e.created_by_id = u.id
              -- AND e.encounter_class = 'emer'
              -- AND e.priority = 'emergency'
              AND mr.created_by_id = u.id
              AND (
                mr.medication->>'display' ILIKE '%Ambroxol%' OR
                mr.medication->>'display' ILIKE '%Ibuprofen%'
              )
        ) THEN '✅'
        ELSE '❌'
    END AS task3C_prescribed_medicine,

    -- Task 3D: encounter closed
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM assigned_patients ap
            JOIN emr_encounter e ON e.patient_id = ap.patient_id
            JOIN emr_encounterorganization eo ON eo.encounter_id = e.id
            JOIN emr_facilityorganization fo ON eo.organization_id = fo.id
            WHERE ap.user_id = u.id
              AND e.created_by_id = u.id
              AND e.encounter_class = 'emer'
              AND e.priority = 'emergency'
              AND e.status = 'completed'
              AND fo.name = 'Casualty Department'
        ) THEN '✅'
        ELSE '❌'
    END AS task3D_encounter_closed,

   -- Task 4: Created a doctor user in Cardiology Department
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM users_user doc
            JOIN emr_facilityorganizationuser fou ON fou.user_id = doc.id
            JOIN emr_facilityorganization fo ON fou.organization_id = fo.id
            WHERE doc.user_type = 'doctor'
              AND fou.created_by_id = u.id
			  AND fou.role_id = 1
              AND fo.name ILIKE '%cardiology department%'
        ) THEN '✅'
        ELSE '❌'
    END AS task4_created_doctor_in_cardiology,

    -- Task 5: Schedule for Dr. Anjali Kumari in Cardiology OPD, created by this user
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM emr_availability avail
            JOIN emr_schedule sched ON avail.schedule_id = sched.id
            JOIN emr_schedulableresource sr ON sched.resource_id = sr.id
            JOIN users_user doc ON sr.user_id = doc.id
            WHERE avail.name ILIKE 'Cardiology OPD Session'
              AND avail.slot_type = 'appointment'
              AND avail.slot_size_in_minutes = 30
              AND avail.tokens_per_slot = 1
              AND sched.name ILIKE 'regular visit'
              AND sched.created_by_id = u.id
              AND doc.first_name || ' ' || doc.last_name ILIKE '%anjali kumari%'
        ) THEN '✅'
        ELSE '❌'
    END AS task5_anjali_cardiology_schedule,

      -- Task 6a: Practitioner slot rescheduling for user_id=80 on Dec 15
	  CASE
        WHEN EXISTS (
            SELECT 1
            FROM emr_tokenbooking tb
            JOIN emr_tokenslot ts ON tb.token_slot_id = ts.id
            JOIN emr_schedulableresource sr ON ts.resource_id = sr.id
            JOIN users_user pr ON sr.user_id = pr.id
            WHERE tb.created_by_id = u.id
              AND tb.status = 'rescheduled'
              AND DATE(ts.start_datetime) = '2025-12-15'
              AND sr.resource_type = 'practitioner'
              AND sr.user_id = 80
        ) THEN '✅'
        ELSE '❌'
    END AS task6A_practitioner_80_rescheduled,

	
    -- Task 6b: Practitioner slot booking for user_id=80 on Dec 20
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM emr_tokenbooking tb
            JOIN emr_tokenslot ts ON tb.token_slot_id = ts.id
            JOIN emr_schedulableresource sr ON ts.resource_id = sr.id
            JOIN users_user pr ON sr.user_id = pr.id
            WHERE tb.created_by_id = u.id
              AND tb.status = 'booked'
              AND DATE(ts.start_datetime) = '2025-12-20'
              AND sr.resource_type = 'practitioner'
              AND sr.user_id = 80
        ) THEN '✅'
        ELSE '❌'
    END AS task6B_practitioner_80_booked

FROM
    users_user u
WHERE
    u.id IN (SELECT user_id FROM assigned_patients)
ORDER BY
    u.first_name, u.last_name;


```

## Notes

- The test dependencies are hardcoded, so this query is for controlled scenarios only.
- All users and patients considered are specified in the VALUES clause in the `assigned_patients` CTE.
- The dates and resource IDs are fixed; update for different test periods or practitioners as needed.
- Make sure the associated tables (`users_user`, `emr_patient`, etc.) exist and are populated.

*Last updated: 2025-12-15*
