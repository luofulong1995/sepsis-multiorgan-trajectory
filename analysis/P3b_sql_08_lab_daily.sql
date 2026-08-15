-- P3b Step 5a: lab daily last/median/min/max per day bucket (D0<1440, D1<2880, D2<4320)
DROP TABLE IF EXISTS eicu_p3b_lab_daily;
CREATE TABLE eicu_p3b_lab_daily AS
WITH lab72 AS (
  SELECT l.patientunitstayid, l.labname, l.labresult, l.labresultrevisedoffset,
    CASE WHEN l.labresultrevisedoffset < 1440 THEN 0
         WHEN l.labresultrevisedoffset < 2880 THEN 1 ELSE 2 END AS day
  FROM lab l
  JOIN eicu_p3b_cand c ON c.patientunitstayid = l.patientunitstayid
  WHERE l.labname IN ('platelets x 1000','WBC x 1000','creatinine','lactate','total bilirubin')
    AND l.labresultrevisedoffset <= 4320 AND l.labresult IS NOT NULL
),
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY patientunitstayid, labname, day ORDER BY labresultrevisedoffset DESC) AS rn
  FROM lab72
)
SELECT patientunitstayid, labname, day,
  MAX(labresult) FILTER (WHERE rn=1) AS last_val,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY labresult) AS med_val,
  MIN(labresult) AS min_val,
  MAX(labresult) AS max_val
FROM ranked
GROUP BY patientunitstayid, labname, day;
