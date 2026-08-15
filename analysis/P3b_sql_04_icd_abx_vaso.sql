-- P3b Step 3: sepsis identification cheap legs (restricted to candidate base)
-- 3a. ICD sepsis stays
DROP TABLE IF EXISTS eicu_p3b_icd_sepsis;
CREATE TABLE eicu_p3b_icd_sepsis AS
SELECT DISTINCT d.patientunitstayid
FROM diagnosis d
JOIN eicu_p3b_cand c ON c.patientunitstayid = d.patientunitstayid
WHERE btrim(split_part(d.icd9code, ',', 1)) ~ '^(0?38|995\.91|995\.92|785\.52)'
   OR btrim(split_part(d.icd9code, ',', 2)) ~ '^(A4[01]|R65\.2)'
   OR d.diagnosisstring ILIKE '%sepsis%';

-- 3b. Antibiotic exposure stays (medication, not cancelled)
DROP TABLE IF EXISTS eicu_p3b_abx;
CREATE TABLE eicu_p3b_abx AS
SELECT DISTINCT m.patientunitstayid
FROM medication m
JOIN eicu_p3b_cand c ON c.patientunitstayid = m.patientunitstayid
JOIN eicu_p3b_drugs g ON g.drug = btrim(lower(m.drugname)) AND g.drug_class='abx_med'
WHERE m.drugordercancelled='No';

-- 3c. Vasopressor stays (infusiondrug)
DROP TABLE IF EXISTS eicu_p3b_vaso;
CREATE TABLE eicu_p3b_vaso AS
SELECT DISTINCT i.patientunitstayid
FROM infusiondrug i
JOIN eicu_p3b_cand c ON c.patientunitstayid = i.patientunitstayid
JOIN eicu_p3b_drugs g ON g.drug = btrim(lower(i.drugname)) AND g.drug_class='vaso_inf';
