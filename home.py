# -*- coding: utf-8 -*-
"""個股相對強弱頁：核心標的 vs 參考股（Wyckoff 比較式相對強弱）。

注意：st.set_page_config 只在 app.py（路由）呼叫，此檔不可再呼叫。
"""
from __future__ import annotations

import datetime as dt
import math
import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import analysis
import benchmarks
import data
import peers
import ui


# ---------------------------------------------------------------------------
# 資料抓取（快取 15 分鐘，對齊 yfinance 延遲）
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900, show_spinner="下載價格資料中…")
def cached_fetch(tickers: tuple[str, ...], bench: str | None, market: str, start: str, end: str):
    px, resolved, missing = data.fetch_prices(list(tickers), bench, market, start, end)
    # 全軍覆沒幾乎必是 Yahoo 限流/斷線（清單全打錯的機率極低）。
    # 拋例外 → 失敗不進快取，重跑即可重試。
    if px.empty and missing:
        raise data.FetchQualityError("、".join(missing))
    return px, resolved, missing


def parse_tickers(raw: str) -> list[str]:
    toks = [t.upper() for t in re.split(r"[\s,]+", raw) if t.strip()]
    return list(dict.fromkeys(toks))


# ---------------------------------------------------------------------------
# 預設清單 callback：選了自動帶入核心/參考股、切市場時選單歸位
# ---------------------------------------------------------------------------
def _apply_preset():
    market = st.session_state.get("market", "台股")
    name = st.session_state.get("preset_pick", "")
    core_tk = benchmarks.watchlist_core(market, name)
    ref_tk = benchmarks.watchlist_ref(market, name)
    if core_tk:
        st.session_state["core_raw"] = core_tk
        st.session_state["ref_raw"] = ref_tk


def _on_market_change():
    st.session_state["preset_pick"] = "（自訂 / 清空）"


def _recommend_peers():
    """依核心標的反查同質性研究清單，推薦 peers 填入參考股欄。"""
    raw = (st.session_state.get("core_raw") or "").upper()
    toks = [t for t in re.split(r"[\s,]+", raw) if t.strip()]
    core = toks[0] if toks else ""
    if not core:
        st.session_state["peer_rec"] = {"miss": True, "ticker": ""}
        return
    rec = peers.recommend(core)
    if rec is None:
        st.session_state["peer_rec"] = {"miss": True, "ticker": core}
        return
    st.session_state["peer_rec"] = rec
    st.session_state["peer_sector_pick"] = rec["sector_key"]
    st.session_state["ref_raw"] = " ".join(d["ticker"] for d in rec["peers"])


def _apply_peer_sector():
    """多板塊標的（MRVL/HOOD/UUUU…）切換板塊後重新帶入 peers。"""
    rec = st.session_state.get("peer_rec") or {}
    if rec.get("miss"):
        return
    new = peers.recommend(rec["ticker"], st.session_state.get("peer_sector_pick"))
    if new:
        st.session_state["peer_rec"] = new
        st.session_state["ref_raw"] = " ".join(d["ticker"] for d in new["peers"])


def _shift_asof(days: int):
    """復盤步進器：把基準日往前/後移，並夾在允許範圍內。"""
    cur = st.session_state.get("as_of", dt.date.today() - dt.timedelta(days=90))
    lo = dt.date.today() - dt.timedelta(days=365 * 8)
    hi = dt.date.today()
    st.session_state["as_of"] = min(max(cur + dt.timedelta(days=days), lo), hi)


for key in ("core_raw", "ref_raw"):
    if key not in st.session_state:
        st.session_state[key] = ""

# ---------------------------------------------------------------------------
# 側邊欄
# ---------------------------------------------------------------------------
ui.inject()
with st.sidebar:
    st.header("設定")
    market = st.selectbox("市場", ["台股", "美股"], index=0, key="market", on_change=_on_market_change)
    st.selectbox(
        "預設清單（同質性分級，選了自動帶入、可再增刪）",
        benchmarks.watchlist_options(market),
        key="preset_pick",
        on_change=_apply_preset,
    )
    meta = benchmarks.watchlist_meta(market, st.session_state.get("preset_pick", ""))
    if meta:
        st.caption(
            f"同質性 **{meta['grade']}** 級｜{meta['use']}｜{meta['note']}"
        )
    core_raw = st.text_input(
        "核心標的（分析主角，1 檔）", key="core_raw", placeholder="台股例：2330／美股例：NVDA"
    )
    if market == "美股":
        st.button(
            "🧲 依核心標的推薦同質參考股",
            on_click=_recommend_peers,
            width="stretch",
            help=f"依同質性研究（{peers.as_of()}，46 板塊/340+ 檔）反查核心標的所屬板塊，"
                 "自動帶入同質 peers（綜合型已剔除）。",
        )
        _rec = st.session_state.get("peer_rec")
        _cur = [t for t in re.split(r"[\s,]+", (st.session_state.get("core_raw") or "").upper()) if t]
        _cur = _cur[0] if _cur else ""
        if _rec and _rec.get("ticker", "") == _cur:
            if _rec.get("miss"):
                st.caption(
                    "請先輸入核心標的再按推薦。" if not _cur
                    else f"「{_cur}」不在同質性研究清單（46 板塊/340+ 檔）內，暫無推薦；請手動輸入參考股。"
                )
            else:
                if len(_rec["sectors_all"]) > 1:
                    st.selectbox(
                        "此標的橫跨多板塊，切換：",
                        _rec["sectors_all"],
                        key="peer_sector_pick",
                        format_func=peers.sector_name,
                        on_change=_apply_peer_sector,
                    )
                st.caption(f"**{_rec['name_zh']}**（同質性 **{_rec['rating']}** 級）｜{_rec['driver']}")
                if _rec["rating"] == "C":
                    st.warning(
                        "C 級：僅主題連動、成分基本面異質——只適合動能監控，"
                        "**不建議配對**，RS 標籤解讀需保守。"
                    )
                if _rec["related"]:
                    st.caption("綜合型已剔除：" + "、".join(
                        f"{d['ticker']}（{d['reason']}）" for d in _rec["related"]))
                with st.expander("推薦明細與注意事項"):
                    st.dataframe(
                        pd.DataFrame(_rec["peers"]).rename(columns={
                            "ticker": "代碼", "company": "公司", "cap_tier": "市值層",
                            "purity": "純度", "notes": "備註"}),
                        width="stretch", hide_index=True,
                    )
                    if _rec["pair_candidates"]:
                        st.caption("配對候選（需自行到配對交易頁跑協整檢定）：" +
                                   "；".join("↔".join(p) for p in _rec["pair_candidates"]))
                    if _rec["notes"]:
                        st.caption(f"板塊備註：{_rec['notes']}")
                    st.caption("市值層為 2026-07 概估；成分與評級建議每季重新盤點。")
    ref_raw = st.text_area(
        "參考股（同質群體，空白 / 逗號 / 換行分隔）",
        height=110,
        key="ref_raw",
        placeholder="台股例：2303 6770\n美股例：AMD AVGO",
    )
    use_benchmark = st.checkbox("加入板塊基準比較（選填）", value=False)
    benchmark_ticker = None
    if use_benchmark:
        sector = st.selectbox("板塊", benchmarks.sector_options(market))
        benchmark_ticker = benchmarks.benchmark_for_sector(market, sector)
        st.caption(f"基準：{benchmark_ticker}")
        if market == "台股" and benchmark_ticker == "DRAM":
            st.info("台股無純 DRAM ETF，以美元計價的 US DRAM 代理，RS 會夾帶匯率漂移。")

    align_start = st.checkbox(
        "對齊共同起算日（全部裁到最晚上市者的首日）", value=False,
        help="開啟後跨窗口比較最公平，但會犧牲較早的歷史結構段。",
    )
    replay = st.checkbox("🕰️ 復盤模式（以指定日期當作『當下』）", value=False)
    as_of = None
    if replay:
        if "as_of" not in st.session_state:
            st.session_state["as_of"] = dt.date.today() - dt.timedelta(days=90)
        as_of = st.date_input(
            "復盤基準日",
            min_value=dt.date.today() - dt.timedelta(days=365 * 8),
            max_value=dt.date.today(),
            key="as_of",
        )
        s1, s2, s3, s4 = st.columns(4)
        s1.button("◀ 月", on_click=_shift_asof, args=(-30,), width="stretch",
                  help="基準日往前 30 天")
        s2.button("◀ 週", on_click=_shift_asof, args=(-7,), width="stretch",
                  help="基準日往前 7 天")
        s3.button("週 ▶", on_click=_shift_asof, args=(7,), width="stretch",
                  help="基準日往後 7 天")
        s4.button("月 ▶", on_click=_shift_asof, args=(30,), width="stretch",
                  help="基準日往後 30 天")

    st.divider()
    st.subheader("結構參數")
    zz_threshold = st.slider("ZigZag 門檻 (%)", 3.0, 15.0, 6.0, 0.5) / 100.0
    min_bars = st.slider("最短結構區間（交易日）", 3, 30, 10)
    lookback = st.slider("回看月數", 6, 36, 24)

    st.divider()
    sel_patterns = st.multiselect(
        "Pattern 訊號（強⭐／弱⚠️）",
        options=analysis.pattern_names(),
        default=analysis.pattern_names("bull"),
    )

# ---------------------------------------------------------------------------
# 抓資料
# ---------------------------------------------------------------------------
st.title("📊 個股相對強弱")
st.caption(
    "RS = 個股 / 基準。時間軸依參考序列的 ZigZag 高低點切成結構段（▲上漲段 / ▼下跌段）。"
    "顏色 = 相對強弱（綠 = 贏過族群、紅 = 輸給族群），**不是**絕對漲跌。"
)

core_list = parse_tickers(core_raw)
ref_list = [t for t in parse_tickers(ref_raw) if t not in core_list]
tickers = core_list + ref_list
if not core_list or len(tickers) < 2:
    st.warning("請輸入 1 檔核心標的與至少 1 檔參考股（可用側邊欄「預設清單」快速帶入）。")
    st.stop()
if len(core_list) > 1:
    st.info(f"核心標的僅取第一檔：{core_list[0]}，其餘視為參考股。")
    ref_list = core_list[1:] + ref_list
    core_list = core_list[:1]

end = pd.Timestamp(as_of) if (replay and as_of) else pd.Timestamp.today().normalize()
start = end - pd.DateOffset(months=lookback)

# 抓取窗口刻意比分析窗口寬：起點取到「季度下緣」、迄點一律抓到今天，
# 這樣復盤步進（±週/±月）多半命中快取，不用重新下載。
fetch_start = start.to_period("Q").start_time
fetch_end = pd.Timestamp.today().normalize()
try:
    prices, resolved, missing = cached_fetch(
        tuple(tickers), benchmark_ticker, market, str(fetch_start.date()), str(fetch_end.date())
    )
except data.FetchQualityError as ex:
    st.error(
        "📡 Yahoo Finance 疑似限流（整批清單都抓不到）。"
        "這次的失敗結果**不會**進快取——請等 1〜2 分鐘後重跑即可。"
        f"\n\n本次缺漏：{ex}（若代碼確定正確，就是限流；否則請檢查代碼）"
    )
    st.stop()
if missing:
    st.warning(f"以下代碼無資料，已略過：{', '.join(missing)}")
if prices.empty:
    st.error("復盤基準日之前沒有足夠資料，請調整日期或清單。" if replay else "抓不到任何資料，請確認代碼。")
    st.stop()

# 復盤核心：截斷到 [窗口起點, 基準日]，基準日之後的資料一律不看
prices = prices.loc[start:end].dropna(how="all")
if prices.empty:
    st.error("復盤基準日之前沒有足夠資料，請調整日期或清單。")
    st.stop()
# 截斷後全空的欄（基準日之前尚未上市）視同無資料
empty_cols = [c for c in prices.columns if prices[c].dropna().empty]
if empty_cols:
    prices = prices.drop(columns=empty_cols)
    resolved = {k: v for k, v in resolved.items() if v not in empty_cols}
    st.warning(f"以下代碼在基準日之前沒有資料，已略過：{', '.join(empty_cols)}")

core_col = resolved.get(core_list[0])
stock_cols = [resolved[t] for t in tickers if t in resolved]
sector_col = resolved.get(data.SECTOR_KEY)
if core_col is None:
    st.error(f"核心標的 {core_list[0]} 抓不到資料，無法分析。")
    st.stop()
if len(stock_cols) < 2:
    st.error("有效資料不足 2 檔，無法比較。請確認代碼或調整復盤基準日。")
    st.stop()

# 對齊共同起算日：全部裁到最晚上市者首日
if align_start:
    first_dates = [prices[c].dropna().index[0] for c in stock_cols]
    common = max(first_dates)
    prices = prices.loc[common:]

# ---------------------------------------------------------------------------
# 分析
# ---------------------------------------------------------------------------
res = analysis.analyze(
    prices,
    stock_cols=stock_cols,
    sector_col=sector_col,
    pct=zz_threshold,
    min_bars=min_bars,
)
if res["struct_warn"]:
    st.warning(res["struct_warn"])
legs = res["legs"]
if not legs:
    st.error("以目前參數切不出結構段，請調低 ZigZag 門檻。")
    st.stop()

n_up = sum(1 for l in legs if l.direction == "up")
replay_note = f" 🕰️ **復盤基準日 {end.strftime('%Y-%m-%d')}**。" if (replay and as_of) else ""
st.markdown(
    f"**核心標的：`{core_col}`**　結構：以「{res['struct_name']}」切出 **{len(legs)} 段**"
    f"（▲{n_up} / ▼{len(legs) - n_up}），"
    f"門檻 {zz_threshold:.1%}、最短 {min_bars} 交易日、回看 {lookback} 個月。"
    f" 欄名尾端 `*` = 進行中（尚未確認反轉）。"
    + replay_note
)

# 個股上市日晚於窗口起點 → 公平性提醒（已知限制）
if not align_start:
    late = [
        t for t in stock_cols
        if prices[t].dropna().index[0] > prices.index[0] + pd.Timedelta(days=10)
    ]
    if late:
        st.info(
            f"上市/資料起日晚於窗口起點：{', '.join(late)}。"
            "其早期空白格為資料不足；可勾選側邊欄「對齊共同起算日」求公平比較。"
        )


# ---------------------------------------------------------------------------
# 熱力圖繪製（marks：Pattern 訊號 ⭐/⚠️ 注記；核心標的列名加 🎯）
# ---------------------------------------------------------------------------
def heatmap_fig(
    rel_df: pd.DataFrame,
    lab_df: pd.DataFrame,
    title: str,
    marks: dict[tuple[str, str], set[str]] | None = None,
) -> go.Figure:
    order = rel_df.mean(axis=1, skipna=True).sort_values().index
    rel = rel_df.loc[order] * 100.0
    lab = lab_df.loc[order]

    def cell_text(r: int, c: int) -> str:
        v = rel.iloc[r, c]
        if math.isnan(v):
            return ""
        mk = ""
        if marks:
            kinds = marks.get((rel.index[r], rel.columns[c])) or set()
            mk = ("⭐" if "bull" in kinds else "") + ("⚠️" if "bear" in kinds else "")
        return f"{lab.iloc[r, c]}<br>{v:+.1f}% {mk}".rstrip()

    text = [[cell_text(r, c) for c in range(rel.shape[1])] for r in range(rel.shape[0])]
    ylabels = [f"🎯 {t}" if t == core_col else t for t in rel.index]
    zmax = max(1.0, float(pd.DataFrame(rel).abs().max().max()))
    fig = go.Figure(
        go.Heatmap(
            z=rel.values,
            x=list(rel.columns),
            y=ylabels,
            zmid=0,
            zmin=-zmax,
            zmax=zmax,
            colorscale=ui.HEAT_DIVERGING,
            xgap=2,
            ygap=2,
            text=text,
            texttemplate="%{text}",
            textfont={"size": 10, "color": ui.HEAT_TEXT},
            hovertemplate="%{y} | %{x}<br>相對強弱 %{z:+.2f}%<extra></extra>",
            colorbar={"title": "相對強弱%"},
        )
    )
    fig.update_layout(
        title=title,
        height=max(360, 60 + 42 * rel.shape[0]),
        xaxis={"side": "bottom"},
        margin={"l": 80, "r": 20, "t": 50, "b": 60},
    )
    return ui.apply(fig)


tab_heat, tab_rank, tab_rs, tab_help = st.tabs(
    ["🔥 強弱熱力圖", "🏆 現況排名", "📈 個股 RS 線", "📖 使用說明"]
)

rel_df, lab_df = res["score_vs_group"], res["qual"]
rs_all = res["rs_lines"]
signals, pattern_marks = analysis.detect_patterns(
    lab_df, legs, rs_all, stock_cols, sel_patterns
)

with tab_heat:
    st.plotly_chart(
        heatmap_fig(rel_df, lab_df, "相對「族群平均（等權籃子）」", pattern_marks),
        width="stretch",
    )
    if res["score_vs_sector"] is not None:
        st.plotly_chart(
            heatmap_fig(res["score_vs_sector"], res["qual_vs_sector"], f"相對「板塊基準 {sector_col}」"),
            width="stretch",
        )
    st.markdown("#### 📌 型態訊號清單")
    if signals.empty:
        st.caption("目前選取的型態沒有偵測到訊號。")
    else:
        st.dataframe(signals, width="stretch", hide_index=True)
        st.download_button(
            "⬇️ 下載訊號 CSV",
            signals.to_csv(index=False).encode("utf-8-sig"),
            file_name="pattern_signals.csv",
            mime="text/csv",
        )
    with st.expander("📊 訊號統計：各型態在本族群的歷史應驗率"):
        stats_df = analysis.pattern_forward_stats(lab_df, legs, rs_all, stock_cols, rel_df)
        if stats_df.empty:
            st.caption("已確認的歷史訊號不足，無法統計。")
        else:
            st.dataframe(stats_df, width="stretch", hide_index=True)
            st.caption(
                "應驗定義：⭐ 訊號 → 下一段贏過族群；⚠️ 訊號 → 下一段輸給族群。"
                "只計「訊號段與下一段都已確認」的樣本（無前視）。"
                "**樣本數 < 5 的型態僅供參考**；本表反映的是這個族群在本窗口的歷史，不保證未來。"
            )
    with st.expander("標籤說明"):
        st.markdown(
            "- **綠（相對強）**：`領漲`（▲段贏過族群）、`逆勢抗跌`（▼段逆勢上漲）、`抗跌`（▼段跌得比族群少）\n"
            "- **紅（相對弱）**：`跟漲但落後`（▲段有漲但輸族群）、`落後下跌`（▲段反而下跌）、`同步破底`（▼段跌得比族群兇）\n"
            "- 紅格 ≠ 股價下跌，可能只是漲得比族群少。\n"
            "- `⭐` = 偵測到強勢型態、`⚠️` = 偵測到弱勢型態（詳見下方訊號清單）。"
        )

with tab_rank:
    rank_df = res["ranking"].copy()
    if res["score_vs_sector"] is not None:
        rel_bm, lab_bm = res["score_vs_sector"], res["qual_vs_sector"]
        last = rel_bm.columns[-1]
        rank_df[f"最新段 vs {sector_col}%"] = rank_df["代碼"].map(
            lambda t: round(rel_bm.loc[t, last] * 100, 2)
            if not math.isnan(rel_bm.loc[t, last])
            else math.nan
        )
        rank_df[f"最新段標籤 vs {sector_col}"] = rank_df["代碼"].map(lambda t: lab_bm.loc[t, last])
    rank_df["代碼"] = rank_df["代碼"].map(lambda t: f"🎯 {t}" if t == core_col else t)
    st.dataframe(rank_df, width="stretch", hide_index=True)
    st.download_button(
        "⬇️ 下載 CSV（Excel 可直接開）",
        rank_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="strength_ranking.csv",
        mime="text/csv",
    )
    with st.expander("資料涵蓋度"):
        st.dataframe(res["coverage"], width="stretch", hide_index=True)

with tab_rs:
    rs = rs_all
    picked = st.multiselect("顯示個股", list(rs.columns), default=list(rs.columns))
    fig = go.Figure()
    for leg in legs:  # ▼段淡紅底，結構一目了然
        if leg.direction == "down":
            fig.add_vrect(
                x0=leg.start, x1=leg.end, fillcolor=ui.DOWNLEG_FILL, line_width=0
            )
    for t in picked:
        width = 3.0 if t == core_col else 1.4
        fig.add_trace(go.Scatter(x=rs.index, y=rs[t], name=t, mode="lines", line={"width": width}))
    fig.add_hline(y=1.0, line_dash="dot", line_color=ui.COLORS["baseline"])
    fig.update_layout(
        title="RS = 個股 / 族群籃子（窗口起點 = 1.0；淡紅底 = 籃子▼下跌段；核心標的加粗）",
        height=520,
        legend={"orientation": "h", "y": -0.15},
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
    )
    st.plotly_chart(ui.apply(fig), width="stretch")

with tab_help:
    st.markdown(
        """
### 這頁在做什麼？
把 **核心標的** 放進一群 **高同質參考股** 裡，用 Wyckoff 比較式相對強弱回答：
「這檔股票在自己的族群裡，是領頭羊還是拖油瓶？」

### 怎麼讀？
1. **結構段**：不是固定 N 天，而是用參考序列（族群籃子或板塊基準）的 ZigZag
   高低點切段。▲上漲段看誰領漲、▼下跌段看誰抗跌。
2. **熱力圖**：一列一檔股票、一欄一個結構段。綠 = 該段贏過族群、紅 = 輸給族群。
   **紅色不代表下跌**，可能只是漲得比較少。
3. **標籤**：領漲 / 抗跌 / 逆勢抗跌（強）；跟漲但落後 / 落後下跌 / 同步破底（弱）。
4. **型態訊號**：抗跌後領漲、谷底翻強…等跨段組合，⭐強 / ⚠️弱 直接標在格子上。
5. **RS 線**：個股 ÷ 族群籃子，向上 = 相對走強。核心標的加粗顯示。

### 建議流程
先用預設清單（同質性 A 級最可靠）→ 看核心標的最新段標籤與排名 →
再用復盤模式回放歷史轉折點，驗證訊號在當時是否可操作。

### 已知限制
- 上市較晚的股票早期格子是「資料不足」；勾「對齊共同起算日」可強制公平比較。
- 台股板塊基準若用美元計價代理（DRAM），RS 會夾帶匯率漂移。
- yfinance 資料延遲約 15 分鐘，且偶有缺漏；重要決策請以券商行情為準。
        """
    )
