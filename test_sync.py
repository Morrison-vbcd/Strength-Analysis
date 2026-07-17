# -*- coding: utf-8 -*-
"""同步驗證：邏輯層煙霧測試 + AppTest 跑三個分頁（真實 yfinance 資料）。

用法： .venv\\Scripts\\python.exe test_sync.py
"""
from __future__ import annotations

import sys
import traceback

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FAIL = 0


def check(name: str, fn):
    global FAIL
    try:
        fn()
        print(f"  [PASS] {name}")
    except Exception as ex:
        FAIL += 1
        print(f"  [FAIL] {name}: {ex}")
        traceback.print_exc(limit=3)


# ---------------------------------------------------------------- 邏輯層
print("== 邏輯層 ==")
import analysis
import benchmarks
import data
import pairtrade
import rotation
import sectors

end = pd.Timestamp.today().normalize()
start = end - pd.DateOffset(months=18)


def t_data():
    px, resolved, missing = data.fetch_prices(
        ["NVDA", "AMD", "AVGO"], "SOXX", "美股", str(start.date()), str(end.date())
    )
    assert resolved[data.SECTOR_KEY] == "SOXX", resolved
    assert len(px.columns) == 4 and not missing, (px.columns, missing)
    t_data.px, t_data.resolved = px, resolved


def t_data_tw():
    px, resolved, missing = data.fetch_prices(
        ["2330", "8299"], None, "台股", str(start.date()), str(end.date())
    )
    assert resolved.get("2330") == "2330.TW", resolved
    assert resolved.get("8299") == "8299.TWO", f"上櫃退補失敗: {resolved} missing={missing}"


def t_analyze():
    res = analysis.analyze(
        t_data.px, stock_cols=["NVDA", "AMD", "AVGO"], sector_col="SOXX",
        pct=0.05, min_bars=8,
    )
    assert res["legs"], "no legs"
    assert res["score_vs_group"] is not None and res["score_vs_sector"] is not None
    assert not res["ranking"].empty and not res["coverage"].empty
    sig, marks = analysis.detect_patterns(
        res["qual"], res["legs"], res["rs_lines"], ["NVDA", "AMD", "AVGO"],
        analysis.pattern_names(),
    )
    print(f"       legs={len(res['legs'])} signals={len(sig)}")


def t_rotation():
    market = "美股"
    secs = list(sectors.rotation_sectors(market).keys())
    bench = sectors.rotation_benchmark(market)
    px, resolved, missing = data.fetch_prices(
        secs, bench, market, str(start.date()), str(end.date())
    )
    bcol = resolved[data.SECTOR_KEY]
    cols = [resolved[t] for t in secs if t in resolved]
    assert len(cols) >= 13, f"板塊資料不足: {missing}"
    full = rotation.compute_rrg_full(px, cols, bcol, "週線")
    assert len(full) >= 13, f"RRG 只算出 {len(full)} 板塊"
    for df in full.values():
        assert {"ratio", "mom", "quadrant"} <= set(df.columns)
    summary = rotation.rrg_summary(full, market, sectors.display_name)
    assert len(summary) == len(full)
    regime = rotation.risk_regime(full, market)
    signals = rotation.rrg_pattern_signals(full, market, sectors.display_name, 8)
    daily = rotation.compute_rrg(px, cols, bcol, "日線", tail_len=8)
    assert all(len(v) <= 8 for v in daily.values())
    print(f"       sectors={len(full)} signals={len(signals)} | {regime[:28]}…")


def t_pair():
    px, resolved, missing = data.fetch_prices(
        ["V", "MA"], None, "美股",
        str((end - pd.DateOffset(months=36)).date()), str(end.date()),
    )
    res = pairtrade.compute_pair(px["V"], px["MA"], z_window=60)
    tag, text = pairtrade.verdict(res)
    sig = pairtrade.signal(res["cur_z"])
    ratio = pairtrade.rebased_ratio(px["V"], px["MA"])
    assert abs(float(ratio.iloc[0]) - 100.0) < 1e-6
    print(
        f"       beta={res['beta']:.3f} EGp={res['eg_p']:.3f} ADFp={res['adf_p']:.3f} "
        f"HL={res['half_life']:.0f} z={res['cur_z']:+.2f} → {tag}"
    )


def t_benchmarks():
    assert benchmarks.watchlist_core("美股", "支付 / 金融科技") == "V"
    assert "MA" in benchmarks.watchlist_ref("美股", "支付 / 金融科技")
    assert benchmarks.watchlist_meta("美股", "支付 / 金融科技")["grade"] == "A"
    assert benchmarks.benchmark_for_sector("美股", "半導體") == "SOXX"
    assert benchmarks.watchlist_tickers("台股", "金控").startswith("2881")
    assert sectors.is_defensive("美股", "XLU") and not sectors.is_defensive("美股", "XLK")
    assert sectors.display_name("美股", "GLD").startswith("🛡️")


def t_patterns_synthetic():
    """合成資料驗證新型態：壓力段RS新高、領漲背離、狀態欄。"""
    import numpy as np

    dates = pd.date_range("2025-01-01", periods=7, freq="30D")
    legs = []
    for k in range(6):
        legs.append(analysis.Leg(start=dates[k], end=dates[k + 1],
                                 direction="down" if k % 2 == 0 else "up",
                                 ongoing=(k == 5)))
    cols = [l.label() for l in legs]
    qual = pd.DataFrame.from_dict({
        #          ▼            ▲        ▼            ▲        ▼        ▲
        "PRESS": ["逆勢抗跌",  "領漲",  "逆勢抗跌",  "領漲",  "抗跌",  "領漲"],
        "DIVG":  ["抗跌",      "領漲",  "抗跌",      "領漲",  "抗跌",  "領漲"],
    }, orient="index", columns=cols)
    idx = pd.date_range(dates[0], dates[-1], freq="D")
    n = len(idx)
    # PRESS：RS 一路創高（含下跌段） → 壓力段RS新高
    press = pd.Series(np.linspace(1.0, 2.0, n), index=idx)
    # DIVG：每個上漲段一個波峰、高度遞減（1.5→1.3→1.15） → 領漲背離
    divg = pd.Series(1.0, index=idx)
    for k, h in zip([1, 3, 5], [0.5, 0.3, 0.15]):
        mid = legs[k].start + (legs[k].end - legs[k].start) / 2
        mask = (idx >= legs[k].start) & (idx <= legs[k].end)
        d = (idx[mask] - mid).days.astype(float)
        divg.loc[mask] = 1.0 + h * np.exp(-((d / 7.0) ** 2))
    rs = pd.DataFrame({"PRESS": press, "DIVG": divg})
    sig, _ = analysis.detect_patterns(qual, legs, rs, ["PRESS", "DIVG"],
                                      analysis.pattern_names())
    got = {(r["代號"], r["型態"]) for _, r in sig.iterrows()}
    assert ("PRESS", "壓力段RS新高") in got, f"壓力段RS新高未觸發: {got}"
    assert ("DIVG", "領漲背離") in got, f"領漲背離未觸發: {got}"
    assert ("DIVG", "壓力段RS新高") not in got, "RS 段高點遞減者不應觸發壓力段新高"
    assert set(sig["狀態"]) <= {"✅已確認", "⏳進行中"}
    assert (sig[sig["期間"] == cols[-1]]["狀態"] == "⏳進行中").all()
    # 統計：應驗率表可產出且無進行中樣本
    rel = pd.DataFrame(0.05, index=["PRESS", "DIVG"], columns=cols)
    stats = analysis.pattern_forward_stats(qual, legs, rs, ["PRESS", "DIVG"], rel)
    assert not stats.empty and (stats["樣本數"] >= 1).all()


def t_backtest_synthetic():
    """合成均值回歸配對：回測應產生交易、勝率合理、欄位齊全。"""
    import numpy as np

    rng = np.random.default_rng(42)
    n = 800
    idx = pd.bdate_range("2023-01-02", periods=n)
    # B = 隨機漫步；A = B + 定態 AR(1) spread → 完美共整合
    lb = np.cumsum(rng.normal(0, 0.01, n)) + np.log(100)
    sp = np.zeros(n)
    for i in range(1, n):
        sp[i] = 0.97 * sp[i - 1] + rng.normal(0, 0.01)
    la = lb + sp
    a = pd.Series(np.exp(la), index=idx)
    b = pd.Series(np.exp(lb), index=idx)
    bt = pairtrade.backtest_pair(a, b, z_window=60, entry=2.0, stop=3.5)
    st_ = bt["stats"]
    assert st_["筆數"] >= 3, f"交易太少: {st_}"
    assert st_["勝率%"] >= 60, f"合成完美共整合勝率應高: {st_}"
    assert {"進場日", "方向", "進場z", "出場日", "出場原因", "持有天數", "報酬%"} <= set(bt["trades"].columns)
    assert len(bt["equity"]) == n
    print(f"       trades={st_['筆數']} win={st_['勝率%']}% total={st_['總報酬%']}%")


def t_peers():
    import peers

    problems = peers.integrity_check()
    assert not problems, problems[:5]
    rec = peers.recommend("NVDA")
    assert rec["sector_key"] == "ai_gpu"
    assert [d["ticker"] for d in rec["peers"]] == ["AMD"]
    assert any(d["ticker"] == "AVGO" for d in rec["related"]), "綜合型剔除註記缺失"
    rec2 = peers.recommend("mrvl")  # 小寫 + 多板塊
    assert rec2["sector_key"] == "ai_asic_networking" and len(rec2["sectors_all"]) == 2
    rec3 = peers.recommend("MRVL", "ai_connectivity_silicon")  # 板塊切換
    assert {d["ticker"] for d in rec3["peers"]} == {"ALAB", "CRDO"}
    assert peers.recommend("IONQ")["rating"] == "C"
    assert peers.recommend("V")["rating"] == "A"
    assert peers.recommend("ZZZZ") is None
    db_n = len(peers.lookup_sectors("TSLA"))
    assert db_n == 1  # TSLA 特例：主籃 ai_app_software
    print(f"       sectors=46 tickers={sum(1 for _ in __import__('json').load(open('peers_us.json', encoding='utf-8'))['ticker_index'])}")


check("data.fetch_prices（美股+基準）", t_data)
check("data.fetch_prices（台股 .TW/.TWO 退補）", t_data_tw)
check("analysis.analyze + detect_patterns", t_analyze)
check("analysis：新型態（壓力段RS新高/領漲背離/狀態欄/統計）", t_patterns_synthetic)
check("pairtrade.backtest_pair（合成共整合）", t_backtest_synthetic)
check("peers：同質性推薦（完整性/反查/多板塊/評級）", t_peers)
check("rotation：RRG full/tail/summary/regime/signals", t_rotation)
check("pairtrade：V↔MA 共整合檢定", t_pair)
check("benchmarks/sectors helpers", t_benchmarks)

# ---------------------------------------------------------------- AppTest
print("== AppTest（三分頁 run 路徑）==")
from streamlit.testing.v1 import AppTest


def t_home():
    at = AppTest.from_file("home.py", default_timeout=120)
    at.session_state["market"] = "美股"
    at.session_state["core_raw"] = "NVDA"
    at.session_state["ref_raw"] = "AMD AVGO"
    at.run()
    assert not at.exception, at.exception[0].value if at.exception else ""
    # 點「推薦同質參考股」→ ref_raw 應被 ai_gpu 板塊 peers 覆寫為 AMD
    btns = [b for b in at.button if "推薦同質參考股" in (b.label or "")]
    assert btns, "找不到推薦按鈕"
    btns[0].click()
    at.run()
    assert not at.exception, at.exception[0].value if at.exception else ""
    assert at.session_state["ref_raw"] == "AMD", at.session_state["ref_raw"]


def t_rot_page():
    at = AppTest.from_file("sector_rotation.py", default_timeout=180)
    at.session_state["rot_run"] = True
    at.run()
    assert not at.exception, at.exception[0].value if at.exception else ""


def t_pair_page():
    at = AppTest.from_file("pair_trading.py", default_timeout=120)
    at.session_state["pair_run"] = True
    at.session_state["pair_a"] = "V"
    at.session_state["pair_b"] = "MA"
    at.run()
    assert not at.exception, at.exception[0].value if at.exception else ""


check("home.py（個股相對強弱）", t_home)
check("sector_rotation.py（板塊輪動）", t_rot_page)
check("pair_trading.py（配對交易）", t_pair_page)

print(f"\n{'全部通過 ✅' if FAIL == 0 else f'{FAIL} 項失敗 ❌'}")
sys.exit(1 if FAIL else 0)
