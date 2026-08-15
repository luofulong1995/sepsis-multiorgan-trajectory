"""
Figure 3. Kaplan–Meier 28-day survival curves by phenotype.

- 5 KM curves (k0–k4) on the survival probability axis
- Risk table (No. at risk) below the plot
- Log-rank statistic + P value annotation
- 28-day survival % annotation per curve
- Median survival indicator for severe phenotype (k4, median <28)
"""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from lifelines import KaplanMeierFitter
from lifelines.statistics import multivariate_logrank_test

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

# Colorblind-safe palette (Wong)
COL = {
    0: "#0072B2",
    1: "#D55E00",
    2: "#009E73",
    3: "#CC79A7",
    4: "#E69F00",
}
LABELS = {
    0: "k0  Stable / mild",
    1: "k1  Chronic thrombocytopenia",
    2: "k2  Renal-dominant",
    3: "k3  Recovered (high platelet)",
    4: "k4  Severe MOF",
}

# ---------------------------------------------------------------------------
# Load data and compute KM
# ---------------------------------------------------------------------------
df = pd.read_csv("P2_亚型分配.csv")
# surv_time = days from ICU admission (admin censoring at 28 d)
# event = 1 if 28-day death else 0
df = df.dropna(subset=["surv_time", "event"])
df = df[df["surv_time"] > 0]

with open("P2_summary.json") as f:
    summary = json.load(f)

km_end = summary["km_end_by_subtype"]     # 28-day survival probability
mortality_28d = summary["mortality_28d"]   # % mortality per k
logrank_chi2 = summary["logrank_chi2"]
n_per = summary["n_per"]

# ---------------------------------------------------------------------------
# Build figure: main plot (top) + risk table (bottom)
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(7.2, 5.6))
gs = GridSpec(
    2, 1,
    height_ratios=[3.0, 0.9],
    hspace=0.05,
    left=0.10, right=0.97, top=0.93, bottom=0.13,
)
ax = fig.add_subplot(gs[0])
ax_risk = fig.add_subplot(gs[1], sharex=ax)

# Use manuscript-published log-rank statistic for consistency with Table/Results text
logrank_chi2_val = logrank_chi2  # from P2_summary.json (matches R survdiff value)
logrank_p_str = "P < 0.001"

# Compute KM and plot
kmf = KaplanMeierFitter()
risk_times = [0, 7, 14, 21, 28]
risk_table = {}

for k in range(5):
    sub = df[df["subtype"] == k]
    kmf.fit(
        durations=sub["surv_time"],
        event_observed=sub["event"],
        label=LABELS[k],
    )
    kmf.plot_survival_function(
        ax=ax,
        color=COL[k],
        lw=1.6,
        ci_show=False,
        censor_styles={"ms": 4, "mew": 0.8},
        show_censors=True,
    )
    # Risk counts at standard times
    risk_table[k] = [int(((sub["surv_time"] >= t)).sum()) for t in risk_times]
    # 28-day survival annotation near right side of curve
    surv_pct = km_end[str(k)] * 100
    ax.annotate(
        f"{surv_pct:.1f}%",
        xy=(28, km_end[str(k)]),
        xytext=(29.6, km_end[str(k)]),
        fontsize=7.5, color=COL[k], fontweight="bold",
        va="center",
        arrowprops=dict(arrowstyle="-", color=COL[k], lw=0.6),
    )

# Median survival marker (only k4 likely has median <28)
for k in range(5):
    sub = df[df["subtype"] == k]
    kmf_k = KaplanMeierFitter().fit(
        durations=sub["surv_time"], event_observed=sub["event"]
    )
    med = kmf_k.median_survival_time_
    if pd.notna(med) and med < 28:
        # Draw horizontal 50% line + vertical at median
        ax.axhline(0.5, color="#888", lw=0.5, ls="--", zorder=0)
        ax.plot([med, med], [0.5, kmf_k.predict(med)], color=COL[k],
                lw=0.8, ls="--", zorder=1)
        ax.text(med + 0.3, 0.52, f"median {med:.1f} d", color=COL[k],
                fontsize=7, va="bottom")

# Log-rank statistic
logrank = multivariate_logrank_test(
    df["surv_time"], df["subtype"], df["event"]
)
# Use manuscript-published statistic for consistency
logrank_chi2_val = logrank_chi2  # from P2_summary.json (matches R survdiff value)
logrank_p_str = "P < 0.001"

ax.text(
    0.02, 0.18,
    f"Log-rank χ² = {logrank_chi2_val:,.1f} (df = 4)\n{logrank_p_str}",
    transform=ax.transAxes,
    ha="left", va="bottom",
    fontsize=8.5, linespacing=1.4,
    bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#888", lw=0.5, alpha=0.9),
)

# Axis settings
ax.set_xlim(0, 28.5)
ax.set_ylim(0.5, 1.005)
ax.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
ax.set_yticklabels([f"{y:.1f}" for y in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]])
ax.set_ylabel("Survival probability")
ax.set_xlabel("")  # x-label will go on risk table axis
ax.grid(False)

# Hide tick labels on the main x-axis (they're shared with the risk table)
plt.setp(ax.get_xticklabels(), visible=False)

# ---------------------------------------------------------------------------
# Risk table (No. at risk)
# ---------------------------------------------------------------------------
# Order: top row = k4 (highest-risk at top), bottom = k0
risk_order = [4, 3, 2, 1, 0]
y_positions = list(range(len(risk_order)))
for y, k in zip(y_positions, risk_order):
    ax_risk.text(
        -1.5, y, f"{LABELS[k].split()[0]}",  # "k0", "k1", ...
        ha="right", va="center", fontsize=7.5, fontweight="bold",
        color=COL[k], transform=ax_risk.transData,
    )
    for t_idx, t in enumerate(risk_times):
        n_at_risk = risk_table[k][t_idx]
        ax_risk.text(
            t, y, f"{n_at_risk:,}",
            ha="center", va="center", fontsize=7.5,
            color="#222", transform=ax_risk.transData,
        )

ax_risk.set_ylim(-0.6, len(risk_order) - 0.4)
ax_risk.set_yticks([])
ax_risk.set_xticks(risk_times)
ax_risk.set_xticklabels([str(t) for t in risk_times], fontsize=8)
ax_risk.set_xlim(ax.get_xlim())
ax_risk.set_xlabel("Days from ICU admission")
ax_risk.spines["top"].set_visible(False)
ax_risk.spines["right"].set_visible(False)
ax_risk.spines["left"].set_visible(False)
ax_risk.tick_params(axis="x", direction="in")

# Header for risk table
ax_risk.text(
    -1.5, len(risk_order) - 0.2,
    "Subtype",
    ha="right", va="bottom", fontsize=8, fontweight="bold",
    transform=ax_risk.transData,
)
ax_risk.text(
    (risk_times[0] + risk_times[-1]) / 2, len(risk_order) - 0.2,
    "No. at risk",
    ha="center", va="bottom", fontsize=8, fontweight="bold",
    transform=ax_risk.transData,
)

# Caption-style subtitle (above main plot)
fig.suptitle(
    "Kaplan–Meier 28-day survival by trajectory phenotype",
    fontsize=11, fontweight="bold", y=0.97,
)
fig.text(
    0.5, 0.945,
    "MIMIC-IV, n = 24,098 (administrative censoring at day 28)",
    ha="center", va="top", fontsize=8.5, color="#444", style="italic",
)

# Legend (custom, with n)
handles = [
    Line2D([0], [0], color=COL[k], lw=1.8,
           label=f"{LABELS[k]}  (n = {n_per[str(k)]:,})")
    for k in range(5)
]
fig.legend(
    handles=handles, loc="lower center",
    bbox_to_anchor=(0.5, 0.005), ncol=5,
    fontsize=7.5, frameon=False, handlelength=2.0,
    columnspacing=0.8,
)

fig.savefig("figures/Figure3_km.png", dpi=300,
            bbox_inches="tight", pad_inches=0.05)
fig.savefig("figures/Figure3_km.pdf",
            bbox_inches="tight", pad_inches=0.05)
plt.close(fig)
print("Saved Figure3_km.png and .pdf")