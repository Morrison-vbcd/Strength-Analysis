# -*- coding: utf-8 -*-
"""ZigZag 參數掃描:在多個代表性參考序列上,比較 門檻 × 最短區間 的切段結果。

實用性判準(啟發式):
- 24 個月切出 8~16 段最能看出板塊內輪動(平均一段約 6~12 週);
- 段數 < 6 → 太粗,看不到輪動;> 20 → 太碎,標籤變成雜訊;
- 中位段長 >= 15 個交易日,單段才有統計意義。

用法: .venv\\Scripts\\python.exe param_sweep.py
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import analysis as core
import data as datamod


def _fetch(tickers: list[str], start: pd.Timestamp, end: pd.Timestamp):
    """相容舊介面：回傳 (價格表, 略過清單)。市場混用時逐檔已含後綴，用美股模式即可。"""
    px, _resolved, missing = datamod.fetch_prices(
        tickers, None, "美股", str(start.date()), str(end.date())
    )
    return px, missing

LOOKBACK_MONTHS = 24
THRESHOLDS = [0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10, 0.12]
MIN_BARS_LIST = [5, 10, 15]

# 代表性參考序列:美股板塊基準 + 台股基準 + 兩個等權籃子
REFS_SINGLE = ["SOXX", "XLK", "QQQ", "XLE", "XBI", "0050.TW", "00891.TW"]
BASKETS = {
    "美股半導體籃子": ["NVDA", "AMD", "AVGO", "QCOM", "TXN", "MU", "INTC", "MRVL"],
    "台股半導體籃子": ["2330.TW", "2454.TW", "2379.TW", "3034.TW", "2303.TW", "3711.TW"],
}


def leg_stats(series: pd.Series, threshold: float, min_bars: int) -> dict:
    legs = core.build_legs(series, threshold, min_bars)
    if not legs:
        return {"段數": 0, "中位段長": np.nan, "平均段長": np.nan}
    s = series.dropna()
    lens = [len(s.loc[l.start:l.end]) - 1 for l in legs]
    return {
        "段數": len(legs),
        "中位段長": float(np.median(lens)),
        "平均段長": round(float(np.mean(lens)), 1),
    }


def main() -> None:
    # Windows 主控台預設 cp950,強制 UTF-8 避免中文/符號炸掉
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    end = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(months=LOOKBACK_MONTHS)

    refs: dict[str, pd.Series] = {}
    px, skipped = _fetch(REFS_SINGLE, start, end)
    if skipped:
        print(f"[warn] 無資料略過: {skipped}")
    for t in px.columns:
        refs[t] = px[t]
    for name, lst in BASKETS.items():
        bp, bs = _fetch(lst, start, end)
        if bs:
            print(f"[warn] {name} 略過: {bs}")
        refs[name] = core.build_group_index(bp)

    rows = []
    for name, s in refs.items():
        for th in THRESHOLDS:
            for mb in MIN_BARS_LIST:
                st = leg_stats(s, th, mb)
                rows.append({"參考序列": name, "門檻%": th * 100, "最短區間": mb, **st})
    df = pd.DataFrame(rows)

    # 每組參數跨參考序列彙總
    agg = (
        df.groupby(["門檻%", "最短區間"])
        .agg(平均段數=("段數", "mean"), 最少段數=("段數", "min"), 最多段數=("段數", "max"),
             中位段長=("中位段長", "median"))
        .round(1)
        .reset_index()
    )
    agg["實用"] = agg.apply(
        lambda r: "✔" if 8 <= r["平均段數"] <= 16 and r["最少段數"] >= 5 and r["中位段長"] >= 15 else "",
        axis=1,
    )

    pd.set_option("display.unicode.east_asian_width", True)
    pd.set_option("display.width", 200)
    print("\n=== 各參考序列明細 ===")
    print(df.pivot_table(index="參考序列", columns=["門檻%", "最短區間"], values="段數").to_string())
    print("\n=== 跨序列彙總(24 個月)===")
    print(agg.to_string(index=False))
    df.to_csv("param_sweep_detail.csv", index=False, encoding="utf-8-sig")
    agg.to_csv("param_sweep_summary.csv", index=False, encoding="utf-8-sig")
    print("\n已輸出 param_sweep_detail.csv / param_sweep_summary.csv")


if __name__ == "__main__":
    main()
