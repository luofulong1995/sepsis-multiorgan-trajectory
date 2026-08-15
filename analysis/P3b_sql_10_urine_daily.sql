-- P3b Step 5c: urine daily per day bucket
DROP TABLE IF EXISTS eicu_p3b_urine_daily;
CREATE TABLE eicu_p3b_urine_daily AS
SELECT io.patientunitstayid,
  CASE WHEN io.intakeoutputoffset<1440 THEN 0 WHEN io.intakeoutputoffset<2880 THEN 1 ELSE 2 END AS day,
  SUM(io.cellvaluenumeric) AS urine_ml
FROM intakeoutput io
JOIN eicu_p3b_cand c ON c.patientunitstayid=io.patientunitstayid
WHERE io.intakeoutputoffset<=4320 AND io.cellvaluenumeric>0
  AND (lower(io.celllabel) LIKE '%urine%' OR lower(io.celllabel) LIKE '%foley%'
       OR lower(io.celllabel) LIKE '%void%' OR lower(io.celllabel) LIKE '%indwelling%'
       OR lower(io.celllabel) LIKE '%urethral%')
  AND lower(io.celllabel) NOT LIKE '%count%' AND lower(io.celllabel) NOT LIKE '%occurrence%'
GROUP BY io.patientunitstayid,
  CASE WHEN io.intakeoutputoffset<1440 THEN 0 WHEN io.intakeoutputoffset<2880 THEN 1 ELSE 2 END;
