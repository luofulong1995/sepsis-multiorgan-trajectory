-- P3b Step 4a: SOFA raw components (indexed tables: lab, vitalperiodic)
-- worst lab in 72h
DROP TABLE IF EXISTS eicu_p3b_sofa_lab;
CREATE TABLE eicu_p3b_sofa_lab AS
SELECT l.patientunitstayid,
  MIN(l.labresult) FILTER (WHERE l.labname='platelets x 1000') AS plt_min72,
  MAX(l.labresult) FILTER (WHERE l.labname='total bilirubin')  AS bili_max72,
  MAX(l.labresult) FILTER (WHERE l.labname='creatinine')       AS cre_max72
FROM lab l
JOIN eicu_p3b_cand c ON c.patientunitstayid = l.patientunitstayid
WHERE l.labname IN ('platelets x 1000','total bilirubin','creatinine')
  AND l.labresultrevisedoffset <= 4320 AND l.labresult IS NOT NULL
GROUP BY l.patientunitstayid;
-- worst MAP in 72h
DROP TABLE IF EXISTS eicu_p3b_sofa_map;
CREATE TABLE eicu_p3b_sofa_map AS
SELECT v.patientunitstayid, MIN(v.systemicmean) AS map_min72
FROM vitalperiodic v
JOIN eicu_p3b_cand c ON c.patientunitstayid = v.patientunitstayid
WHERE v.systemicmean IS NOT NULL AND v.observationoffset <= 4320
GROUP BY v.patientunitstayid;
