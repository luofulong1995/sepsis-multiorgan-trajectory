-- P3b Step 4b: combined MAP (vitalaperiodic.noninvasivemean + vitalperiodic.systemicmean/pamean), 72h worst
DROP TABLE IF EXISTS eicu_p3b_sofa_map;
CREATE TABLE eicu_p3b_sofa_map AS
SELECT stay_id, MIN(map_val) AS map_min72
FROM (
  SELECT va.patientunitstayid AS stay_id, va.noninvasivemean AS map_val
  FROM vitalaperiodic va JOIN eicu_p3b_cand c ON c.patientunitstayid=va.patientunitstayid
  WHERE va.noninvasivemean IS NOT NULL AND va.observationoffset<=4320 AND va.noninvasivemean BETWEEN 20 AND 200
  UNION ALL
  SELECT v.patientunitstayid, v.systemicmean
  FROM vitalperiodic v JOIN eicu_p3b_cand c ON c.patientunitstayid=v.patientunitstayid
  WHERE v.systemicmean IS NOT NULL AND v.observationoffset<=4320 AND v.systemicmean BETWEEN 20 AND 200
  UNION ALL
  SELECT v.patientunitstayid, v.pamean
  FROM vitalperiodic v JOIN eicu_p3b_cand c ON c.patientunitstayid=v.patientunitstayid
  WHERE v.pamean IS NOT NULL AND v.observationoffset<=4320 AND v.pamean BETWEEN 20 AND 200
) t
GROUP BY stay_id;
