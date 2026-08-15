-- P3b Step 9: fluids aggregate (intake/output) from io_daily
DROP TABLE IF EXISTS eicu_p3b_fluids;
CREATE TABLE eicu_p3b_fluids AS
SELECT patientunitstayid,
  SUM(CASE WHEN day=0 THEN intake_ml ELSE 0 END) AS intake_d0,
  SUM(CASE WHEN day<=2 THEN intake_ml ELSE 0 END) AS intake_72h,
  SUM(CASE WHEN day=0 THEN output_ml ELSE 0 END) AS output_d0,
  SUM(CASE WHEN day<=2 THEN output_ml ELSE 0 END) AS output_72h
FROM eicu_p3b_io_daily GROUP BY patientunitstayid;
