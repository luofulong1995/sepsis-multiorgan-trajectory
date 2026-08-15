"""
Figure 1. CONSORT flow diagram — MIMIC-IV and eICU cohorts.

Layout: Two parallel vertical flow diagrams (MIMIC left, eICU right).
Each box = a cohort step; side labels show exclusions at the arrow midpoint.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ---------------------------------------------------------------------------
# Journal style configuration
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 8,
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": False,
    "xtick.bottom": False,
    "ytick.left": False,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

# Colorblind-safe palette (Wong 2011, Nature Methods)
COL_INCLUDE    = "#0072B2"   # blue
COL_STEP_FILL  = "#F0F4F8"   # very light gray-blue
COL_STEP_EDGE  = "#2F4F6F"   # deep navy
COL_EXCLUDE    = "#D55E00"   # vermillion (orange-red, distinct from blue)
COL_ANALYSIS   = "#117733"   # green  (final analytic cohort)
COL_TEXT       = "#111111"

# ---------------------------------------------------------------------------
# Cohort data (from P1 and P3b reports)
# ---------------------------------------------------------------------------
mimic_nodes = [
    # (label, count, type)  type: 'start' | 'step' | 'analysis'
    ("MIMIC-IV sepsis-3 population\n(Sepsis-3 criteria)", "n = 41,295", "start"),
    ("First ICU stay of first\nhospitalization (patient-level)", "n = 27,881", "step"),
    ("ICU length of stay ≥ 24 hours", "n = 25,106", "step"),
    ("No CKD stage 5 or chronic dialysis\n(ICD-10 N18.5/N18.6/Z99.2)", "n = 24,101", "step"),
    ("Main analytic cohort\n(complete time-to-event)", "n = 24,098", "analysis"),
]
mimic_excl = [
    ("Excluded: not patient-level\nfirst ICU stay / hospitalization", "13,414"),
    ("Excluded: ICU stay < 24 h", "2,775"),
    ("Excluded: CKD stage 5 /\nchronic dialysis", "1,005"),
    ("Excluded: in-hospital death\nwith missing death time", "3"),
]

eicu_nodes = [
    ("All ICU stays in eICU-CRD", "n = 200,859", "start"),
    ("Patient-level first ICU stay\n(unique uniquepid)", "n = 139,367", "step"),
    ("Age ≥ 18 years", "n = 138,837", "step"),
    ("ICU length of stay ≥ 24 hours", "n = 94,888", "step"),
    ("Sepsis identified\n(ICD infection OR antibiotics + SOFA ≥ 2)", "n = 36,668", "step"),
    ("Main analytic cohort\n(no CKD5 or chronic dialysis)", "n = 34,003", "analysis"),
]
eicu_excl = [
    ("Excluded: not patient-level\nfirst ICU stay", "61,492"),
    ("Excluded: age < 18 years", "530"),
    ("Excluded: ICU stay < 24 h", "43,949"),
    ("Excluded: no sepsis\nidentification", "58,220"),
    ("Excluded: CKD stage 5 /\nchronic dialysis", "2,665"),
]

# ---------------------------------------------------------------------------
# Geometry (data coordinates, inches)
# ---------------------------------------------------------------------------
FIG_W = 8.5
FIG_H = 9.0

BOX_W  = 2.85
BOX_H  = 0.55

# X centers of each column
X_MIMIC = 2.55
X_EICU  = X_MIMIC + BOX_W + 0.45   # 2.55 + 2.85 + 0.45 = 5.85

# Y positions: top-down
Y_TOP    = FIG_H - 0.55
Y_STEP   = 0.85   # vertical spacing between box centers

# Side-exclusion geometry
# Exclusion label sits to the side of the arrow midpoint, with a small connector.
# MIMIC exclusions go to the LEFT; eICU exclusions go to the RIGHT.
EXCL_OFFSET_MIMIC = -1.65   # x distance from MIMIC box center to excl label
EXCL_OFFSET_EICU  = +1.65   # x distance from eICU box center to excl label

# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def node_fill(ntype):
    return {
        "start":    COL_INCLUDE,
        "step":     COL_STEP_FILL,
        "analysis": COL_ANALYSIS,
    }[ntype]


def node_edge(ntype):
    return {
        "start":    COL_INCLUDE,
        "step":     COL_STEP_EDGE,
        "analysis": COL_ANALYSIS,
    }[ntype]


def text_color(ntype):
    return "white" if ntype in ("start", "analysis") else COL_TEXT


def draw_node(ax, x, y, w, h, label, count, ntype):
    fc = node_fill(ntype)
    ec = node_edge(ntype)
    lw = 1.4 if ntype in ("start", "analysis") else 1.0
    box = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        fc=fc, ec=ec, lw=lw, zorder=2,
    )
    ax.add_patch(box)
    tc = text_color(ntype)
    ax.text(
        x, y + 0.10, label,
        ha="center", va="center",
        fontsize=7.4, color=tc, linespacing=1.2, zorder=3,
    )
    ax.text(
        x, y - 0.14, count,
        ha="center", va="center",
        fontsize=8.5, fontweight="bold", color=tc, zorder=3,
    )


def draw_arrow_down(ax, x, y_top, y_bottom):
    arrow = FancyArrowPatch(
        (x, y_top), (x, y_bottom),
        arrowstyle="-|>", mutation_scale=12, lw=1.1,
        color=COL_STEP_EDGE, zorder=1,
    )
    ax.add_patch(arrow)


def draw_exclusion(ax, x_arrow, y_arrow, x_label, text, count):
    """Horizontal connector from arrow midpoint to exclusion label."""
    # Tiny bracket pointing from arrow to side label
    connector = FancyArrowPatch(
        (x_arrow, y_arrow),
        (x_label, y_arrow),
        arrowstyle="-", lw=0.9,
        color=COL_EXCLUDE, linestyle=(0, (3, 2)), zorder=1,
    )
    ax.add_patch(connector)
    # Small dot on the arrow midpoint
    ax.plot(x_arrow, y_arrow, "o", color=COL_EXCLUDE, ms=4, zorder=2)
    # Exclusion text (italic, two-line max)
    ax.text(
        x_label + (0.06 if x_label > x_arrow else -0.06),
        y_arrow + 0.04,
        text,
        ha="left" if x_label > x_arrow else "right",
        va="center",
        fontsize=7.0, color=COL_EXCLUDE, style="italic", linespacing=1.2,
    )
    ax.text(
        x_label + (0.06 if x_label > x_arrow else -0.06),
        y_arrow - 0.12,
        f"−{count}",
        ha="left" if x_label > x_arrow else "right",
        va="center",
        fontsize=8.0, fontweight="bold", color=COL_EXCLUDE,
    )


def draw_column(ax, col_x, nodes, excl, title, excl_x_offset):
    n = len(nodes)
    y_positions = [Y_TOP - i * Y_STEP for i in range(n)]

    # Title
    ax.text(
        col_x, FIG_H - 0.10, title,
        ha="center", va="bottom",
        fontsize=11.5, fontweight="bold", color=COL_TEXT,
    )

    # Draw nodes
    for y, (label, count, ntype) in zip(y_positions, nodes):
        draw_node(ax, col_x, y, BOX_W, BOX_H, label, count, ntype)

    # Draw arrows
    for i in range(n - 1):
        draw_arrow_down(
            ax, col_x,
            y_positions[i] - BOX_H / 2,
            y_positions[i + 1] + BOX_H / 2,
        )

    # Draw side exclusions at midpoint of each down-arrow
    for i, (excl_text, excl_count) in enumerate(excl):
        if i + 1 < len(y_positions):
            y_arrow = (y_positions[i] + y_positions[i + 1]) / 2.0
        else:
            y_arrow = y_positions[i] - Y_STEP / 2.0
        x_label = col_x + excl_x_offset
        draw_exclusion(ax, col_x, y_arrow, x_label, excl_text, excl_count)


def main():
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.set_aspect("auto")
    ax.axis("off")

    draw_column(ax, X_MIMIC, mimic_nodes, mimic_excl,
                "MIMIC-IV  (derivation cohort)",
                EXCL_OFFSET_MIMIC)
    draw_column(ax, X_EICU, eicu_nodes, eicu_excl,
                "eICU-CRD  (external validation cohort)",
                EXCL_OFFSET_EICU)

    # Footnote
    fig.text(
        0.5, 0.025,
        "Sepsis-3 = suspected infection + SOFA ≥ 2. eICU uses an ICD-based or "
        "antibiotic-plus-SOFA approximation because no Sepsis-3 cohort is available.",
        ha="center", va="bottom",
        fontsize=7.5, color="#444444", style="italic", linespacing=1.3,
    )

    fig.savefig("figures/Figure1_consort.png", dpi=300,
                bbox_inches="tight", pad_inches=0.04)
    fig.savefig("figures/Figure1_consort.pdf",
                bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print("Saved Figure1_consort.png and Figure1_consort.pdf")


if __name__ == "__main__":
    main()