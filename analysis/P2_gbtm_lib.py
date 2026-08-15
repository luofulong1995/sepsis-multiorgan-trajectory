# -*- coding: utf-8 -*-
"""
P2_gbtm_lib.py — 组基轨迹模型(GBTM)实现库
==================================================
实现 Nagin 式多变量联合轨迹模型 (group-based multi-trajectory model)：
  - 共享潜类别 k (K 类)
  - 每个变量 v 在类别 k 内为时间多项式回归 (默认二次)
  - 每变量每类别独立方差（符合 GBTM 惯例）
  - 缺失数据处理：按变量×时间点因子化似然，缺失项不贡献（类内条件独立）
  - EM 算法：E步后验概率 → M步加权多项式回归 + 方差 + 类别比例
数值稳定：log 空间 logaddexp；方差下限；WLS 加微小岭。

同时提供 KML（纵向 k-means）交叉验证实现（Python 自实现，等价 R kml 之 Euclidean k-means）。
"""
import numpy as np


class MultiTrajGBTM:
    def __init__(self, K, degree=2, max_iter=300, tol=1e-7,
                 n_starts=3, seed=0, var_floor=1e-3, ridge=1e-6):
        self.K = K
        self.degree = degree
        self.max_iter = max_iter
        self.tol = tol
        self.n_starts = n_starts
        self.seed = seed
        self.var_floor = var_floor
        self.ridge = ridge
        self.best_ll_ = -np.inf
        self.params_ = None
        self.gamma_ = None
        self.loglik_ = None
        self.n_iter_ = 0
        self.converged_ = False

    @staticmethod
    def _design(t, degree):
        """time -> [1, t, t^2, ...]"""
        return np.vander(np.asarray(t, float), degree + 1, increasing=True)

    def _loglik_obs(self, Y, times, pi, betas, sigmas):
        """逐患者 log-likelihood (log p(y_i))"""
        n = len(Y[0])
        ll = np.full(n, -np.inf)
        for k in range(self.K):
            lk = np.zeros(n)
            for v, yv in enumerate(Y):
                X = self._design(times[v], self.degree)   # (T_v, d)
                mu = X @ betas[v][k]                      # (T_v,)
                sd = np.sqrt(sigmas[v][k])
                obs = ~np.isnan(yv)
                if obs.any():
                    dev = (yv - mu[None, :])**2 / sigmas[v][k]
                    term = np.where(obs, -0.5 * dev - 0.5 * np.log(2 * np.pi) - np.log(sd), 0.0)
                    lk += term.sum(axis=1)
            ll = np.logaddexp(ll, np.log(pi[k]) + lk)
        return ll

    def _estep(self, Y, times, pi, betas, sigmas):
        n = len(Y[0])
        log_gamma = np.zeros((n, self.K))
        for k in range(self.K):
            lk = np.zeros(n)
            for v, yv in enumerate(Y):
                X = self._design(times[v], self.degree)
                mu = X @ betas[v][k]
                sd = np.sqrt(sigmas[v][k])
                obs = ~np.isnan(yv)
                if obs.any():
                    dev = (yv - mu[None, :])**2 / sigmas[v][k]
                    term = np.where(obs, -0.5 * dev - 0.5 * np.log(2 * np.pi) - np.log(sd), 0.0)
                    lk += term.sum(axis=1)
            log_gamma[:, k] = np.log(pi[k]) + lk
        # log-sum-exp normalize
        mx = log_gamma.max(axis=1, keepdims=True)
        expg = np.exp(log_gamma - mx)
        Z = expg.sum(axis=1, keepdims=True)
        gamma = expg / Z
        # per-patient log-likelihood
        ll_i = mx.squeeze() + np.log(Z.squeeze())
        return gamma, ll_i

    def _mstep(self, Y, times, gamma):
        n = gamma.shape[0]
        pi = gamma.mean(axis=0)
        betas, sigmas = [], []
        for v, yv in enumerate(Y):
            X = self._design(times[v], self.degree)       # (T_v, d)
            d = X.shape[1]
            bv = np.zeros((self.K, d))
            sv = np.zeros(self.K)
            T_v = yv.shape[1]
            Xbig = np.tile(X, (n, 1))
            yvec = yv.ravel()
            obs = ~np.isnan(yvec)
            for k in range(self.K):
                W = np.repeat(gamma[:, k], T_v)
                Wo = W[obs]
                Xo = Xbig[obs]
                yo = yvec[obs]
                if Wo.sum() < 1e-8:
                    bv[k] = 0.0
                    sv[k] = 1.0
                    continue
                XWX = (Xo * Wo[:, None]).T @ Xo
                XWy = (Xo * Wo[:, None]).T @ yo
                XWX += self.ridge * np.eye(d)
                b = np.linalg.solve(XWX, XWy)
                resid = yo - Xo @ b
                ss = float(np.sum(Wo * resid**2) / Wo.sum())
                bv[k] = b
                sv[k] = max(ss, self.var_floor)
            betas.append(bv)
            sigmas.append(sv)
        return pi, betas, sigmas

    def _fit_single(self, Y, times, init_gamma):
        n = len(Y[0])
        gamma = init_gamma.copy()
        pi, betas, sigmas = self._mstep(Y, times, gamma)
        prev_ll = -np.inf
        for it in range(self.max_iter):
            gamma, ll_i = self._estep(Y, times, pi, betas, sigmas)
            pi, betas, sigmas = self._mstep(Y, times, gamma)
            ll = ll_i.sum()
            if abs(ll - prev_ll) < self.tol * max(1.0, abs(prev_ll)):
                break
            prev_ll = ll
        gamma, ll_i = self._estep(Y, times, pi, betas, sigmas)
        ll = ll_i.sum()
        return ll, pi, betas, sigmas, gamma, it + 1

    def _kmeans_init(self, Y, times):
        """以均值插补后拼接向量做 k-means 硬分类作 EM 初始 gamma"""
        n = len(Y[0])
        vecs = []
        for v, yv in enumerate(Y):
            mu_v = np.nanmean(yv, axis=0)
            imp = np.where(np.isnan(yv), mu_v[None, :], yv)
            vecs.append(imp)
        X = np.hstack(vecs)
        from sklearn.cluster import KMeans
        km = KMeans(n_clusters=self.K, n_init=10, random_state=self.seed)
        lab = km.fit_predict(X)
        gamma = np.zeros((n, self.K))
        gamma[np.arange(n), lab] = 1.0
        return gamma

    def fit(self, Y, times):
        """Y: list of (n, T_v) arrays (NaN=缺失); times: list of time arrays"""
        rng = np.random.default_rng(self.seed)
        n = len(Y[0])
        best = None
        start_lls = []
        for s in range(self.n_starts):
            if s == 0:
                init_gamma = self._kmeans_init(Y, times)
            else:
                init_gamma = rng.dirichlet(np.ones(self.K), size=n)
            ll, pi, betas, sigmas, gamma, n_it = self._fit_single(Y, times, init_gamma)
            start_lls.append(ll)
            if ll > self.best_ll_ + 1e-6:
                self.best_ll_ = ll
                best = (pi, betas, sigmas, gamma, n_it)
        if best is None:
            best = (np.ones(self.K)/self.K, None, None, None, 0)
        self.pi_, self.betas_, self.sigmas_, self.gamma_, self.n_iter_ = best
        self.start_lls_ = np.array(start_lls)
        self.converged_ = True
        return self

    # ---- 模型诊断 ----
    def n_params(self, V):
        return (self.K - 1) + V * self.K * (self.degree + 1 + 1)  # beta + sigma per var per class

    def bic(self, V, n):
        return -2 * self.best_ll_ + self.n_params(V) * np.log(n)

    def aic(self, V, n):
        return -2 * self.best_ll_ + 2 * self.n_params(V)

    def icl(self, V, n):
        """ICL (Biernacki 2000) = BIC + 2*Σγᵢₖlnγᵢₖ = BIC - 2*n*entropy*ln(K)
        由于 Σγ lnγ ≤ 0，ICL ≤ BIC（entropy 项为减号）。"""
        ent = self.diagnostics()["entropy"]
        return self.bic(V, n) - 2 * n * ent * np.log(self.K)

    def posterior(self):
        return self.gamma_

    def labels(self):
        return self.gamma_.argmax(axis=1)

    def diagnostics(self):
        """AVP, 熵, 类别占比(软/硬), 每类样本量"""
        K = self.K
        lab = self.labels()
        n = len(lab)
        avp = np.array([self.gamma_[lab == k, k].mean() if (lab == k).sum() else np.nan
                        for k in range(K)])
        entropy = float(-np.sum(self.gamma_ * np.log(self.gamma_ + 1e-300)) / (n * np.log(K)))
        hard_n = np.array([(lab == k).sum() for k in range(K)])
        hard_p = hard_n / n
        return dict(avp=avp, entropy=entropy, hard_n=hard_n, hard_p=hard_p, pi=self.pi_)

    def trajectory_means(self, Y, times):
        """返回每变量每类别 3 时间点的期望值（变换空间，供反变换）"""
        out = {}
        for v in range(len(Y)):
            X = self._design(times[v], self.degree)
            out[v] = np.array([X @ self.betas_[v][k] for k in range(self.K)])  # (K, T_v)
        return out


class KMLCrossVal:
    """KML 交叉验证：纵向 k-means（Euclidean），多起点，报告 CH / silhouette 选择类数"""
    def __init__(self, K_range, n_init=20, seed=0):
        self.K_range = list(K_range)
        self.n_init = n_init
        self.seed = seed

    def run(self, X):
        """X: (n, p) 标准化轨迹（缺失已按时间点均值插补）"""
        from sklearn.cluster import KMeans
        from sklearn.metrics import calinski_harabasz_score, silhouette_score
        res = {}
        for K in self.K_range:
            km = KMeans(n_clusters=K, n_init=self.n_init, random_state=self.seed)
            lab = km.fit_predict(X)
            ch = calinski_harabasz_score(X, lab)
            sil = silhouette_score(X, lab) if K > 1 else np.nan
            res[K] = dict(labels=lab, centers=km.cluster_centers_, ch=ch, sil=sil,
                          inertia=km.inertia_)
        return res
