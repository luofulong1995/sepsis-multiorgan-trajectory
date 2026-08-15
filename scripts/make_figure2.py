"""
Figure 2. Multiorgan trajectory phenotypes.

2×2 panel grid showing model-based trajectory means (solid lines) with
±SD bands (light fill) and observed values (open circles) for the four
organ-function biomarkers across day 0–2 for the five phenotypes.
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ---------------------------------------------------------------------------
# Style configuration
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 8,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "legend.frameon": False,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

# Colorblind-safe palette (Wong 2011, Nature Methods)
COL = {
    0: "#0072B2",   # k0 Stable/mild — blue
    1: "#D55E00",   # k1 Chronic thrombocytopenia — vermillion
    2: "#009E73",   # k2 Renal-dominant — bluish green
    3: "#CC79A7",   # k3 Recovered — reddish purple
    4: "#E69F00",   # k4 Severe MOF — orange
}

LABELS = {
    0: "k0  Stable / mild",
    1: "k1  Chronic thrombocytopenia",
    2: "k2  Renal-dominant",
    3: "k3  Recovered (high platelet)",
    4: "k4  Severe multi-organ failure",
}

NS = {0: 6713, 1: 5898, 2: 3964, 3: 3828, 4: 3695}

VAR_LABELS = {
    "plt":  ("Platelet count",     "10⁹/L"),
    "cre":  ("Creatinine",         "mg/dL"),
    "lac":  ("Lactate",            "mmol/L"),
    "bili": ("Total bilirubin",    "mg/dL"),
}

# ---------------------------------------------------------------------------
# Load trajectory data
# ---------------------------------------------------------------------------
with open("scripts/traj_data.json") as f:
    TD = json.load(f)

VARS = TD["vars"]              # ['plt','cre','lac','bili']
DAYS = np.array(TD["days"])    # [0, 1, 2]
gbtm_to_k = {int(k): v for k, v in TD["gbtm_to_k"].items()}

# Reorder model-based means into manuscript k0..k4 order
# mean_raw is in gbtm native (0..4); gbtm_to_k[gbtm] = manuscript_k
mean_raw = np.array(TD["mean_raw"])   # (5, 4, 3)
sd_low   = np.array(TD["sd_low_raw"]) # (5, 4, 3)
sd_high  = np.array(TD["sd_high_raw"])
obs_raw  = TD["obs_raw"]              # dict var_t → list (k0..k4)


def get_model(var_idx, k_manu):
    """Get model mean / sd_low / sd_high for var_idx and manuscript subtype k."""
    gbtm_idx = [g for g, k in gbtm_to_k.items() if k == k_manu][0]
    return mean_raw[gbtm_idx, var_idx, :], sd_low[gbtm_idx, var_idx, :], sd_high[gbtm_idx, var_idx, :]


def get_obs(var_idx, k_manu, t):
    """Get observed mean for var_idx, manuscript subtype k, timepoint t."""
    var = VARS[var_idx]
    return obs_raw[f"{var}_{t}"][k_manu]


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.0))
axes = axes.flatten()

for v_idx, var in enumerate(VARS):
    ax = axes[v_idx]
    title, unit = VAR_LABELS[var]
    ax.set_title(f"{title}", loc="left", fontsize=10, fontweight="bold", pad=4)

    for k_manu in range(5):
        col = COL[k_manu]
        m, sl, sh = get_model(v_idx, k_manu)

        # SD band (model ± SD)
        ax.fill_between(DAYS, sl, sh, color=col, alpha=0.12, linewidth=0, zorder=1)

        # Solid model line
        ax.plot(DAYS, m, color=col, lw=1.6, zorder=3,
                label=LABELS[k_manu])

        # Observed means (open circles)
        obs_vals = [get_obs(v_idx, k_manu, t) for t in range(3)]
        ax.plot(DAYS, obs_vals, "o", mfc="white", mec=col,
                ms=6, mew=1.2, zorder=4)

    ax.set_xticks([0, 1, 2])
    ax.set_xlabel("ICU day")
    ax.set_ylabel(unit)
    # Pad x-limits a little
    ax.set_xlim(-0.15, 2.15)
    # Set y-axis to start near 0 if reasonable (not always for bilirubin)
    ymin, ymax = ax.get_ylim()
    if ymin > 0:
        ax.set_ylim(bottom=0)
    ax.tick_params(axis="both", which="major", labelsize=8)

# ---------------------------------------------------------------------------
# Single shared legend at bottom
# ---------------------------------------------------------------------------
handles, labels = axes[0].get_legend_handles_labels()
# Replace lines with custom legend handles that show n in the label
legend_handles = []
for k_manu in range(5):
    line = Line2D([0], [0], color=COL[k_manu], lw=2.0,
                  label=f"{LABELS[k_manu]}  (n = {NS[k_manu]:,})")
    legend_handles.append(line)

fig.legend(
    handles=legend_handles,
    loc="lower center", ncol=5,
    bbox_to_anchor=(0.5, -0.01),
    fontsize=8, frameon=False, handlelength=2.2,
    columnspacing=1.0,
)

# Title at top
fig.suptitle(
    "Multiorgan trajectory phenotypes (K = 5, joint GBTM, MIMIC-IV, n = 24,098)",
    fontsize=11, fontweight="bold", y=1.00,
)

# Legend explanation
fig.text(
    0.5, -0.10,
    "Solid lines: model-implied trajectory means (inverse-z transform); shaded bands: model ± SD.\n"
    "Open circles: observed per-timepoint means (subject to informative truncation).",
    ha="center", va="top",
    fontsize=7.5, color="#444", style="italic", linespacing=1.3,
)

fig.tight_layout(rect=[0, 0.05, 1, 0.97])
fig.savefig("figures/Figure2_trajectories.png", dpi=300,
            bbox_inches="tight", pad_inches=0.05)
fig.savefig("figures/Figure2_trajectories.pdf",
            bbox_inches="tight", pad_inches=0.05)
plt.close(fig)
print("Saved Figure2_trajectories.png and .pdf")