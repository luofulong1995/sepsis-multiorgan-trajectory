-- P3b Step 1: eICU base (all ICU stays) with patient-level first-stay flag + parsed age
DROP TABLE IF EXISTS eicu_p3b_base;
CREATE TABLE eicu_p3b_base AS
SELECT patientunitstayid, uniquepid, gender, age,
  CASE WHEN age ~ '^[0-9]+$' THEN age::int
       WHEN age ~ '> ?89' THEN 90
       ELSE NULL END AS age_num,
  admissionweight, unitdischargeoffset, hospitaldischargeoffset,
  unitdischargestatus, hospitaldischargestatus, hospitaldischargeyear,
  unitvisitnumber, hospitalid, unittype, unitstaytype,
  MIN(patientunitstayid) OVER (PARTITION BY uniquepid) AS first_stay_id,
  (patientunitstayid = MIN(patientunitstayid) OVER (PARTITION BY uniquepid)) AS first_icu_stay
FROM patient;
