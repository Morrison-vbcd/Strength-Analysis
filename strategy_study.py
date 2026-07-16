# -*- coding: utf-8 -*-
"""波段板塊輪動策略的實價復盤研究（策略守則的數據依據，可重跑）。

美股週線 RRG（與工具同一套 rotation.py 計算），2018 起抓價、2019 起評估：

A. 象限狀態 → 未來 4/8/13 週「相對 SPY」報酬（勝率/平均/中位）
B. 象限轉換事件 → 未來 4/8/13 週相對報酬（哪種轉換值得進場）
C. 多頭轉換「立刻進場」vs「等 1 週確認再進場」的比較
D. 板塊多頭事件時，族群內「RS 最強 vs 等權籃子 vs 最弱」的下 8 週表現
E. 簡單組合回測：每週持有 領先∪改善 中 RS-Mom 最高的 3 個進攻板塊，
   搭配 risk-off 開關（防禦強於進攻時改持防禦組）vs SPY buy&hold

用法： .venv\\Scripts\\python.exe strategy_study.py
輸出：主控台表格 + strategy_study_results.csv（各分析彙總）
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import analysis
import data
import rotation
import sectors

START_FETCH = "2018-01-01"
START_EVAL = pd.Timestamp("2019-01-01")
FWD_WEEKS = [4, 8, 13]
MARKET = "美股"

# D 研究用的板塊代表籃子（高同質、事件當下可交易的大型股）
STOCK_BASKETS: dict[str, list[str]] = {
    "SMH": ["NVDA", "AMD", "AVGO", "AMAT", "LRCX", "KLAC", "MU", "TXN"],
    "XLF": ["JPM", "BAC", "WFC", "C", "GS", "MS"],
    "XLE": ["EOG", "DVN", "FANG", "OXY", "XOM", "CVX"],
    "XLK": ["AAPL", "MSFT", "NVDA", "CRM", "ADBE", "ORCL"],
}

BULL_TRANS = [("落後", "改善"), ("改善", "領先"), ("轉弱", "領先"), ("落後", "領先")]
BEAR_TRANS = [("領先", "轉弱"), ("轉弱", "落後"), ("改善", "落後"), ("領先", "落後")]


def fwd_rel(pxw: pd.DataFrame, col: str, bench: str, t: pd.Timestamp, k: int) -> float:
    """t 之後 k 週的相對報酬（col vs bench）。資料不足回 NaN。"""
    idx = pxw.index
    i = idx.get_loc(t)
    if i + k >= len(idx):
        return np.nan
    s0, s1 = pxw[col].iloc[i], pxw[col].iloc[i + k]
    b0, b1 = pxw[bench].iloc[i], pxw[bench].iloc[i + k]
    if any(pd.isna(x) for x in (s0, s1, b0, b1)):
        return np.nan
    return float((s1 / s0) / (b1 / b0) - 1.0)


def agg(vals: list[float]) -> dict:
    s = pd.Series([v for v in vals if not pd.isna(v)])
    if s.empty:
        return {"n": 0, "win%": np.nan, "mean%": np.nan, "med%": np.nan}
    return {
        "n": int(len(s)),
        "win%": round(100.0 * float((s > 0).mean()), 1),
        "mean%": round(float(s.mean()) * 100, 2),
        "med%": round(float(s.median()) * 100, 2),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    end = pd.Timestamp.today().normalize()
    secs = list(sectors.rotation_sectors(MARKET).keys())
    bench = sectors.rotation_benchmark(MARKET)

    print(f"抓取 {len(secs)} 板塊 + {bench}，{START_FETCH} ~ {end.date()} ...")
    px, resolved, missing = data.fetch_prices(secs, bench, MARKET, START_FETCH, str(end.date()))
    if missing:
        print(f"[warn] 略過: {missing}")
    bcol = resolved[data.SECTOR_KEY]
    scols = [resolved[t] for t in secs if t in resolved]
    full = rotation.compute_rrg_full(px, scols, bcol, "週線")
    pxw = rotation.to_freq(px, "週線")
    out_rows: list[dict] = []

    # ---------------- A. 象限狀態 → 未來相對報酬 ----------------
    print("\n=== A. 象限狀態 → 未來相對 SPY 報酬 ===")
    for k in FWD_WEEKS:
        bucket: dict[str, list[float]] = {q: [] for q in rotation.QUADRANT_ORDER}
        for col, df in full.items():
            for t, row in df.iterrows():
                if t < START_EVAL or t not in pxw.index:
                    continue
                bucket[row["quadrant"]].append(fwd_rel(pxw, col, bcol, t, k))
        for q in rotation.QUADRANT_ORDER:
            r = agg(bucket[q])
            out_rows.append({"分析": "A_象限狀態", "項目": q, "前瞻週": k, **r})
            if k == 8:
                print(f"  {q}: n={r['n']:5d}  勝率 {r['win%']:5.1f}%  平均 {r['mean%']:+.2f}%  中位 {r['med%']:+.2f}%  (8週)")

    # ---------------- A2. 離中心距離過濾後的象限狀態 ----------------
    print("\n=== A2. 象限狀態（離中心 ≥1.0 才計）→ 8 週相對報酬 ===")
    for q in rotation.QUADRANT_ORDER:
        vals = []
        for col, df in full.items():
            for t, row in df.iterrows():
                if t < START_EVAL or t not in pxw.index or row["quadrant"] != q:
                    continue
                if abs(row["ratio"] - 100.0) < 1.0 or abs(row["mom"] - 100.0) < 1.0:
                    continue
                vals.append(fwd_rel(pxw, col, bcol, t, 8))
        r = agg(vals)
        out_rows.append({"分析": "A2_距離過濾", "項目": q, "前瞻週": 8, **r})
        print(f"  {q}: n={r['n']:5d}  勝率 {r['win%']:5.1f}%  平均 {r['mean%']:+.2f}%  中位 {r['med%']:+.2f}%")

    # ---------------- A3. 原始 13 週相對動能（趨勢態，非 z-score 振盪器） ----------------
    print("\n=== A3. 原始 13 週相對動能狀態 → 8 週相對報酬 ===")
    for label, cond in [("13週贏SPY", 1), ("13週輸SPY", -1)]:
        vals = []
        for col in scols:
            s = pxw[col].dropna()
            common = s.index.intersection(pxw[bcol].dropna().index)
            for i in range(13, len(common) - 8):
                t = common[i]
                if t < START_EVAL:
                    continue
                rel13 = (s.loc[t] / s.loc[common[i - 13]]) / (
                    pxw[bcol].loc[t] / pxw[bcol].loc[common[i - 13]]) - 1.0
                if (rel13 > 0) == (cond > 0):
                    vals.append(fwd_rel(pxw, col, bcol, t, 8))
        r = agg(vals)
        out_rows.append({"分析": "A3_原始動能", "項目": label, "前瞻週": 8, **r})
        print(f"  {label}: n={r['n']:5d}  勝率 {r['win%']:5.1f}%  平均 {r['mean%']:+.2f}%  中位 {r['med%']:+.2f}%")

    # ---------------- B. 象限轉換事件 ----------------
    print("\n=== B. 象限轉換 → 未來相對 SPY 報酬（8 週） ===")
    events: dict[tuple[str, str], list[tuple[str, pd.Timestamp]]] = {}
    for col, df in full.items():
        quads = df["quadrant"]
        for i in range(1, len(quads)):
            t = quads.index[i]
            if t < START_EVAL or t not in pxw.index:
                continue
            if quads.iloc[i] != quads.iloc[i - 1]:
                events.setdefault((quads.iloc[i - 1], quads.iloc[i]), []).append((col, t))
    for trans in BULL_TRANS + BEAR_TRANS:
        evs = events.get(trans, [])
        for k in FWD_WEEKS:
            r = agg([fwd_rel(pxw, c, bcol, t, k) for c, t in evs])
            out_rows.append({"分析": "B_象限轉換", "項目": f"{trans[0]}→{trans[1]}", "前瞻週": k, **r})
            if k == 8:
                print(f"  {trans[0]}→{trans[1]}: n={r['n']:4d}  勝率 {r['win%']:5.1f}%  平均 {r['mean%']:+.2f}%  中位 {r['med%']:+.2f}%")

    # ---------------- C. 立刻進場 vs 等 1 週確認 ----------------
    print("\n=== C. 多頭轉換：立刻進場 vs 等 1 週確認（8 週相對報酬） ===")
    for trans in [("落後", "改善"), ("改善", "領先")]:
        evs = events.get(trans, [])
        immediate, confirmed, reverted = [], [], 0
        for col, t in evs:
            immediate.append(fwd_rel(pxw, col, bcol, t, 8))
            df = full[col]
            i = df.index.get_loc(t)
            if i + 1 < len(df):
                if df["quadrant"].iloc[i + 1] == trans[1]:
                    confirmed.append(fwd_rel(pxw, col, bcol, df.index[i + 1], 8))
                else:
                    reverted += 1
        ri, rc = agg(immediate), agg(confirmed)
        out_rows.append({"分析": "C_確認比較", "項目": f"{trans[0]}→{trans[1]}_立刻", "前瞻週": 8, **ri})
        out_rows.append({"分析": "C_確認比較", "項目": f"{trans[0]}→{trans[1]}_等1週", "前瞻週": 8, **rc})
        rev_pct = 100.0 * reverted / max(len(evs), 1)
        print(f"  {trans[0]}→{trans[1]}: 立刻 n={ri['n']} 勝率 {ri['win%']}% 平均 {ri['mean%']:+.2f}% ｜ "
              f"等1週 n={rc['n']} 勝率 {rc['win%']}% 平均 {rc['mean%']:+.2f}% ｜ 1週內打回 {rev_pct:.0f}%")

    # ---------------- D. 板塊多頭事件 → 族群內選股 ----------------
    print("\n=== D. 板塊多頭事件（落後→改善 / 改善→領先）時的族群內選股（下 8 週 vs 籃子） ===")
    top_sp, bot_sp, top_beats = [], [], 0
    n_events = 0
    for etf, names in STOCK_BASKETS.items():
        spx, sres, smiss = data.fetch_prices(names, None, MARKET, START_FETCH, str(end.date()))
        cols = [sres[t] for t in names if t in sres]
        spw = rotation.to_freq(spx[cols], "週線")
        basket_w = analysis.build_group_index(spw, cols)
        for trans in [("落後", "改善"), ("改善", "領先")]:
            for col, t in events.get(trans, []):
                if col != etf or t not in spw.index:
                    continue
                i = spw.index.get_loc(t)
                if i < 13 or i + 8 >= len(spw):
                    continue
                # 事件當下：過去 13 週相對籃子的報酬排名
                mom = {}
                for c in cols:
                    s0, s1 = spw[c].iloc[i - 13], spw[c].iloc[i]
                    b0, b1 = basket_w.iloc[i - 13], basket_w.iloc[i]
                    if pd.isna(s0) or pd.isna(s1):
                        continue
                    mom[c] = (s1 / s0) / (b1 / b0) - 1.0
                if len(mom) < 4:
                    continue
                top = max(mom, key=mom.get)
                bot = min(mom, key=mom.get)
                fb = float(basket_w.iloc[i + 8] / basket_w.iloc[i] - 1.0)
                ft = float(spw[top].iloc[i + 8] / spw[top].iloc[i] - 1.0)
                fw = float(spw[bot].iloc[i + 8] / spw[bot].iloc[i] - 1.0)
                top_sp.append(ft - fb)
                bot_sp.append(fw - fb)
                top_beats += int(ft > fb)
                n_events += 1
    rt, rb = agg(top_sp), agg(bot_sp)
    out_rows.append({"分析": "D_族群內選股", "項目": "RS最強-籃子", "前瞻週": 8, **rt})
    out_rows.append({"分析": "D_族群內選股", "項目": "RS最弱-籃子", "前瞻週": 8, **rb})
    print(f"  事件數 {n_events}（4 籃子合計）")
    print(f"  RS 最強 vs 籃子: 贏籃子比率 {100.0 * top_beats / max(n_events, 1):.1f}%  平均超額 {rt['mean%']:+.2f}%  中位 {rt['med%']:+.2f}%")
    print(f"  RS 最弱 vs 籃子: 平均超額 {rb['mean%']:+.2f}%  中位 {rb['med%']:+.2f}%")

    # ---------------- E. 簡單組合回測 ----------------
    print("\n=== E. 組合回測（2019~，週線，訊號週收盤進出，不含成本） ===")
    att_cols = [c for c in scols if not sectors.is_defensive(MARKET, c)]
    dfn_cols = [c for c in scols if sectors.is_defensive(MARKET, c)]
    widx = pxw.loc[pxw.index >= START_EVAL].index

    def run_portfolio(use_regime: bool) -> pd.Series:
        eq, val = [], 1.0
        for i in range(len(widx) - 1):
            t, t1 = widx[i], widx[i + 1]
            ratios_att, ratios_dfn, cand = [], [], []
            for c in scols:
                df = full.get(c)
                if df is None or t not in df.index:
                    continue
                row = df.loc[t]
                (ratios_dfn if c in dfn_cols else ratios_att).append(float(row["ratio"]))
                if c in att_cols and row["quadrant"] in ("領先", "改善"):
                    cand.append((float(row["mom"]), c))
            risk_off = (
                use_regime and ratios_att and ratios_dfn
                and (np.mean(ratios_att) - np.mean(ratios_dfn)) < -1.0
            )
            if risk_off:
                held = dfn_cols
            else:
                held = [c for _, c in sorted(cand, reverse=True)[:3]]
            if held:
                rets = [pxw[c].loc[t1] / pxw[c].loc[t] - 1.0 for c in held
                        if pd.notna(pxw[c].loc[t]) and pd.notna(pxw[c].loc[t1])]
                r = float(np.mean(rets)) if rets else 0.0
            else:
                r = 0.0  # 無合格板塊 → 空手
            val *= 1.0 + r
            eq.append((t1, val))
        return pd.Series(dict(eq))

    def perf(eqs: pd.Series, name: str) -> dict:
        total = float(eqs.iloc[-1] - 1.0)
        years = (eqs.index[-1] - eqs.index[0]).days / 365.25
        cagr = (float(eqs.iloc[-1]) ** (1 / years) - 1.0) if years > 0 else np.nan
        dd = float((eqs / eqs.cummax() - 1.0).min())
        row = {"分析": "E_組合回測", "項目": name, "前瞻週": 0, "n": len(eqs),
               "win%": round(total * 100, 1), "mean%": round(cagr * 100, 2), "med%": round(dd * 100, 1)}
        print(f"  {name}: 總報酬 {total * 100:+.1f}%  年化 {cagr * 100:+.2f}%  最大回落 {dd * 100:.1f}%")
        return row

    eq_sw = run_portfolio(use_regime=True)
    eq_ns = run_portfolio(use_regime=False)
    spy = pxw[bcol].loc[eq_sw.index[0]: eq_sw.index[-1]]
    eq_spy = spy / spy.iloc[0]
    out_rows.append(perf(eq_sw, "輪動組合(含risk-off開關)"))
    out_rows.append(perf(eq_ns, "輪動組合(無開關)"))
    out_rows.append(perf(eq_spy, "SPY買進持有"))
    print("  （E 列欄位對應：win%=總報酬%、mean%=年化%、med%=最大回落%）")

    pd.DataFrame(out_rows).to_csv("strategy_study_results.csv", index=False, encoding="utf-8-sig")
    print("\n已輸出 strategy_study_results.csv")


if __name__ == "__main__":
    main()
