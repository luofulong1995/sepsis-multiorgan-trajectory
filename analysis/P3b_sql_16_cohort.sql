-- P3b Step 10: FINAL eICU sepsis cohort (aligned with MIMIC P1)
-- sepsis = ICD infection code OR (antibiotic AND approx SOFA>=2); then exclude CKD5/chronic dialysis
DROP TABLE IF EXISTS eicu_sepsis_cohort;
CREATE TABLE eicu_sepsis_cohort AS
WITH s AS (
  SELECT s.*,
    COALESCE(s.sofa_coag,0)+COALESCE(s.sofa_liver,0)
      +GREATEST(COALESCE(s.sofa_cre,0),COALESCE(s.sofa_urine,0))
      +GREATEST(COALESCE(s.sofa_map,0),COALESCE(s.sofa_vaso,0))
      +COALESCE(s.sofa_resp,0)+COALESCE(s.sofa_cns,0) AS sofa_total
  FROM eicu_p3b_sofa s
)
SELECT c.patientunitstayid AS stay_id,
       c.uniquepid,
       c.age_num AS age,
       c.gender,
       c.admissionweight AS weight_kg,
       c.hospitalid,
       c.unittype,
       c.unitdischargeoffset AS los_icu_min,
       round(c.unitdischargeoffset/60.0,2) AS los_icu_h,
       c.hospitaldischargeoffset AS los_hosp_min,
       c.hospitaldischargeyear,
       -- sepsis criteria
       CASE WHEN icd.patientunitstayid IS NOT NULL THEN 1 ELSE 0 END AS sepsis_icd,
       CASE WHEN abx.patientunitstayid IS NOT NULL THEN 1 ELSE 0 END AS sepsis_abx,
       s.sofa_total,
       s.sofa_coag, s.sofa_liver, s.sofa_cre, s.sofa_urine, s.sofa_map, s.sofa_vaso, s.sofa_resp, s.sofa_cns,
       s.plt_min72, s.bili_max72, s.cre_max72, s.map_min72, s.urine_72h, s.urine_min_day, s.fio2_max_pct, s.sao2_min72, s.gcs_min,
       -- interventions
       s.vaso_any,
       va.vaso_peak_ne_eq, va.vaso_duration_h,
       CASE WHEN cr.patientunitstayid IS NOT NULL THEN 1 ELSE 0 END AS crrt_any,
       CASE WHEN ih.patientunitstayid IS NOT NULL THEN 1 ELSE 0 END AS ihd_any,
       mv.mv_any, mv.mv_duration_h,
       fl.intake_d0 AS fluids_24h_ml, fl.intake_72h AS fluids_72h_ml,
       round(fl.intake_d0/NULLIF(c.admissionweight,0),1) AS fluids_24h_mlkg,
       round(fl.intake_72h/NULLIF(c.admissionweight,0),1) AS fluids_72h_mlkg,
       fl.output_d0 AS output_24h_ml, fl.output_72h AS output_72h_ml,
       -- outcomes
       CASE WHEN c.hospitaldischargestatus='Expired' THEN 1 ELSE 0 END AS death_hosp,
       CASE WHEN c.unitdischargestatus='Expired' THEN 1 ELSE 0 END AS death_icu,
       CASE WHEN c.hospitaldischargestatus='Expired' AND c.hospitaldischargeoffset <= 40320 THEN 1 ELSE 0 END AS death_28d_proxy,
       c.hospitaldischargestatus
FROM eicu_p3b_cand c
JOIN s ON s.stay_id = c.patientunitstayid
LEFT JOIN eicu_p3b_icd_sepsis icd ON icd.patientunitstayid=c.patientunitstayid
LEFT JOIN eicu_p3b_abx abx ON abx.patientunitstayid=c.patientunitstayid
LEFT JOIN eicu_p3b_vaso_agg va ON va.patientunitstayid=c.patientunitstayid
LEFT JOIN eicu_p3b_crrt cr ON cr.patientunitstayid=c.patientunitstayid
LEFT JOIN eicu_p3b_ihd ih ON ih.patientunitstayid=c.patientunitstayid
LEFT JOIN eicu_p3b_mv mv ON mv.patientunitstayid=c.patientunitstayid
LEFT JOIN eicu_p3b_fluids fl ON fl.patientunitstayid=c.patientunitstayid
LEFT JOIN eicu_p3b_ckd ckd ON ckd.patientunitstayid=c.patientunitstayid
WHERE (icd.patientunitstayid IS NOT NULL OR (abx.patientunitstayid IS NOT NULL AND s.sofa_total >= 2))
  AND ckd.patientunitstayid IS NULL;
