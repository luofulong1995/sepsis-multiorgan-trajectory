-- P3b Step 8: assemble SOFA component scores (first-72h worst) + sepsis criteria flags
DROP TABLE IF EXISTS eicu_p3b_sofa;
CREATE TABLE eicu_p3b_sofa AS
WITH u AS (SELECT patientunitstayid, MIN(urine_ml) AS urine_min_day FROM eicu_p3b_urine_daily GROUP BY patientunitstayid)
SELECT c.patientunitstayid AS stay_id,
  sl.plt_min72, sl.bili_max72, sl.cre_max72,
  sm.map_min72, su.urine_72h, u.urine_min_day, sf.fio2_max_pct, sp.sao2_min72, sg.gcs_min,
  CASE WHEN v.patientunitstayid IS NOT NULL THEN 1 ELSE 0 END AS vaso_any,
  -- component scores
  CASE WHEN sl.plt_min72 IS NULL THEN NULL
       WHEN sl.plt_min72 >= 150 THEN 0 WHEN sl.plt_min72 < 20 THEN 4
       WHEN sl.plt_min72 < 50 THEN 3 WHEN sl.plt_min72 < 100 THEN 2 ELSE 1 END AS sofa_coag,
  CASE WHEN sl.bili_max72 IS NULL THEN NULL
       WHEN sl.bili_max72 < 1.2 THEN 0 WHEN sl.bili_max72 >= 12 THEN 4
       WHEN sl.bili_max72 >= 6 THEN 3 WHEN sl.bili_max72 >= 2 THEN 2 ELSE 1 END AS sofa_liver,
  CASE WHEN sl.cre_max72 IS NULL THEN NULL
       WHEN sl.cre_max72 < 1.2 THEN 0 WHEN sl.cre_max72 >= 5 THEN 4
       WHEN sl.cre_max72 >= 3.5 THEN 3 WHEN sl.cre_max72 >= 2 THEN 2 ELSE 1 END AS sofa_cre,
  CASE WHEN u.urine_min_day IS NULL THEN NULL
       WHEN u.urine_min_day < 200 THEN 2 WHEN u.urine_min_day < 500 THEN 1 ELSE 0 END AS sofa_urine,
  CASE WHEN sm.map_min72 IS NULL THEN NULL WHEN sm.map_min72 < 70 THEN 1 ELSE 0 END AS sofa_map,
  CASE WHEN v.patientunitstayid IS NOT NULL THEN 2 ELSE 0 END AS sofa_vaso,
  -- respiration via SF ratio (SpO2/FiO2), FiO2 default 21% if missing
  CASE WHEN sp.sao2_min72 IS NULL THEN NULL
       WHEN (sp.sao2_min72 / NULLIF(COALESCE(sf.fio2_max_pct,21)/100.0,0)) >= 315 THEN 0
       WHEN (sp.sao2_min72 / (COALESCE(sf.fio2_max_pct,21)/100.0)) < 144 THEN 4
       WHEN (sp.sao2_min72 / (COALESCE(sf.fio2_max_pct,21)/100.0)) < 175 THEN 3
       WHEN (sp.sao2_min72 / (COALESCE(sf.fio2_max_pct,21)/100.0)) < 235 THEN 2
       ELSE 1 END AS sofa_resp,
  CASE WHEN sg.gcs_min IS NULL THEN NULL
       WHEN sg.gcs_min >= 15 THEN 0 WHEN sg.gcs_min < 6 THEN 4
       WHEN sg.gcs_min < 10 THEN 3 WHEN sg.gcs_min < 13 THEN 2 ELSE 1 END AS sofa_cns
FROM eicu_p3b_cand c
LEFT JOIN eicu_p3b_sofa_lab sl ON sl.patientunitstayid=c.patientunitstayid
LEFT JOIN eicu_p3b_sofa_map sm ON sm.stay_id=c.patientunitstayid
LEFT JOIN eicu_p3b_urine su ON su.patientunitstayid=c.patientunitstayid
LEFT JOIN u ON u.patientunitstayid=c.patientunitstayid
LEFT JOIN eicu_p3b_fio2 sf ON sf.patientunitstayid=c.patientunitstayid
LEFT JOIN eicu_p3b_spo2 sp ON sp.patientunitstayid=c.patientunitstayid
LEFT JOIN eicu_p3b_gcs sg ON sg.patientunitstayid=c.patientunitstayid
LEFT JOIN eicu_p3b_vaso v ON v.patientunitstayid=c.patientunitstayid;
