-- P3b Step 2: base candidates = patient-level first ICU stay + age>=18 + LOS>=24h
DROP TABLE IF EXISTS eicu_p3b_cand;
CREATE TABLE eicu_p3b_cand AS
SELECT b.*
FROM eicu_p3b_base b
WHERE b.first_icu_stay AND b.age_num >= 18 AND b.unitdischargeoffset >= 1440;
CREATE INDEX IF NOT EXISTS eicu_p3b_cand_pk ON eicu_p3b_cand(patientunitstayid);
