"""
Figure 4. Forest plot of subtype-by-intervention associations.

Two-panel layout:
  (a) Within-subtype HRs (Panel C of Table 3) — adjusted hazard ratios
      for each intervention across the 5 phenotypes (5×5 grid).
  (b) Selected interaction HRs (Panel B of Table 3) — interaction HRs
      relative to the k0 stable/mild reference for the key findings.

All HRs are plotted on a log scale; the vertical reference line is at HR = 1.
"""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import ScalarFormatter, LogLocator, FixedLocator

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
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "legend.frameon": False,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

# Colorblind-safe palette (Wong)
COL = {
    0: "#0072B2",   # k0 blue
    1: "#D55E00",   # k1 vermillion
    2: "#009E73",   # k2 green
    3: "#CC79A7",   # k3 purple
    4: "#E69F00",   # k4 orange
}

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
within = pd.read_csv("P3_within_subtype_hr.csv")
inter  = pd.read_csv("P3_interaction_results.csv")
with open("P2_summary.json") as f:
    summary = json.load(f)
n_per = {int(k): v for k, v in summary["n_per"].items()}

INTERVENTIONS = [
    ("vaso_any",       "Vasopressor (any)"),
    ("vaso_peak",      "Vasopressor\nhigh dose (T3)"),
    ("crrt_any",       "CRRT (any)"),
    ("fluids_24h",     "Fluids 24 h\nhigh (T3 vs T1)"),
    ("fluids_72h",     "Fluids 72 h\nhigh (T3 vs T1)"),
]

LRT_P = {
    "vaso_any":  3.1e-7,
    "vaso_peak": 3.3e-6,
    "crrt_any":  5.4e-6,
    "fluids_24h": 1.1e-7,
    "fluids_72h": 1.1e-9,
}


def get_within(analysis, k):
    """Get the row for a within-subtype HR for given analysis & subtype."""
    sub = within[(within["analysis"] == analysis) & (within["subtype"] == f"k{k}")]
    if len(sub) == 0:
        return None
    row = sub.iloc[0]
    return row["HR_adj"], row["lo_adj"], row["hi_adj"], row["P_adj"]


def get_interaction(analysis, level, subtype_str):
    """Get the row for an interaction HR. level identifies the term (None for binary)."""
    sub = inter[(inter["analysis"] == analysis) & (inter["subtype"] == subtype_str)]
    if analysis == "vaso_any":
        sub = sub[sub["term"].str.contains("vaso_anyyes")]
    elif analysis == "vaso_peak":
        # level = 'T1(low)' or 'T2(mid)' or 'T3(high)'
        sub = sub[sub["term"].str.contains("vaso_peak_ne_t" + level, regex=False)]
    elif analysis == "crrt_any":
        sub = sub[sub["term"].str.contains("crrt_anyyes")]
    elif analysis == "fluids_24h":
        sub = sub[sub["term"].str.contains("fluids_24h_t" + level, regex=False)]
    elif analysis == "fluids_72h":
        sub = sub[sub["term"].str.contains("fluids_72h_t" + level, regex=False)]
    if len(sub) == 0:
        return None
    row = sub.iloc[0]
    return row["HR"], row["HR_low"], row["HR_high"], row["P"]


# ---------------------------------------------------------------------------
# Figure: 5 columns (interventions) × 5 rows (subtypes) + a thin interaction row at bottom
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(7.2, 9.2))
gs = GridSpec(
    2, 5,
    height_ratios=[5.0, 2.6],
    hspace=0.85, wspace=0.20,
    left=0.10, right=0.97, top=0.91, bottom=0.07,
)
axes = [fig.add_subplot(gs[0, i]) for i in range(5)]
ax_int = fig.add_subplot(gs[1, :])

# ====== Top panel (a): within-subtype HRs ======
y_positions = list(range(5))   # 0=k0 (bottom), 4=k4 (top)
y_labels = ["k0 Stable /\nmild", "k1 Chronic\nthrombocytopenia",
            "k2 Renal-\ndominant", "k3 Recovered", "k4 Severe MOF"]

# Common x range
XMIN, XMAX = 0.35, 9.0

for col_idx, (analysis, title) in enumerate(INTERVENTIONS):
    ax = axes[col_idx]

    for y, k in enumerate(y_positions):
        r = get_within(analysis, k)
        if r is None:
            continue
        hr, lo, hi, p = r
        if not (np.isfinite(hr) and np.isfinite(lo) and np.isfinite(hi)):
            continue
        ax.plot([lo, hi], [y, y], color=COL[k], lw=1.4, zorder=2)
        ax.plot(hr, y, "s", color=COL[k], mfc=COL[k], ms=7,
                mec="black", mew=0.4, zorder=3)
        # Annotate HR (95% CI) to the right of the box
        sig_marker = "*" if p < 0.05 else ""
        # Place the text to the right of the CI upper bound
        x_text = hi * 1.05
        ax.text(x_text, y + 0.18, f"{hr:.2f}{sig_marker}",
                ha="left", va="center",
                fontsize=7.0, color=COL[k], fontweight="bold")
        ax.text(x_text, y - 0.18, f"({lo:.2f}-{hi:.2f})",
                ha="left", va="center",
                fontsize=6.5, color="#444")

    ax.axvline(1.0, color="#888", lw=0.6, ls="--", zorder=1)
    ax.set_xscale("log")
    ax.set_xlim(XMIN, XMAX)
    # Use ScalarFormatter so labels are "0.5 1 2 4" not "5×10⁻¹"
    major_ticks = [0.5, 1, 2, 4]
    ax.set_xticks(major_ticks)
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=(2, 3, 5, 8), numticks=12))
    ax.xaxis.set_minor_formatter(plt.NullFormatter())
    ax.tick_params(axis="x", labelsize=7.5)
    ax.set_yticks(y_positions)
    if col_idx == 0:
        ax.set_yticklabels(y_labels, fontsize=7.5)
    else:
        ax.set_yticklabels([])
    ax.set_ylim(-0.7, 4.7)
    ax.set_title(title, fontsize=9, fontweight="bold", pad=4)
    ax.tick_params(axis="y", length=0)
    # Hide x-tick labels on top panel (use a shared axis label below instead)
    ax.tick_params(axis="x", labelbottom=False)

    # LRT P annotation (top-right)
    ax.text(
        0.97, 0.97,
        f"LRT P = {LRT_P[analysis]:.0e}",
        transform=ax.transAxes,
        ha="right", va="top",
        fontsize=6.8, color="#555",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#bbb", lw=0.4),
    )

# Shared y label
axes[0].set_ylabel("Subtype\n(D0-D1 early trajectory)",
                   fontsize=9, fontweight="bold")

# Shared x label below the top panel (in the hspace gap)
fig.text(0.5, 0.500,
         "Adjusted hazard ratio (95% CI) within subtype (log scale)",
         ha="center", va="bottom", fontsize=9, fontweight="bold")

# Show x-tick marks (but no labels) on the top panel for context
for ax in axes:
    ax.tick_params(axis="x", which="both", length=3)

# ====== Bottom panel (b): selected interaction HRs (Panel B) ======
key_interactions = [
    # (analysis, level, subtype, short_label)
    ("vaso_any",   "",           "k1", "Vaso (any)"),
    ("vaso_any",   "",           "k3", "Vaso (any)"),
    ("vaso_any",   "",           "k4", "Vaso (any)"),
    ("vaso_peak",  "T1(low)",    "k1", "Vaso T1 (low)"),
    ("vaso_peak",  "T2(mid)",    "k1", "Vaso T2 (mid)"),
    ("vaso_peak",  "T2(mid)",    "k3", "Vaso T2 (mid)"),
    ("crrt_any",   "",           "k2", "CRRT"),
    ("crrt_any",   "",           "k4", "CRRT"),
    ("fluids_24h", "T3(high)",   "k1", "Fluids 24 h T3"),
    ("fluids_24h", "T3(high)",   "k3", "Fluids 24 h T3"),
    ("fluids_72h", "T3(high)",   "k1", "Fluids 72 h T3"),
    ("fluids_72h", "T3(high)",   "k4", "Fluids 72 h T3"),
]

rows = []
for analysis, level, subtype_str, label in key_interactions:
    r = get_interaction(analysis, level, subtype_str)
    if r is None:
        continue
    rows.append((label, subtype_str, r, analysis))

# Order: by analysis, then by subtype k1..k4
analysis_order = ["vaso_any", "vaso_peak", "crrt_any", "fluids_24h", "fluids_72h"]
subtype_order = {"k0": 0, "k1": 1, "k2": 2, "k3": 3, "k4": 4}
rows.sort(key=lambda r: (analysis_order.index(r[3]),
                        subtype_order.get(r[1], 99)))

# Plot
n_rows = len(rows)
ax_int.axvline(1.0, color="#888", lw=0.6, ls="--", zorder=1)
ax_int.set_xscale("log")
ax_int.set_xlim(0.20, 4.0)
ax_int.set_xticks([0.25, 0.5, 1, 2, 4])
ax_int.xaxis.set_major_formatter(ScalarFormatter())
ax_int.xaxis.set_minor_locator(LogLocator(base=10.0, subs=(2, 3, 5, 8), numticks=12))
ax_int.xaxis.set_minor_formatter(plt.NullFormatter())
ax_int.tick_params(axis="x", labelsize=7.5)

y_ticks = []
for i, (label, subtype_str, (hr, lo, hi, p), _analysis) in enumerate(rows):
    k = int(subtype_str.replace("k", ""))
    ax_int.plot([lo, hi], [i, i], color=COL[k], lw=1.3, zorder=2)
    ax_int.plot(hr, i, "s", color=COL[k], ms=6.5, mec="black", mew=0.4, zorder=3)
    sig_marker = "*" if p < 0.05 else ""
    ax_int.text(hi * 1.08, i,
                f"HR {hr:.2f}{sig_marker} ({lo:.2f}-{hi:.2f})",
                ha="left", va="center",
                fontsize=7.5, color=COL[k])
    y_ticks.append(f"{label}  ×  {subtype_str}")

ax_int.set_yticks(range(n_rows))
ax_int.set_yticklabels(y_ticks, fontsize=7.5)
ax_int.set_ylim(-0.7, n_rows - 0.3)
ax_int.set_xlabel("Interaction hazard ratio vs. k0 reference (log scale)",
                  fontsize=9, fontweight="bold", labelpad=8)
ax_int.invert_yaxis()
ax_int.tick_params(axis="y", length=0)

# Panel labels (a, b) — bold, top-left of each panel
axes[0].text(-0.32, 1.10, "a", transform=axes[0].transAxes,
             fontsize=14, fontweight="bold")
ax_int.text(-0.10, 1.06, "b", transform=ax_int.transAxes,
            fontsize=14, fontweight="bold")

# Title for top of figure
fig.text(0.5, 0.985,
         "Subtype-by-intervention associations with 28-day mortality",
         ha="center", va="top", fontsize=11, fontweight="bold")

# Subtitle for panel (b)
fig.text(0.5, 0.450,
         "(b) Selected interaction HRs vs. k0 stable/mild reference (Panel B of Table 3)",
         ha="center", va="top", fontsize=8.5, color="#444", style="italic")

# Bottom annotation
fig.text(
    0.5, 0.015,
    "* P < 0.05.  Box = HR point estimate; horizontal line = 95% CI.  "
    "Models adjusted for age, sex, day-0 SOFA, Charlson comorbidity index, and infection site.",
    ha="center", va="bottom", fontsize=7.5, color="#444", style="italic",
)

fig.savefig("figures/Figure4_forest.png", dpi=300,
            bbox_inches="tight", pad_inches=0.05)
fig.savefig("figures/Figure4_forest.pdf",
            bbox_inches="tight", pad_inches=0.05)
plt.close(fig)
print(f"Saved Figure4_forest.png and .pdf ({n_rows} interaction rows)")