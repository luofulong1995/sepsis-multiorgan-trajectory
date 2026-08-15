"""
Compute model-based and observed trajectory means (MIMIC) and export to JSON.
Used by Figure 2 (multiorgan trajectories) and Figure 5 (eICU vs MIMIC).
"""
import json
import sys
import pickle
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, ".")  # for P2_gbtm_lib import


def main():
    # ---- Load GBTM model ----
    with open("P2_joint_gbtm.pkl", "rb") as f:
        m = pickle.load(f)
    mdl = m["models"][5]
    zmeta = m["zmeta"]

    VARS = ["plt", "cre", "lac", "bili"]
    K = 5
    T = np.array([0.0, 1.0, 2.0])
    X = np.column_stack([np.ones_like(T), T, T**2])  # design matrix (quadratic)

    # Compute mean_z[k, v, t]  from betas_[v][k, :]
    mean_z = np.zeros((K, len(VARS), len(T)))
    for v_idx, var in enumerate(VARS):
        beta = mdl.betas_[v_idx]   # (K, 3)
        for k in range(K):
            mean_z[k, v_idx, :] = X @ beta[k]

    # Inverse z-transform to raw units: value = exp(z * sd + mu) - 1
    def inv_z(z_arr, var):
        mu = zmeta[var]["mu"]
        sd = zmeta[var]["sd"]
        return np.exp(z_arr * sd + mu) - 1.0

    mean_raw = np.zeros_like(mean_z)
    for v_idx, var in enumerate(VARS):
        mean_raw[:, v_idx, :] = inv_z(mean_z[:, v_idx, :], var)

    # Compute SD bands using class-specific sigma[k]
    # bands_z = mean_z ± sigma  → back-transform
    sd_low_raw = np.zeros_like(mean_z)
    sd_high_raw = np.zeros_like(mean_z)
    for v_idx, var in enumerate(VARS):
        for k in range(K):
            sigma_z = mdl.sigmas_[v_idx][k]
            sd_low_raw[k, v_idx, :] = inv_z(mean_z[k, v_idx, :] - sigma_z, var)
            sd_high_raw[k, v_idx, :] = inv_z(mean_z[k, v_idx, :] + sigma_z, var)

    # ---- Map model indexing (0..4 = gbtm native) to manuscript k0..k4 ----
    # Renumber map from P2_summary.json:
    #   gbtm 2 → k0,  gbtm 4 → k1,  gbtm 1 → k2,  gbtm 0 → k3,  gbtm 3 → k4
    gbtm_to_k = {0: 3, 1: 2, 2: 0, 3: 4, 4: 1}

    # ---- Compute observed means from trajectory matrix ----
    df = pq.read_table("P2_traj_matrix.parquet").to_pandas()
    # df has z-scored cols; load labels
    lbl = pd.read_csv("P2_亚型分配.csv")
    df = df.merge(lbl[["stay_id", "subtype"]], on="stay_id", how="inner")
    # df['subtype'] is in renumbered manuscript form (k0..k4)

    # Compute observed mean per (subtype, timepoint) for each variable
    obs_raw = {}
    for v_idx, var in enumerate(VARS):
        for t in range(3):
            col_z = f"{var}_z_d{t}"
            # inverse transform: x = exp(z * sd + mu) - 1
            z = df[col_z].dropna()
            mu, sd = zmeta[var]["mu"], zmeta[var]["sd"]
            x = np.exp(z.values * sd + mu) - 1.0
            mask = df[col_z].notna().values
            df_sub = df.loc[mask, ["subtype"]].copy()
            df_sub["x"] = x
            means = df_sub.groupby("subtype")["x"].mean().reindex(range(5))
            obs_raw[(var, t)] = means.tolist()

    # ---- Load eICU model-based means (from P3b_eICU_亚型形状.csv) ----
    eicu_df = pd.read_csv("P3b_eICU_亚型形状.csv")
    # Build: eicu_raw[k][var] = [d0, d1, d2]
    eicu_raw = {k: {} for k in range(5)}
    for _, row in eicu_df.iterrows():
        k = int(row["subtype"].replace("k", "")) if isinstance(row["subtype"], str) else int(row["subtype"])
        var = row["var"]
        eicu_raw[k][var] = [row["eicu_d0"], row["eicu_d1"], row["eicu_d2"]]

    # ---- Build output dict ----
    out = {
        "vars": VARS,
        "days": T.tolist(),
        "gbtm_to_k": gbtm_to_k,           # map gbtm index → manuscript subtype
        "mean_raw": mean_raw.tolist(),     # shape (K, V, T) in gbtm native order
        "sd_low_raw": sd_low_raw.tolist(),
        "sd_high_raw": sd_high_raw.tolist(),
        "obs_raw": {f"{v}_{t}": obs_raw[(v, t)] for v in VARS for t in range(3)},
        "eicu_raw": {str(k): eicu_raw[k] for k in range(5)},
        "n_per": mdl.pi_.tolist() if hasattr(mdl, "pi_") else None,  # gbtm native
        "labels": {
            0: "Recovered (high platelet)",
            1: "Renal-dominant",
            2: "Stable/mild dysfunction",
            3: "Severe multi-organ failure",
            4: "Chronic thrombocytopenia",
        },
    }

    with open("scripts/traj_data.json", "w") as f:
        json.dump(out, f, indent=2, default=float)
    print("Saved scripts/traj_data.json")

    # Print summary
    for v_idx, var in enumerate(VARS):
        print(f"\n{var} (manuscript order k0..k4):")
        for k_manu in range(5):
            gbtm_idx = [g for g, k in gbtm_to_k.items() if k == k_manu][0]
            mvals = mean_raw[gbtm_idx, v_idx, :].round(1).tolist()
            obs_vals = [round(obs_raw[(var, t)][k_manu], 1) for t in range(3)]
            print(f"  k{k_manu}: model={mvals}  obs={obs_vals}")


if __name__ == "__main__":
    main()