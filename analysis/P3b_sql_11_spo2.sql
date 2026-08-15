-- P3b Step 4d: min SpO2 in 72h per stay (for SF ratio resp SOFA component)
DROP TABLE IF EXISTS eicu_p3b_spo2;
CREATE TABLE eicu_p3b_spo2 AS
SELECT v.patientunitstayid, MIN(v.sao2) AS sao2_min72
FROM vitalperiodic v
JOIN eicu_p3b_cand c ON c.patientunitstayid = v.patientunitstayid
WHERE v.sao2 IS NOT NULL AND v.observationoffset<=4320 AND v.sao2 BETWEEN 1 AND 100
GROUP BY v.patientunitstayid;
