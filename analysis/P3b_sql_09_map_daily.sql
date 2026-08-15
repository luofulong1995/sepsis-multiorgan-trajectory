-- P3b Step 5b: MAP daily med/worst per day bucket (combined sources)
DROP TABLE IF EXISTS eicu_p3b_map_daily;
CREATE TABLE eicu_p3b_map_daily AS
WITH map72 AS (
  SELECT stay_id, day, map_val::numeric AS mv FROM (
    SELECT va.patientunitstayid AS stay_id,
      CASE WHEN va.observationoffset<1440 THEN 0 WHEN va.observationoffset<2880 THEN 1 ELSE 2 END AS day,
      va.noninvasivemean AS map_val
    FROM vitalaperiodic va JOIN eicu_p3b_cand c ON c.patientunitstayid=va.patientunitstayid
    WHERE va.noninvasivemean IS NOT NULL AND va.observationoffset<=4320 AND va.noninvasivemean BETWEEN 20 AND 200
    UNION ALL
    SELECT v.patientunitstayid,
      CASE WHEN v.observationoffset<1440 THEN 0 WHEN v.observationoffset<2880 THEN 1 ELSE 2 END,
      v.systemicmean
    FROM vitalperiodic v JOIN eicu_p3b_cand c ON c.patientunitstayid=v.patientunitstayid
    WHERE v.systemicmean IS NOT NULL AND v.observationoffset<=4320 AND v.systemicmean BETWEEN 20 AND 200
    UNION ALL
    SELECT v.patientunitstayid,
      CASE WHEN v.observationoffset<1440 THEN 0 WHEN v.observationoffset<2880 THEN 1 ELSE 2 END,
      v.pamean
    FROM vitalperiodic v JOIN eicu_p3b_cand c ON c.patientunitstayid=v.patientunitstayid
    WHERE v.pamean IS NOT NULL AND v.observationoffset<=4320 AND v.pamean BETWEEN 20 AND 200
  ) x
)
SELECT stay_id, day,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY mv) AS map_med,
  MIN(mv) AS map_worst
FROM map72
GROUP BY stay_id, day;
