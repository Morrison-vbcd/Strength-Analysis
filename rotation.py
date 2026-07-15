# -*- coding: utf-8 -*-
"""RRG（Relative Rotation Graph）計算。純邏輯，無 Streamlit。

用「板塊 ETF ÷ 大盤」的 RS 做 RRG：RS-Ratio(x) vs RS-Momentum(y)，中心 100。
JdK RS-Ratio/Momentum 的公開重現（rolling z-score 中心 100），
非 StockCharts 專有公式，數值會略有出入但象限與輪動方向一致。

四象限（順時針輪動 落後→改善→領先→轉弱→落後）：
- 右上 領先 Leading（ratio≥100, mom≥100）
- 右下 轉弱 Weakening（ratio≥100, mom<100）
- 左下 落後 Lagging（ratio<100, mom<100）
- 左上 改善 Improving（ratio<100, mom≥100）
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import sectors

# 頻率 → (正規化滾動窗, 動能回看期)
FREQ_PARAMS: dict[str, tuple[int, int]] = {"週線": (13, 1), "日線": (63, 5)}

QUADRANT_ORDER = ["領先", "改善", "轉弱", "落後"]


def to_freq(prices: pd.DataFrame, freq: str) -> pd.DataFrame:
    """週線 = W-FRI 收盤重採樣；日線原樣。"""
    if freq == "週線":
        return prices.resample("W-FRI").last().dropna(how="all")
    return prices


def _quadrant(ratio: float, mom: float) -> str:
    if ratio >= 100.0:
        return "領先" if mom >= 100.0 else "轉弱"
    return "改善" if mom >= 100.0 else "落後"


def compute_rrg_full(
    prices: pd.DataFrame,
    sector_cols: list[str],
    bench_col: str,
    freq: str,
    window: int | None = None,
    mom_window: int | None = None,
) -> dict[str, pd.DataFrame]:
    """回傳 {板塊: 完整 DataFrame[ratio, mom, quadrant]}（不裁尾，給動畫與訊號用）。"""
    w, m = FREQ_PARAMS.get(freq, (13, 1))
    window = window or w
    mom_window = mom_window or m
    px = to_freq(prices, freq)
    bench = px[bench_col].dropna()
    out: dict[str, pd.DataFrame] = {}
    for col in sector_cols:
        if col not in px.columns:
            continue
        sec = px[col].dropna()
        idx = sec.index.intersection(bench.index)
        if len(idx) < window + mom_window + 2:
            continue
        rs = 100.0 * sec.loc[idx] / bench.loc[idx]
        mean = rs.rolling(window).mean()
        std = rs.rolling(window).std()
        ratio = 100.0 + (rs - mean) / std.replace(0.0, np.nan)
        roc = 100.0 * (ratio / ratio.shift(mom_window) - 1.0)
        r_mean = roc.rolling(window).mean()
        r_std = roc.rolling(window).std()
        mom = 100.0 + (roc - r_mean) / r_std.replace(0.0, np.nan)
        df = pd.DataFrame({"ratio": ratio, "mom": mom}).dropna()
        if df.empty:
            continue
        df["quadrant"] = [_quadrant(r, mo) for r, mo in zip(df["ratio"], df["mom"])]
        out[col] = df
    return out


def compute_rrg(
    prices: pd.DataFrame,
    sector_cols: list[str],
    bench_col: str,
    freq: str,
    tail_len: int,
    window: int | None = None,
    mom_window: int | None = None,
) -> dict[str, pd.DataFrame]:
    """各板塊裁到最近 tail_len 點（畫快照/軌跡用）。"""
    full = compute_rrg_full(prices, sector_cols, bench_col, freq, window, mom_window)
    return {k: v.tail(tail_len) for k, v in full.items()}


def rrg_summary(rrg: dict[str, pd.DataFrame], market: str, name_fn) -> pd.DataFrame:
    """現況象限一覽表，依象限順序（領先→改善→轉弱→落後）與 RS-Ratio 排序。"""
    rows = []
    for col, df in rrg.items():
        last = df.iloc[-1]
        rows.append(
            {
                "板塊": name_fn(market, col),
                "象限": last["quadrant"],
                "RS-Ratio": round(float(last["ratio"]), 2),
                "RS-Mom": round(float(last["mom"]), 2),
                "日期": df.index[-1].strftime("%Y-%m-%d"),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["_q"] = out["象限"].map({q: i for i, q in enumerate(QUADRANT_ORDER)})
    out = out.sort_values(["_q", "RS-Ratio"], ascending=[True, False]).drop(columns="_q")
    return out.reset_index(drop=True)


def risk_regime(rrg: dict[str, pd.DataFrame], market: str) -> str:
    """比較進攻 vs 防禦板塊的平均 RS-Ratio，給 risk-on/off 提示。"""
    att, dfn = [], []
    for col, df in rrg.items():
        v = float(df["ratio"].iloc[-1])
        (dfn if sectors.is_defensive(market, col) else att).append(v)
    if not att or not dfn:
        return "⚖️ 板塊樣本不足，無法判定 risk-on/off（進攻與防禦板塊都要至少選一個）。"
    a, d = float(np.mean(att)), float(np.mean(dfn))
    diff = a - d
    if diff > 1.0:
        return f"🔥 Risk-ON：進攻板塊平均 RS-Ratio {a:.1f} 明顯高於防禦 {d:.1f}，資金偏好風險資產。"
    if diff < -1.0:
        return f"🛡️ Risk-OFF：防禦板塊平均 RS-Ratio {d:.1f} 高於進攻 {a:.1f}，資金轉向避風港，操作宜保守。"
    return f"⚖️ 中性：進攻 {a:.1f} vs 防禦 {d:.1f}，資金風向不明朗。"


# 象限轉換 → (多空, 訊號說明)。順時針 = 正常輪動；逆時針/跳象限 = 特別注意。
_TRANSITIONS: dict[tuple[str, str], tuple[str, str]] = {
    ("落後", "改善"): ("利多", "動能翻正，脫離落後象限"),
    ("改善", "領先"): ("利多", "站上大盤，確認轉強"),
    ("轉弱", "領先"): ("利多", "動能重啟，重回領先"),
    ("落後", "領先"): ("利多", "跳象限直上領先（罕見，強訊號）"),
    ("領先", "轉弱"): ("利空", "動能熄火，領導力衰退"),
    ("轉弱", "落後"): ("利空", "跌破大盤，完成轉弱循環"),
    ("改善", "落後"): ("利空", "改善失敗，動能再度轉負"),
    ("領先", "落後"): ("利空", "跳象限直落（罕見，急轉直下)"),
    ("領先", "改善"): ("中性", "跌破大盤但動能仍正，觀察是否假摔"),
    ("改善", "轉弱"): ("中性", "橫跨到大盤上方但動能轉負（罕見對角）"),
    ("轉弱", "改善"): ("中性", "動能修復中（罕見對角）"),
    ("落後", "轉弱"): ("中性", "站上大盤但動能仍弱（罕見對角）"),
}


def rrg_pattern_signals(
    full: dict[str, pd.DataFrame],
    market: str,
    name_fn,
    lookback: int = 8,
) -> pd.DataFrame:
    """最近 lookback 期內的象限轉換訊號表。

    回傳 DataFrame[日期, 板塊, 訊號, 多空, RS-Ratio, RS-Mom]，日期新→舊。
    """
    rows = []
    for col, df in full.items():
        seg = df.tail(lookback + 1)
        quads = list(seg["quadrant"])
        for i in range(1, len(quads)):
            if quads[i] == quads[i - 1]:
                continue
            side, note = _TRANSITIONS.get(
                (quads[i - 1], quads[i]), ("中性", "象限變動")
            )
            rows.append(
                {
                    "日期": seg.index[i].strftime("%Y-%m-%d"),
                    "板塊": name_fn(market, col),
                    "訊號": f"{quads[i-1]} → {quads[i]}：{note}",
                    "多空": side,
                    "RS-Ratio": round(float(seg["ratio"].iloc[i]), 2),
                    "RS-Mom": round(float(seg["mom"].iloc[i]), 2),
                }
            )
    out = pd.DataFrame(rows, columns=["日期", "板塊", "訊號", "多空", "RS-Ratio", "RS-Mom"])
    if not out.empty:
        out = out.sort_values("日期", ascending=False).reset_index(drop=True)
    return out
