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


check("data.fetch_prices（美股+基準）", t_data)
check("data.fetch_prices（台股 .TW/.TWO 退補）", t_data_tw)
check("analysis.analyze + detect_patterns", t_analyze)
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
