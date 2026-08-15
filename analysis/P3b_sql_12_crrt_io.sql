-- P3b Step 6a: CRRT (continuous modalities, aligned with MIMIC procedureevents CRRT)
DROP TABLE IF EXISTS eicu_p3b_crrt;
CREATE TABLE eicu_p3b_crrt AS
SELECT DISTINCT t.patientunitstayid
FROM treatment t
JOIN eicu_p3b_cand c ON c.patientunitstayid=t.patientunitstayid
WHERE lower(t.treatmentstring) ~ 'c v v h|cvvh|sled|c a v h|cavh|scuf|continuous renal replacement|crrt|ultrafiltr';
-- IHD flag (intermittent hemodialysis) - separate for transparency
DROP TABLE IF EXISTS eicu_p3b_ihd;
CREATE TABLE eicu_p3b_ihd AS
SELECT DISTINCT t.patientunitstayid
FROM treatment t
JOIN eicu_p3b_cand c ON c.patientunitstayid=t.patientunitstayid
WHERE lower(t.treatmentstring) LIKE '%hemodial%'
  AND lower(t.treatmentstring) NOT LIKE '%insertion of venous catheter%'
  AND lower(t.treatmentstring) NOT LIKE '%for chronic renal failure%';
-- Step 6b: fluids intake/output daily
DROP TABLE IF EXISTS eicu_p3b_io_daily;
CREATE TABLE eicu_p3b_io_daily AS
SELECT io.patientunitstayid,
  CASE WHEN io.intakeoutputoffset<1440 THEN 0 WHEN io.intakeoutputoffset<2880 THEN 1 ELSE 2 END AS day,
  SUM(CASE WHEN io.cellpath ILIKE '%Intake (ml)%' THEN io.cellvaluenumeric ELSE 0 END) AS intake_ml,
  SUM(CASE WHEN io.cellpath ILIKE '%Output (ml)%' THEN io.cellvaluenumeric ELSE 0 END) AS output_ml
FROM intakeoutput io
JOIN eicu_p3b_cand c ON c.patientunitstayid=io.patientunitstayid
WHERE io.intakeoutputoffset<=4320 AND io.cellvaluenumeric>0
GROUP BY io.patientunitstayid,
  CASE WHEN io.intakeoutputoffset<1440 THEN 0 WHEN io.intakeoutputoffset<2880 THEN 1 ELSE 2 END;
