# -*- coding: utf-8 -*-
"""配對交易統計核心。純邏輯，無 Streamlit。

流程：對 log 價 OLS 得 β/α → spread = ln(A) − β·ln(B) − α →
Engle-Granger 共整合檢定 + ADF 檢定 + 滾動 z-score + AR(1) 半衰期。
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint

# 內建配對候選（高同質雙雄）。值 = (標的A, 標的B, 備註)
PAIR_PRESETS: dict[str, tuple[str, str, str]] = {
    "（自訂）": ("", "", ""),
    "V ↔ MA（支付雙雄）": ("V", "MA", "商業模式幾乎相同，經典配對"),
    "WDC ↔ STX（硬碟雙雄）": ("WDC", "STX", "HDD 寡占雙雄，同受容量價格驅動"),
    "AMAT ↔ LRCX（半導體設備）": ("AMAT", "LRCX", "同吃晶圓廠 capex"),
    "GS ↔ MS（投行雙雄）": ("GS", "MS", "同受資本市場活動驅動"),
    "FANG ↔ DVN（頁岩油）": ("FANG", "DVN", "同區域頁岩油 E&P"),
    "TXN ↔ ADI（類比 IC）": ("TXN", "ADI", "類比晶片雙雄，工業/車用曝險相近"),
    "PANW ↔ FTNT（資安）": ("PANW", "FTNT", "網路資安平台雙雄"),
    "SNOW ↔ DDOG（數據雲）": ("SNOW", "DDOG", "高成長數據軟體，利率敏感度同向"),
    "CEG ↔ TLN（核電）": ("CEG", "TLN", "AI 電力題材核電雙雄"),
}


def rebased_ratio(a: pd.Series, b: pd.Series) -> pd.Series:
    """A/B 比值 rebase 到 100（起點=100，上升 = A 相對走強）。"""
    ratio = (a / b).dropna()
    return 100.0 * ratio / ratio.iloc[0]


def _half_life(spread: pd.Series) -> float:
    """AR(1) 均值回歸半衰期：Δs_t = λ·s_{t-1} + ε，half-life = −ln2/λ。"""
    s = spread.dropna()
    lag = s.shift(1).dropna()
    ds = s.diff().dropna()
    lag, ds = lag.align(ds, join="inner")
    if len(lag) < 20 or float(np.var(lag)) == 0.0:
        return math.inf
    lam = float(np.cov(ds, lag)[0, 1] / np.var(lag))
    if lam >= 0:
        return math.inf  # 無均值回歸
    return float(-math.log(2.0) / lam)


def compute_pair(a: pd.Series, b: pd.Series, z_window: int = 60) -> dict:
    """回傳 dict：beta/alpha/spread/eg_p/adf_p/z/cur_z/half_life/n。

    a、b 為收盤價序列（同市場、同幣別）。
    """
    df = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(df) < max(z_window + 10, 90):
        raise ValueError(f"共同交易日僅 {len(df)} 天，至少需要 {max(z_window + 10, 90)} 天")
    la, lb = np.log(df["a"]), np.log(df["b"])
    # OLS：la = alpha + beta * lb
    beta = float(np.cov(la, lb)[0, 1] / np.var(lb))
    alpha = float(la.mean() - beta * lb.mean())
    spread = la - beta * lb - alpha
    eg_p = float(coint(la, lb)[1])
    adf_p = float(adfuller(spread.values, autolag="AIC")[1])
    z = (spread - spread.rolling(z_window).mean()) / spread.rolling(z_window).std()
    return {
        "beta": beta,
        "alpha": alpha,
        "spread": spread,
        "eg_p": eg_p,
        "adf_p": adf_p,
        "z": z,
        "cur_z": float(z.dropna().iloc[-1]) if not z.dropna().empty else math.nan,
        "half_life": _half_life(spread),
        "n": len(df),
    }


def verdict(res: dict) -> tuple[str, str]:
    """判讀：(標籤, 說明)。依共整合/ADF 是否 <0.05 且半衰期 5–60 天。"""
    coint_ok = res["eg_p"] < 0.05
    adf_ok = res["adf_p"] < 0.05
    hl = res["half_life"]
    hl_ok = 5.0 <= hl <= 60.0
    if coint_ok and adf_ok and hl_ok:
        return (
            "🟢 適合均值回歸",
            f"共整合成立（EG p={res['eg_p']:.3f}）、spread 定態（ADF p={res['adf_p']:.3f}）、"
            f"半衰期 {hl:.0f} 天在可操作範圍（5–60），統計上具備配對條件。",
        )
    if (coint_ok or adf_ok) and hl < 120:
        weak = []
        if not coint_ok:
            weak.append(f"EG 共整合未過（p={res['eg_p']:.3f}）")
        if not adf_ok:
            weak.append(f"ADF 未過（p={res['adf_p']:.3f}）")
        if not hl_ok:
            weak.append(f"半衰期 {hl:.0f} 天偏出 5–60 區間")
        return (
            "🟡 部分成立",
            "統計條件部分成立：" + "、".join(weak) + "。可觀察但倉位宜小、停損要嚴。",
        )
    return (
        "🔴 不建議配對",
        f"共整合不成立（EG p={res['eg_p']:.3f}、ADF p={res['adf_p']:.3f}）"
        + (f"，半衰期 {hl:.0f} 天過長" if math.isfinite(hl) else "，spread 無均值回歸傾向")
        + "。價差可能持續發散，均值回歸邏輯不適用。",
    )


def backtest_pair(
    a: pd.Series,
    b: pd.Series,
    z_window: int = 60,
    entry: float = 2.0,
    exit_z: float = 0.0,
    stop: float = 3.0,
    beta_window: int = 120,
) -> dict:
    """歷史回測：±entry σ 進場、z 回到 exit_z 平倉、|z| ≥ stop 停損。

    刻意與現況診斷不同的三個設計，避免前視偏誤：
    - β 用「滾動 beta_window 日」估計（診斷用的全樣本 β 看得到未來）。
    - z 用滾動 β 的 spread 再滾動標準化。
    - 訊號在 t 日收盤產生、**t+1 日收盤成交**。
    交易報酬 = 進場時固定 β 的 log 價差變化（≈ 對 A 腿名目的報酬率），
    不含手續費/借券成本。

    回傳 {trades: DataFrame, equity: Series(每日累計損益), stats: dict}。
    """
    df = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    need = beta_window + z_window + 20
    if len(df) < need:
        raise ValueError(f"共同交易日僅 {len(df)} 天，回測至少需要 {need} 天")
    la, lb = np.log(df["a"]), np.log(df["b"])
    beta = la.rolling(beta_window).cov(lb) / lb.rolling(beta_window).var()
    spread = la - beta * lb
    z = (spread - spread.rolling(z_window).mean()) / spread.rolling(z_window).std()

    idx = df.index
    lav, lbv, zv, bev = la.values, lb.values, z.values, beta.values
    pos = 0  # +1 = 做多 spread（多A空B）, -1 = 做空 spread
    ent: dict = {}
    trades: list[dict] = []
    daily = pd.Series(0.0, index=idx)

    def close_trade(i: int, reason: str) -> None:
        nonlocal pos
        pnl = pos * ((lav[i] - ent["la"]) - ent["beta"] * (lbv[i] - ent["lb"]))
        trades.append(
            {
                "進場日": ent["date"].strftime("%Y-%m-%d"),
                "方向": "多A空B" if pos > 0 else "空A多B",
                "進場z": round(ent["z"], 2),
                "出場日": idx[i].strftime("%Y-%m-%d"),
                "出場原因": reason,
                "持有天數": int((idx[i] - ent["date"]).days),
                "報酬%": round(pnl * 100, 2),
            }
        )
        pos = 0

    for i in range(1, len(idx)):
        zprev = zv[i - 1]
        if math.isnan(zprev) or math.isnan(bev[i - 1]):
            continue
        if pos != 0:
            # 每日以進場 β 計 mark-to-market
            daily.iloc[i] = pos * ((lav[i] - lav[i - 1]) - ent["beta"] * (lbv[i] - lbv[i - 1]))
            if pos > 0 and zprev >= exit_z:
                close_trade(i, "回歸")
            elif pos > 0 and zprev <= -stop:
                close_trade(i, "停損")
            elif pos < 0 and zprev <= exit_z:
                close_trade(i, "回歸")
            elif pos < 0 and zprev >= stop:
                close_trade(i, "停損")
        elif zprev <= -entry or zprev >= entry:
            pos = 1 if zprev <= -entry else -1
            ent = {"date": idx[i], "la": lav[i], "lb": lbv[i],
                   "beta": float(bev[i - 1]), "z": float(zprev)}
    if pos != 0:
        close_trade(len(idx) - 1, "未平倉（強制結算）")

    tr = pd.DataFrame(trades)
    equity = daily.cumsum() * 100.0
    if tr.empty:
        stats = {"筆數": 0}
    else:
        closed = tr[tr["出場原因"] != "未平倉（強制結算）"]
        base = closed if not closed.empty else tr
        stats = {
            "筆數": int(len(tr)),
            "勝率%": round(100.0 * float((base["報酬%"] > 0).mean()), 1),
            "平均報酬%": round(float(base["報酬%"].mean()), 2),
            "報酬中位%": round(float(base["報酬%"].median()), 2),
            "總報酬%": round(float(tr["報酬%"].sum()), 2),
            "平均持有天數": round(float(base["持有天數"].mean()), 1),
            "停損次數": int((tr["出場原因"] == "停損").sum()),
        }
    return {"trades": tr, "equity": equity, "stats": stats}


def signal(cur_z: float, entry: float = 2.0) -> str:
    """進出場方向提示（A = 分子腿）。"""
    if math.isnan(cur_z):
        return "z-score 資料不足，無法判斷。"
    if cur_z >= entry:
        return f"📉 現況 z = {cur_z:+.2f} ≥ +{entry:.1f}σ：A 相對 B 過度昂貴 → 做空 A、做多 B，等回到 0 附近平倉。"
    if cur_z <= -entry:
        return f"📈 現況 z = {cur_z:+.2f} ≤ −{entry:.1f}σ：A 相對 B 過度便宜 → 做多 A、做空 B，等回到 0 附近平倉。"
    if abs(cur_z) < 0.5:
        return f"⏸️ 現況 z = {cur_z:+.2f}，接近均值，無交易機會（持倉者可考慮平倉）。"
    return f"👀 現況 z = {cur_z:+.2f}，未達 ±{entry:.1f}σ 門檻，觀望等訊號。"
