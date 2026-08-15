# Sepsis Multiorgan Trajectory Phenotypes and Intervention Heterogeneity

Analysis code for: "Multiorgan trajectory phenotypes in sepsis and heterogeneous associations of vasopressors, continuous renal replacement therapy, and fluid resuscitation with mortality: a MIMIC-IV cohort study with external validation in eICU"

## Study overview

Joint group-based trajectory modeling (GBTM) of the first-72-hour trajectories of four organ variables (platelet count, creatinine, lactate, bilirubin) identifies five sepsis phenotypes with differential 28-day mortality (7.7%-37.6%) and phenotype-specific associations of three ICU interventions (vasopressors, CRRT, fluid resuscitation) with mortality.

- Derivation: MIMIC-IV (n = 24,098 adults with Sepsis-3, first ICU admission)
- External validation: eICU-CRD (n = 34,003)
- Additional robustness: synthetic cohort generated with TimeGAN

## Repository structure

```
scripts/     Figure generation (make_figure1-5.py) and compute_traj_data.py
analysis/    Cohort construction, GBTM modeling (P1/P2), eICU validation SQL (P3b)
figures/     Manuscript figures (PNG preview; PDF/TIFF versions available on request)
```

## Data

- MIMIC-IV v2.x and eICU-CRD v2.0: publicly available from PhysioNet (https://physionet.org) after credentialed access.
- No patient-level data are included in this repository.

## Requirements

Python 3.10+; pandas, numpy, statsmodels (or analogous GBTM implementation), lifelines, scikit-learn, matplotlib.

## Reproducibility

- Fixed random seed 42 used throughout.
- All effect estimates reported with 95% confidence intervals computed by reparameterization (log-scale beta +/- z*SE, then exponentiated).
- Analysis scripts are provided as-is for transparency; database-specific schema paths (PostgreSQL) must be adapted to the local MIMIC-IV/eICU installation.

## License

Analysis code provided under the MIT License. Data use is governed by the PhysioNet Data Use Agreements.
