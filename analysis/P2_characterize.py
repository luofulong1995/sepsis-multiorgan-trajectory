# -*- coding: utf-8 -*-
"""
P2_characterize.py — 亚型表征 + KM + 轨迹图 + 敏感性分析 + 报告
依赖 P2_gbtm.py 输出 (P2_joint_labels.csv / P2_joint_gbtm.pkl / P2_model_selection.csv)
"""
import pandas as pd, numpy as np, os, pickle, sys, json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = r"C:\Users\12751\WorkBuddy\脓毒症多器官轨迹"
sys.path.insert(0, OUT)
from P2_gbtm_lib import MultiTrajGBTM

VARS = ["plt", "cre", "lac", "bili"]
VAR_LABEL = {"plt": "Platelet (10^9/L)", "cre": "Creatinine (mg/dL)",
             "lac": "Lactate (mmol/L)", "bili": "Bilirubin (mg/dL)"}
TIMES = [0, 1, 2]

# ---------------- 加载 ----------------
cohort = pd.read_parquet(f"{OUT}\\P2_cohort.parquet")
wide = pd.read_parquet(f"{OUT}\\P2_daily_wide.parquet")
df = cohort.merge(wide, on="stay_id", how="inner")
labs = pd.read_csv(f"{OUT}\\P2_joint_labels.csv")
sel = pd.read_csv(f"{OUT}\\P2_model_selection.csv")
kml_df = pd.read_csv(f"{OUT}\\P2_kml_results.csv")
with open(f"{OUT}\\P2_joint_gbtm.pkl", "rb") as f:
    pkl = pickle.load(f)
best_K = int(pkl["best_K"])
print("best_K =", best_K)

# dischtime 映射（C1：KM 使用住院出院时间而非 ICU 出科时间）
disc = pd.read_csv(f"{OUT}\\P2_admissions_dischtime.csv",
                   parse_dates=["dischtime"])

data = df.merge(labs, on="stay_id", how="inner")
data = data.merge(disc[["stay_id", "dischtime"]], on="stay_id", how="left")
# C1: 剔除 3 例 death_hosp=1 且 deathtime NULL 的歧义患者（无 28 天事件时间），
#     全分析统一 n=24,098；P1 遗留 Minor 处理。
_ambig = data["death_hosp"].eq(1) & data["deathtime"].isna()
print("剔除 death_hosp=1 且 deathtime NULL 例数 =", int(_ambig.sum()))
data = data[~_ambig].copy()
# 统一数值类型（PostgreSQL numeric -> Decimal 需转 float）
for _c in ["age", "charlson_comorbidity_index", "sofa_worst", "los", "vaso_peak_ne",
           "vaso_duration_h", "fluids_24h_mlkg", "fluids_72h_mlkg"]:
    data[_c] = pd.to_numeric(data[_c], errors="coerce")

# 按类别样本量排序重编号（大→小），保证亚型编号稳定
cnt = data["subtype"].value_counts().sort_values(ascending=False)
map_old = {k: i for i, k in enumerate(cnt.index)}
data["subtype"] = data["subtype"].map(map_old)
K = int(data["subtype"].nunique())
# order[k] = 重编号 k 对应的原始类别号（cnt.index 按样本量降序）
order = cnt.index.tolist()
# 重编号映射表（M3：显式记录旧k ↔ 新k）
renumber_map = pd.DataFrame({"gbtm_class_id": order,
                             "renumbered_subtype": range(K),
                             "n": [cnt.iloc[i] for i in range(K)]})
renumber_map.to_csv(f"{OUT}\\P2_renumber_map.csv", index=False, encoding="utf-8-sig")
print("subtype counts:", data["subtype"].value_counts().sort_index().to_dict())
print("renumber map:\n", renumber_map.to_string(index=False))

# ---------------- 1. 亚型特征表 ----------------
feat_vars = {
    "age": "numeric", "charlson_comorbidity_index": "numeric", "sofa_worst": "numeric",
    "los": "numeric", "vaso_peak_ne": "numeric", "vaso_duration_h": "numeric",
    "fluids_24h_mlkg": "numeric", "fluids_72h_mlkg": "numeric",
    "gender": "categorical", "vaso_any": "categorical", "crrt_any": "categorical",
    "mv_any": "categorical", "death_28d": "categorical",
}
FEAT_LABEL = {
    "age": "Age (years)", "charlson_comorbidity_index": "Charlson index",
    "sofa_worst": "SOFA (worst)", "los": "ICU LOS (days)",
    "vaso_peak_ne": "Vaso peak NE eq (mcg/kg/min)", "vaso_duration_h": "Vaso duration (h)",
    "fluids_24h_mlkg": "Fluids 24h (mL/kg)", "fluids_72h_mlkg": "Fluids 72h (mL/kg)",
    "gender": "Male sex", "vaso_any": "Vasopressor use", "crrt_any": "CRRT use",
    "mv_any": "Mechanical ventilation", "death_28d": "28-day death",
}

from scipy import stats

def norm_test(x):
    if len(x) < 3:
        return False
    try:
        w, p = stats.shapiro(x)
        return p > 0.05
    except Exception:
        return False


def _mc_chi2_p(tbl, n_sim=10000, seed=1):
    """2xK 列联表 Monte Carlo 置换检验（Fisher 精确扩展，m1）：
    固定行列边际，零假设下随机置换行标签，计算卡方统计量经验分布。"""
    rng = np.random.default_rng(seed)
    obs, _ = stats.chi2_contingency(tbl)
    n = int(tbl.values.sum())
    col_levels = list(tbl.columns)
    row_tot = tbl.sum(axis=1).to_numpy()
    # 长格式：每行样本的列标签
    long_labels = []
    for col in col_levels:
        long_labels += [col] * int(tbl[col].sum())
    long_labels = np.array(long_labels)
    counts = np.array([len(long_labels[long_labels == c]) for c in col_levels])
    # 置换行标签（保持每亚组行总数），计算卡方
    cnt_sim = 0
    for _ in range(n_sim):
        perm = rng.permutation(long_labels)
        sim_tbl = np.zeros(tbl.shape)
        idx = 0
        for r in range(tbl.shape[0]):
            seg = perm[idx:idx + int(row_tot[r])]
            idx += int(row_tot[r])
            for j, c in enumerate(col_levels):
                sim_tbl[r, j] = np.sum(seg == c)
        chi2_sim, *_ = stats.chi2_contingency(sim_tbl)
        if chi2_sim >= obs:
            cnt_sim += 1
    return (cnt_sim + 1) / (n_sim + 1)

rows = []
for v, typ in feat_vars.items():
    if typ == "numeric":
        groups = [pd.to_numeric(data.loc[data["subtype"] == k, v], errors="coerce").dropna()
                  for k in range(K)]
    else:
        groups = [data.loc[data["subtype"] == k, v].dropna() for k in range(K)]
    if typ == "numeric":
        # 正态性：任一亚组 Shapiro p<0.05 即用非参数（m2：亚组级检验，非合并分布）
        is_norm = all(norm_test(g.sample(min(2000, len(g)), random_state=1)) for g in groups)
        if is_norm:
            means = [g.mean() for g in groups]
            sds = [g.std() for g in groups]
            stat_str = " | ".join(f"{m:.1f}±{s:.1f}" for m, s in zip(means, sds))
            F, p = stats.f_oneway(*groups)
            method = "ANOVA"
        else:
            meds = [g.median() for g in groups]
            iqrs = [g.quantile(.75) - g.quantile(.25) for g in groups]
            stat_str = " | ".join(f"{m:.1f}[{i:.1f}]" for m, i in zip(meds, iqrs))
            H, p = stats.kruskal(*groups)
            method = "Kruskal-Wallis"
        pv = p
    else:
        # 分类变量 n (%)：以排序末水平的计数呈现（如性别 'M'→男性）
        g_sizes = np.array([len(g) for g in groups])
        if len(g_sizes) == 0 or (g_sizes == 0).any():
            ref = sorted(data[v].dropna().unique())[0] if data[v].nunique() else None
        else:
            # 参考水平：对二元变量取"非首水平"更常见；这里取水平1（如 M）
            levs = sorted(data[v].dropna().unique())
            ref = levs[-1] if len(levs) >= 2 else levs[0]
        counts = [int((g == ref).sum()) for g in groups]
        pct = [n / gs * 100 if gs else np.nan for n, gs in zip(counts, g_sizes)]
        stat_str = " | ".join(f"{n} ({pc:.1f}%)" for n, pc in zip(counts, pct))
        tbl = pd.crosstab(data["subtype"], data[v])
        # m1: 期望频数 <5 或任一格 <5 时用 Monte Carlo 置换检验（2xK Fisher 扩展）
        chi2, p, dof, exp = stats.chi2_contingency(tbl)
        if (exp < 5).any() or (tbl < 5).any().any():
            p = _mc_chi2_p(tbl, n_sim=10000, seed=1)
            method = "Chi-square (MC exact)"
        else:
            method = "Chi-square"
        pv = p
    rows.append(dict(variable=v, label=FEAT_LABEL[v], type=typ,
                     stat=stat_str, method=method, p=pv,
                     p_str="<0.001" if pv < 0.001 else f"{pv:.3f}"))
feat_df = pd.DataFrame(rows)
feat_df.to_csv(f"{OUT}\\P2_subtype_features.csv", index=False, encoding="utf-8-sig")
print("\n===== 亚型特征表 =====")
print(feat_df.to_string(index=False))

# 每类样本量 + 亚型标签
n_per = data["subtype"].value_counts().sort_index()

# ---------------- 2. 亚型命名（基于轨迹模式：水平 + 方向） ----------------
# 阈值（原始单位，基于临床参考范围）
TH = {
    "plt": dict(low=150.0, dir="declining", drop=-0.15),   # 血小板减少 <150
    "cre": dict(high=1.2, dir="worsening", rise=0.15),      # 肌酐升高 >1.2
    "lac": dict(high=2.0, dir="worsening", rise=0.15),      # 乳酸升高 >2.0
    "bili": dict(high=1.2, dir="worsening", rise=0.15),     # 胆红素升高 >1.2
}
trajZ = pkl["trajZ"]          # var_idx -> (K,3) z 空间（原类别号）
traj_raw = pkl["traj_raw"]    # var_idx -> (K,3) 原始单位（原类别号）

def organ_status(v, r):
    """返回 (状态词, 说明)"""
    d0, d1, d2 = r
    if v == "plt":
        declining = (d2 - d0) / max(d0, 1e-9) < TH[v]["drop"]
        low = d0 < TH[v]["low"]
        if declining and low:
            return "declining_thrombocytopenia", f"{d0:.0f}->{d2:.0f} low+falling"
        if declining:
            return "declining", f"{d0:.0f}->{d2:.0f} falling"
        if low:
            return "low_stable", f"{d0:.0f}->{d2:.0f} low-stable"
        return "normal", f"{d0:.0f}->{d2:.0f}"
    else:
        rising = (d2 - d0) / max(d0, 1e-9) > TH[v]["rise"]
        high = d0 > TH[v]["high"]
        if rising and high:
            return "worsening_elevated", f"{d0:.1f}->{d2:.1f} high+rising"
        if rising:
            return "rising", f"{d0:.1f}->{d2:.1f} rising"
        if high:
            return "elevated_stable", f"{d0:.1f}->{d2:.1f} high-stable"
        return "normal", f"{d0:.1f}->{d2:.1f}"

print("\n===== 亚型器官状态（原始单位） =====")
status_all = {}
for k in range(K):
    orig_k = order[k]
    st = {}
    for vi, v in enumerate(VARS):
        st[v] = organ_status(v, traj_raw[v][orig_k])
    status_all[k] = st
    print(f"k{k} (n={n_per.get(k,0)}): " + "; ".join(f"{v}={st[v][0]}[{st[v][1]}]" for v in VARS))

def assign_name(k):
    st = status_all[k]
    bad = [v for v in VARS if st[v][0] in ("declining_thrombocytopenia", "declining",
                                           "worsening_elevated", "rising",
                                           "elevated_stable", "low_stable")]
    # 严重：乳酸/胆红素高（代谢+肝）或肌酐高（肾）+ 血小板低
    severe_metabolic = (st["lac"][0] in ("worsening_elevated", "elevated_stable")) and \
                       (st["bili"][0] in ("worsening_elevated", "elevated_stable"))
    renal = st["cre"][0] in ("worsening_elevated", "elevated_stable", "rising")
    coag = st["plt"][0] in ("declining_thrombocytopenia", "declining", "low_stable")
    # 恢复型：血小板高（反应性血小板增多，提示恢复）且无其他受累
    high_plt_recovery = (traj_raw["plt"][order[k]][0] >= 300) and (len(bad) == 0)
    if severe_metabolic and renal and coag:
        return "Severe multi-organ failure"
    if severe_metabolic and renal:
        return "Metabolic+renal failure"
    if severe_metabolic and coag:
        return "Metabolic+coagulopathy"
    if renal and coag:
        return "Renal+coagulopathy"
    if renal:
        return "Renal-dominant"
    if coag:
        # M5: 慢性血小板减少背景（急性凝血病"dominant"误导），改为中性描述
        return "Chronic thrombocytopenia profile"
    if severe_metabolic:
        return "Metabolic-dominant"
    if high_plt_recovery:
        return "Recovered (high platelet)"
    if len(bad) == 0:
        return "Stable/mild dysfunction"
    return "Moderate dysfunction"

subtype_names = {k: assign_name(k) for k in range(K)}
print("\n===== 亚型命名 =====")
for k in range(K):
    print(f"k{k}: {subtype_names[k]}  n={n_per.get(k,0)}")

# ---------------- 3. 轨迹轮廓图（原始单位） ----------------
fig, axes = plt.subplots(2, 2, figsize=(11, 8))
colors = plt.cm.tab10(np.linspace(0, 1, K))
best_model = pkl["models"][int(pkl["best_K"])]
zmeta_all = pkl["zmeta"]
for vi, v in enumerate(VARS):
    ax = axes[vi // 2][vi % 2]
    for k in range(K):
        orig_k = order[k]
        # 模型预测的 z 空间均值（trajZ）+ 类内 SD
        zmeta = zmeta_all[v]
        z_mu = pkl["trajZ"][vi][orig_k]                # (T,) z 空间轨迹
        sigma = np.sqrt(best_model.sigmas_[vi][orig_k]) # z 空间类内 SD
        # 反变换到原始单位（线性化在反 log1p 处）
        fz = z_mu * zmeta["sd"] + zmeta["mu"]          # log1p 空间
        df = zmeta["sd"]
        f_lo = np.expm1(fz - df * sigma)
        f_hi = np.expm1(fz + df * sigma)
        # 观测均值（受信息性截尾影响）
        sub = data[data["subtype"] == k]
        obs_means = []
        for t in TIMES:
            c = f"{v}_last_d{t}"
            obs_means.append(sub[c].dropna().mean())
        # 模型均值实线 + SE 阴影 + 观测均值空心点
        ax.plot(TIMES, np.expm1(fz), "-", color=colors[k], lw=2.2,
                label=f"{subtype_names[k]} (n={len(sub)})")
        ax.fill_between(TIMES, f_lo, f_hi, color=colors[k], alpha=0.18)
        ax.plot(TIMES, obs_means, "o", color=colors[k], ms=4, mfc="white",
                mec=colors[k], mew=1.5)
    ax.set_title(VAR_LABEL[v], fontsize=11)
    ax.set_xlabel("Day (D0=ICU day 0)")
    ax.set_ylabel("Value")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="best")
fig.suptitle(f"Multi-organ trajectory subtypes (K={K}, GBTM joint model)\n"
             f"solid line=model-implied trajectory; bands=model ±SD (log1p+z); "
             f"open circles=observed per-timepoint mean (subject to informative truncation)",
             fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(f"{OUT}\\P2_亚型轨迹图.png", dpi=300)
fig.savefig(f"{OUT}\\P2_subtype_trajectories.png", dpi=300)
plt.close(fig)
print("\nsaved P2_亚型轨迹图.png")

# ---------------- 4. KM 曲线（28 天死亡，C1 修正口径） ----------------
# C1 修正说明：28 天固定观察窗采用管理性删失（administrative censoring at day 28）。
#   - 死亡患者（death_28d=1）：事件时间 = min(deathtime − intime, 28)
#   - 非死亡患者（death_28d=0）：删失于第 28 天（death_28d 提供完整 28 天随访，
#     经 MIMIC death 记录/SSA 链接可确定其 28 天存活状态）
# 不采用"住院出院时间删失"：出院患者是已知 28 天存活者（death_28d=0），提前删失
# 会引入信息性删失，导致 KM 系统性低估 28 天生存（实测差 12-17pp，见诊断）。
# 歧义 3 例已在加载时剔除（death_hosp=1 且 deathtime NULL）。

def compute_surv_time(row):
    if row["death_28d"] == 1 and pd.notna(row["deathtime"]):
        return min((row["deathtime"] - row["intime"]).total_seconds() / 86400.0, 28.0)
    else:
        return 28.0   # 非死亡：管理性删失在第 28 天

data["surv_time"] = data.apply(compute_surv_time, axis=1)
data["event"] = data["death_28d"].astype(int)
# 极小时间保护（理论上不需要，保留以防极端）
data.loc[data["surv_time"] <= 0, "surv_time"] = 0.1

def km_curve(times, events):
    """返回 (t_unique, S, n_risk, n_event)"""
    order = np.argsort(times)
    ts = np.array(times)[order]
    ev = np.array(events)[order]
    u = np.unique(ts)
    S = 1.0
    out_t = [0.0]; out_S = [1.0]
    n_at_risk = len(ts)
    for ti in u:
        idx = ts == ti
        d = ev[idx].sum()
        n = idx.sum()
        if n_at_risk > 0 and d > 0:
            S *= (1 - d / n_at_risk)
        out_t.append(ti)
        out_S.append(S)
        n_at_risk -= n
    return np.array(out_t), np.array(out_S)

def logrank(groups_times, groups_events):
    """两两/多组 log-rank 卡方"""
    # 合并唯一事件时间
    all_t = np.unique(np.concatenate(groups_times))
    all_t = all_t[all_t > 0]
    O = np.zeros(len(groups_times)); E = np.zeros(len(groups_times)); V = 0.0
    for ti in all_t:
        n_j = np.array([np.sum(gt >= ti) for gt in groups_times])
        d_j = np.array([np.sum((gt == ti) & (ev == 1)) for gt, ev in zip(groups_times, groups_events)])
        n = n_j.sum(); d = d_j.sum()
        if n > 1 and d > 0 and d < n:
            O += d_j
            E += d_j * n_j / n
            V += d * (n - d) * (n - n_j) * n_j / (n * n * (n - 1))
    # 统计量（多组卡方近似）
    chi2 = np.sum((O - E) ** 2 / np.maximum(E, 1e-9))
    df = len(groups_times) - 1
    p = stats.chi2.sf(chi2, df)
    return chi2, p, O, E

gt = [data.loc[data["subtype"] == k, "surv_time"].to_numpy() for k in range(K)]
ge = [data.loc[data["subtype"] == k, "event"].to_numpy() for k in range(K)]
chi2_lr, p_lr, O, E = logrank(gt, ge)
p_lr_str = "<2.2e-308" if p_lr < 2.2e-308 else f"{p_lr:.2e}"  # m3: 浮点下溢
print(f"log-rank chi2={chi2_lr:.1f}, df={K-1}, P={p_lr_str}")

# 自洽性核对（C1）：KM 终值应与 1−death_28d 接近
km_end_by_subtype = {}
for k in range(K):
    sub = data[data["subtype"] == k]
    true_surv = 1 - sub["death_28d"].mean()
    tt, SS = km_curve(sub["surv_time"].to_numpy(), sub["event"].to_numpy())
    km_end = SS[-1]
    km_end_by_subtype[str(k)] = float(km_end)
    print(f"k{k}: 真28d生存={true_surv*100:.1f}%  KM终值={km_end*100:.1f}%  "
          f"差={abs(true_surv-km_end)*100:.2f}pp")

fig, ax = plt.subplots(figsize=(8, 6))
for k in range(K):
    tt, SS = km_curve(gt[k], ge[k])
    ax.step(tt, SS, where="post", color=colors[k], lw=2,
            label=f"{subtype_names[k]} (n={len(gt[k])})")
ax.set_xlabel("Days from ICU admission")
ax.set_ylabel("Survival probability")
ax.set_title(f"28-day all-cause survival by trajectory subtype\n"
             f"(administrative censoring at day 28; log-rank P={p_lr_str})")
ax.grid(alpha=0.3)
ax.legend(fontsize=8)
ax.set_xlim(0, 28)
fig.tight_layout()
fig.savefig(f"{OUT}\\P2_KM曲线.png", dpi=300)
fig.savefig(f"{OUT}\\P2_km_curve.png", dpi=300)
plt.close(fig)
print(f"saved P2_KM曲线.png (log-rank chi2={chi2_lr:.1f}, P={p_lr:.3g})")

# 28d 死亡率按亚型
mort = data.groupby("subtype")["death_28d"].agg(["sum", "count"])
mort["pct"] = mort["sum"] / mort["count"] * 100
print("\n===== 28d 死亡率按亚型 =====")
print(mort.to_string())

# ---------------- 5. 敏感性：替代口径 (worst/median) 与子集 ----------------
# 可经环境变量 SKIP_SENS=1 跳过敏感性（隔离执行 P2_sensitivity_only.py，
# 规避长进程被杀；否则在完整运行时执行 n_starts=10 的 4 项重拟合）
import os as _os
SKIP_SENS = _os.environ.get("SKIP_SENS", "0") == "1"
from sklearn.metrics import adjusted_rand_score

def build_Z(df2, metric):
    mat = {}
    for v in VARS:
        cols = [f"{v}_{metric}_{t}" for t in ["d0", "d1", "d2"]]
        m = df2[cols].to_numpy(float)
        mat[v] = np.log1p(m)
    Z = {}
    for v in VARS:
        m = mat[v]
        Z[v] = (m - np.nanmean(m)) / np.nanstd(m)
    return [Z[v] for v in VARS]

sens = {}
if not SKIP_SENS:
    # a) worst 口径
    print("sens: worst 口径 拟合中…", flush=True)
    Yw = build_Z(data, "worst")
    mw = MultiTrajGBTM(K=K, degree=2, n_starts=10, seed=K, max_iter=400).fit(Yw, [TIMES] * 4)
    lw = mw.labels()
    sens["worst"] = dict(ARI=adjusted_rand_score(data["subtype"], lw))
    print("sens: worst 完成", flush=True)
    # b) median 口径
    print("sens: median 口径 拟合中…", flush=True)
    Ym = build_Z(data, "med")
    mm = MultiTrajGBTM(K=K, degree=2, n_starts=10, seed=K, max_iter=400).fit(Ym, [TIMES] * 4)
    lm = mm.labels()
    sens["median"] = dict(ARI=adjusted_rand_score(data["subtype"], lm))
    print("sens: median 完成", flush=True)
    # c) 4变量均>=2时间点子集 (n=5360)
    print("sens: complete_ge2 子集 拟合中…", flush=True)
    mask2 = np.ones(len(data), dtype=bool)
    for v in VARS:
        cols = [f"{v}_last_{t}" for t in ["d0", "d1", "d2"]]
        mask2 &= data[cols].notna().sum(axis=1).ge(2)
    sub = data[mask2].copy()
    Ysub = build_Z(sub, "last")
    msub = MultiTrajGBTM(K=K, degree=2, n_starts=10, seed=K, max_iter=400).fit(Ysub, [TIMES] * 4)
    ls_ = msub.labels()
    sens["complete_ge2"] = dict(ARI=adjusted_rand_score(sub["subtype"], ls_), n=int(mask2.sum()))
    print("sens: complete_ge2 完成", flush=True)
    # d) 敏感性队列（剔除转院, n=21681）
    print("sens: no_transfer 队列 拟合中…", flush=True)
    transfer_locs = ["ACUTE HOSPITAL", "OTHER FACILITY", "CHRONIC/LONG TERM ACUTE CARE"]
    nsens = ~data["discharge_location"].isin(transfer_locs)
    ds = data[nsens].copy()
    Ys = build_Z(ds, "last")
    ms = MultiTrajGBTM(K=K, degree=2, n_starts=10, seed=K, max_iter=400).fit(Ys, [TIMES] * 4)
    lss = ms.labels()
    sens["no_transfer"] = dict(ARI=adjusted_rand_score(ds["subtype"], lss), n=int(nsens.sum()))
    print("sens: no_transfer 完成", flush=True)
else:
    print("SKIP_SENS=1：敏感性由 P2_sensitivity_only.py 隔离执行", flush=True)
sens_df = pd.DataFrame(sens).T if sens else pd.DataFrame()
if not sens_df.empty:
    sens_df.to_csv(f"{OUT}\\P2_sensitivity.csv", encoding="utf-8-sig")
print("\n===== 敏感性 ARI（与主模型标签一致性） =====")
print(sens_df.to_string())

# ---------------- 5b. 边界患者敏感性（m8：subtype_prob<0.6） ----------------
print("\n===== 边界患者敏感性（subtype_prob<0.6） =====")
n_bound = int((data["subtype_prob"] < 0.6).sum())
print(f"subtype_prob<0.6 边界患者 n={n_bound} ({n_bound/len(data)*100:.2f}%)")
clean = data[data["subtype_prob"] >= 0.6].copy()
mort_clean = clean.groupby("subtype")["death_28d"].agg(["sum", "count"])
mort_clean["pct"] = mort_clean["sum"] / mort_clean["count"] * 100
print("剔除边界后 28d 死亡率：")
print(mort_clean.to_string())
# 与全样本死亡率对比
mort_cmp = pd.DataFrame({
    "subtype": range(K),
    "n_all": [int((data["subtype"] == k).sum()) for k in range(K)],
    "mort_all_pct": [mort.loc[k, "pct"] for k in range(K)],
    "n_clean": [int((clean["subtype"] == k).sum()) for k in range(K)],
    "mort_clean_pct": [mort_clean.loc[k, "pct"] if k in mort_clean.index else np.nan for k in range(K)],
})
mort_cmp.to_csv(f"{OUT}\\P2_boundary_sensitivity.csv", index=False, encoding="utf-8-sig")
print(mort_cmp.to_string(index=False))

# 逐亚型 5th/10th percentile of prob（m8 参考）
prob_pct = data.groupby("subtype")["subtype_prob"].quantile([0.05, 0.10, 0.50]).unstack()
prob_pct.columns = ["p5", "p10", "p50"]
print("亚型 subtype_prob 百分位：")
print(prob_pct.round(3).to_string())

# n_iter 汇总（m5）
n_iter_all = {str(kk): int(pkl["models"][kk].n_iter_) for kk in sorted(pkl["models"].keys())}
print("各 K 收敛迭代数 n_iter_:", n_iter_all)

# ---------------- 6. 保存亚型分配（供 P3） ----------------
final = data[["stay_id", "subject_id", "subtype", "subtype_prob", "surv_time", "event"]].copy()
final["subtype_name"] = final["subtype"].map(subtype_names)
final.to_csv(f"{OUT}\\P2_亚型分配.csv", index=False, encoding="utf-8-sig")
print("\nsaved P2_亚型分配.csv", final.shape)

# ---------------- 7. 汇总 JSON（供报告） ----------------
summary = dict(
    best_K=K,
    n_main=int(len(data)),
    subtype_names={str(k): subtype_names[k] for k in range(K)},
    n_per={str(k): int(n_per.get(k, 0)) for k in range(K)},
    mortality_28d={str(k): float(mort.loc[k, "pct"]) if k in mort.index else np.nan for k in range(K)},
    logrank_chi2=float(chi2_lr), logrank_p=float(p_lr),
    logrank_p_str=p_lr_str,
    km_end_by_subtype=km_end_by_subtype,
    sensitivity={k: v for k, v in sens.items()},
    kml_best_CH=int(kml_df.sort_values("CH", ascending=False).iloc[0]["K"]),
    kml_best_sil=int(kml_df.sort_values("Silhouette", ascending=False).iloc[0]["K"]),
    n_iter_all=n_iter_all,
    n_boundary_prob_lt06=int(n_bound),
    boundary_sensitivity=mort_cmp.to_dict("records"),
    renumber_map=renumber_map.to_dict("records"),
)
with open(f"{OUT}\\P2_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
print("\nDONE_CHARACTERIZE")
