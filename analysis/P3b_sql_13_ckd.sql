-- P3b Step 7: CKD5 / chronic dialysis exclusion (aligned with MIMIC CKD5+ESRD exclusion)
DROP TABLE IF EXISTS eicu_p3b_ckd;
CREATE TABLE eicu_p3b_ckd AS
SELECT DISTINCT patientunitstayid FROM (
  SELECT d.patientunitstayid
  FROM diagnosis d JOIN eicu_p3b_cand c ON c.patientunitstayid=d.patientunitstayid
  WHERE btrim(split_part(d.icd9code,',',1)) ~ '^(585\.5|585\.6|V45\.1|V56\.)'
     OR btrim(split_part(d.icd9code,',',2)) ~ '^(N18\.[56]|Z99\.2)'
     OR d.diagnosisstring ILIKE '%ESRD (end stage renal disease)%'
     OR d.diagnosisstring ILIKE '%chronic kidney disease|Stage 5%'
  UNION
  SELECT p.patientunitstayid
  FROM pasthistory p JOIN eicu_p3b_cand c ON c.patientunitstayid=p.patientunitstayid
  WHERE lower(p.pasthistorypath) LIKE '%renal failure - hemodialysis%'
     OR lower(p.pasthistorypath) LIKE '%renal failure - peritoneal dialysis%'
     OR lower(p.pasthistorypath) LIKE '%renal failure- not currently dialyzed%'
     OR lower(p.pasthistorypath) LIKE '%s/p renal transplant%'
  UNION
  SELECT t.patientunitstayid
  FROM treatment t JOIN eicu_p3b_cand c ON c.patientunitstayid=t.patientunitstayid
  WHERE lower(t.treatmentstring) LIKE '%for chronic renal failure%'
) x;
