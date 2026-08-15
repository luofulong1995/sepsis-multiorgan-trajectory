# -*- coding: utf-8 -*-
"""P1 Table 1: 28-day survivors vs deaths (Wilcoxon rank-sum / chi-square)."""
import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_csv("C:/Users/12751/WorkBuddy/脓毒症多器官轨迹/P1_cohort_table1.csv")

grp0 = df[df["death_28d"] == 0]
grp1 = df[df["death_28d"] == 1]
n0, n1 = len(grp0), len(grp1)

def fmt_p(p):
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"

def cont(var, g0, g1):
    a = g0[var].dropna()
    b = g1[var].dropna()
    med0, q1_0, q3_0 = a.median(), a.quantile(0.25), a.quantile(0.75)
    med1, q1_1, q3_1 = b.median(), b.quantile(0.25), b.quantile(0.75)
    if var in ("age",):
        m0, s0 = a.mean(), a.std(ddof=1)
        m1, s1 = b.mean(), b.std(ddof=1)
        s0 = f"{m0:.1f} ± {s0:.1f}"
        s1 = f"{m1:.1f} ± {s1:.1f}"
    else:
        s0 = f"{med0:.1f} [{q1_0:.1f}, {q3_0:.1f}]"
        s1 = f"{med1:.1f} [{q1_1:.1f}, {q3_1:.1f}]"
    p = stats.mannwhitneyu(a, b, alternative="two-sided").pvalue
    return s0, s1, fmt_p(p)

def cat(var, g0, g1, levels):
    out = []
    for lev in levels:
        a = int((g0[var] == lev).sum())
        b = int((g1[var] == lev).sum())
        pa = 100.0 * a / n0
        pb = 100.0 * b / n1
        out.append(f"{lev}: {a} ({pa:.1f}%)")
        out.append(f"{lev}: {b} ({pb:.1f}%)")
    tab = pd.crosstab(df[var], df["death_28d"])
    chi2, p, _, _ = stats.chi2_contingency(tab)
    return out, fmt_p(p)

lines = []
lines.append("# Table 1 基线特征（按 28 天死亡分层）")
lines.append("")
lines.append(f"- 总 N = {len(df)}；28 天存活 n={n0}（{(100*n0/len(df)):.1f}%）；28 天死亡 n={n1}（{(100*n1/len(df)):.1f}%）")
lines.append("- 连续变量：均值 ± SD（age）或中位数 [IQR]；分类变量：n (%)")
lines.append("- P 值：连续 = Mann-Whitney U；分类 = chi-square")
lines.append("")
lines.append("| 变量 | 存活 (n=%d) | 死亡 (n=%d) | P 值 |" % (n0, n1))
lines.append("|---|---|---|---|")

# continuous
for var, lab in [("age", "年龄 (岁)"), ("charlson_comorbidity_index", "Charlson 评分"),
                 ("sofa_worst", "SOFA 评分（最差值）"), ("los", "ICU 住院时长 (天)"),
                 ("vaso_duration_h", "血管活性药时长 (h)"), ("fluids_24h_ml", "24h 液体量 (mL)"),
                 ("fluids_72h_ml", "72h 液体量 (mL)"), ("weight", "体重 (kg)")]:
    s0, s1, p = cont(var, grp0, grp1)
    lines.append(f"| {lab} | {s0} | {s1} | {p} |")

# categorical
catout, p = cat("gender", grp0, grp1, ["M", "F"])
lines.append(f"| 性别 男/女 | {catout[0]} / {catout[2]} | {catout[1]} / {catout[3]} | {p} |")
for var, lab, levs in [("vaso_any", "血管活性药使用", [1, 0]),
                       ("crrt_any", "CRRT 使用", [1, 0]),
                       ("mv_any", "机械通气", [1, 0])]:
    c0 = f"{int((grp0[var]==1).sum())} ({100.0*(grp0[var]==1).sum()/n0:.1f}%)"
    c1 = f"{int((grp1[var]==1).sum())} ({100.0*(grp1[var]==1).sum()/n1:.1f}%)"
    tab = pd.crosstab(df[var], df["death_28d"])
    chi2, pv, _, _ = stats.chi2_contingency(tab)
    lines.append(f"| {lab} | {c0} | {c1} | {fmt_p(pv)} |")

# care unit (top units)
top_units = df["first_careunit"].value_counts().head(6).index.tolist()
for u in top_units:
    a = int((grp0["first_careunit"] == u).sum())
    b = int((grp1["first_careunit"] == u).sum())
    lines.append(f"| 入住科室: {u} | {a} ({100.0*a/n0:.1f}%) | {b} ({100.0*b/n1:.1f}%) | — |")

out = "\n".join(lines)
with open("C:/Users/12751/WorkBuddy/脓毒症多器官轨迹/P1_table1.md", "w", encoding="utf-8") as f:
    f.write(out)
print("TABLE1_WRITTEN")
