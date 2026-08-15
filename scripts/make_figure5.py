"""
Figure 5. eICU vs. MIMIC trajectory comparison.

For each of the four organ-function variables (platelet, creatinine, lactate,
bilirubin), plot the model-based trajectory means across ICU day 0–2 for the
five phenotypes, with MIMIC-IV and eICU-CRD overlaid.

Illustrates: close replication of k2 (renal) and k4 (severe MOF);
partial replication of k1; boundary confusion between k0 and k3.
"""
import json
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Style
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

# Colorblind-safe palette (Wong)
COL = {
    0: "#0072B2",   # k0 Stable — blue
    1: "#D55E00",   # k1 Chronic thrombocytopenia — vermillion
    2: "#009E73",   # k2 Renal — bluish green
    3: "#CC79A7",   # k3 Recovered — reddish purple
    4: "#E69F00",   # k4 Severe MOF — orange
}

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
with open("scripts/traj_data.json") as f:
    TD = json.load(f)

VARS = TD["vars"]                      # ['plt', 'cre', 'lac', 'bili']
DAYS = np.array(TD["days"])            # [0, 1, 2]
gbtm_to_k = {int(k): v for k, v in TD["gbtm_to_k"].items()}
mean_raw = np.array(TD["mean_raw"])    # (5, 4, 3) in gbtm native order
eicu_raw = TD["eicu_raw"]              # dict k0..k4 → {var:[d0,d1,d2]}


def get_model_manu(var_idx, k_manu):
    gbtm_idx = [g for g, k in gbtm_to_k.items() if k == k_manu][0]
    return mean_raw[gbtm_idx, var_idx, :]


VAR_LABELS = {
    "plt":  ("Platelet count",     "10⁹/L"),
    "cre":  ("Creatinine",         "mg/dL"),
    "lac":  ("Lactate",            "mmol/L"),
    "bili": ("Total bilirubin",    "mg/dL"),
}

LABELS = {
    0: "k0 Stable / mild",
    1: "k1 Chronic thrombocytopenia",
    2: "k2 Renal-dominant",
    3: "k3 Recovered",
    4: "k4 Severe MOF",
}

# ---------------------------------------------------------------------------
# Figure: 2x2 panel grid (one per variable)
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.6))
axes = axes.flatten()

for v_idx, var in enumerate(VARS):
    ax = axes[v_idx]
    title, unit = VAR_LABELS[var]
    ax.set_title(title, loc="left", fontsize=10, fontweight="bold", pad=4)

    for k_manu in range(5):
        col = COL[k_manu]
        m_mimic = get_model_manu(v_idx, k_manu)
        m_eicu  = eicu_raw[str(k_manu)][var]

        # MIMIC: solid line, full opacity
        ax.plot(DAYS, m_mimic, "-", color=col, lw=1.8, zorder=3,
                label=LABELS[k_manu])
        # eICU: dashed line, lighter
        ax.plot(DAYS, m_eicu, "--", color=col, lw=1.4, alpha=0.75,
                zorder=2,
                marker="s", ms=4, mec=col, mfc=col)

    ax.set_xticks([0, 1, 2])
    ax.set_xlabel("ICU day")
    ax.set_ylabel(unit)
    ax.set_xlim(-0.15, 2.15)
    # y-min at 0 for visual consistency
    ymin, ymax = ax.get_ylim()
    if ymin > 0:
        ax.set_ylim(bottom=0)
    ax.tick_params(axis="both", which="major", labelsize=8)

# Panel labels (a, b, c, d)
panel_labels = ["a", "b", "c", "d"]
for i, ax in enumerate(axes):
    ax.text(-0.12, 1.05, panel_labels[i], transform=ax.transAxes,
            fontsize=11, fontweight="bold")

# ---------------------------------------------------------------------------
# Legend (combined subtype + database)
# ---------------------------------------------------------------------------
from matplotlib.lines import Line2D
legend_handles = []
for k_manu in range(5):
    legend_handles.append(
        Line2D([0], [0], color=COL[k_manu], lw=0, marker="o",
               mfc=COL[k_manu], ms=8, label=LABELS[k_manu])
    )
# Add database style legend
legend_handles.append(Line2D([0], [0], color="gray", lw=0,
                             label="—"))
legend_handles.append(Line2D([0], [0], color="gray", lw=2.0,
                             linestyle="-", label="MIMIC-IV (solid)"))
legend_handles.append(Line2D([0], [0], color="gray", lw=1.4,
                             linestyle="--", marker="s", ms=4,
                             label="eICU-CRD (dashed)"))

fig.legend(
    handles=legend_handles,
    loc="lower center", ncol=7,
    bbox_to_anchor=(0.5, -0.03),
    fontsize=7.5, frameon=False,
    handlelength=1.6, handletextpad=0.6, columnspacing=0.8,
)

# Figure title
fig.suptitle(
    "Cross-database trajectory comparison: eICU-CRD vs. MIMIC-IV",
    fontsize=11, fontweight="bold", y=1.00,
)
fig.text(
    0.5, 0.97,
    "Model-based trajectory means (original units, inverse-z transform).  "
    "ARI = 0.42 (mod. agreement); diagonal = 62.9%.",
    ha="center", va="top", fontsize=8.5, color="#444", style="italic",
)

# Bottom annotation
fig.text(
    0.5, -0.10,
    "k2 (renal) and k4 (severe MOF) reproduced closely; k1 (chronic thrombocytopenia) partially "
    "reproduced (low platelet without elevated bilirubin); k0/k3 boundary confused.",
    ha="center", va="top", fontsize=7.5, color="#444", style="italic",
    wrap=True,
)

fig.tight_layout(rect=[0, 0.07, 1, 0.95])
fig.savefig("figures/Figure5_eicu.png", dpi=300,
            bbox_inches="tight", pad_inches=0.05)
fig.savefig("figures/Figure5_eicu.pdf",
            bbox_inches="tight", pad_inches=0.05)
plt.close(fig)
print("Saved Figure5_eicu.png and .pdf")