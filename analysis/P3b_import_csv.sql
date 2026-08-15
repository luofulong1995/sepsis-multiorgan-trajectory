DROP TABLE IF EXISTS eicu_p3b_vaso_agg;
CREATE TABLE eicu_p3b_vaso_agg(patientunitstayid int, vaso_peak_ne_eq float8, vaso_duration_h float8, n_convertible int, n_rows int);
\copy eicu_p3b_vaso_agg FROM 'P3b_vaso_agg.csv' WITH CSV HEADER NULL 'None'
DROP TABLE IF EXISTS eicu_p3b_mv;
CREATE TABLE eicu_p3b_mv(patientunitstayid int, mv_any int, mv_duration_h float8);
\copy eicu_p3b_mv FROM 'P3b_mv_agg2.csv' WITH CSV HEADER
