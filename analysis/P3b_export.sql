\copy (SELECT * FROM eicu_sepsis_cohort ORDER BY stay_id) TO 'P3b_eICU_cohort.csv' WITH CSV HEADER
\copy (SELECT * FROM eicu_sepsis_daily_wide ORDER BY stay_id) TO 'P3b_eICU_daily_wide.csv' WITH CSV HEADER
