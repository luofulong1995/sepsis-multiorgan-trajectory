-- P3b Step 4c: heavy scans (background)
-- urine 72h total
DROP TABLE IF EXISTS eicu_p3b_urine;
CREATE TABLE eicu_p3b_urine AS
SELECT io.patientunitstayid, SUM(io.cellvaluenumeric) AS urine_72h
FROM intakeoutput io
JOIN eicu_p3b_cand c ON c.patientunitstayid = io.patientunitstayid
WHERE io.intakeoutputoffset <= 4320
  AND io.cellvaluenumeric > 0
  AND (lower(io.celllabel) LIKE '%urine%' OR lower(io.celllabel) LIKE '%foley%'
       OR lower(io.celllabel) LIKE '%void%' OR lower(io.celllabel) LIKE '%indwelling%'
       OR lower(io.celllabel) LIKE '%urethral%')
  AND lower(io.celllabel) NOT LIKE '%count%' AND lower(io.celllabel) NOT LIKE '%occurrence%'
GROUP BY io.patientunitstayid;
-- FiO2 max % in 72h
DROP TABLE IF EXISTS eicu_p3b_fio2;
CREATE TABLE eicu_p3b_fio2 AS
SELECT rc.patientunitstayid, MAX(rc.respchartvalue::numeric) AS fio2_max_pct
FROM respiratorycharting rc
JOIN eicu_p3b_cand c ON c.patientunitstayid = rc.patientunitstayid
WHERE rc.respcharttypecat='respFlowSettings' AND rc.respchartvaluelabel='FiO2'
  AND rc.respchartoffset<=4320 AND rc.respchartvalue ~ '^[0-9]+(\.[0-9]+)?$'
  AND rc.respchartvalue::numeric BETWEEN 21 AND 100
GROUP BY rc.patientunitstayid;
-- GCS min in 72h
DROP TABLE IF EXISTS eicu_p3b_gcs;
CREATE TABLE eicu_p3b_gcs AS
SELECT n.patientunitstayid, MIN(n.nursingchartvalue::int) AS gcs_min
FROM nursecharting n
JOIN eicu_p3b_cand c ON c.patientunitstayid = n.patientunitstayid
WHERE n.nursingchartcelltypecat='Scores' AND n.nursingchartcelltypevallabel='Glasgow coma score'
  AND n.nursingchartcelltypevalname='GCS Total' AND n.nursingchartoffset<=4320
  AND n.nursingchartvalue ~ '^[0-9]+$'
GROUP BY n.patientunitstayid;
