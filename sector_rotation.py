# -*- coding: utf-8 -*-
"""板塊輪動頁：RRG（Relative Rotation Graph）+ 結構強弱熱力圖。

注意：st.set_page_config 只在 app.py（路由）呼叫，此檔不可再呼叫。
"""
from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import analysis
import data
import rotation
import sectors

# Dark24 高對比調色盤（plotly.express.colors.qualitative.Dark24）
_PALETTE = [
    "#2E91E5", "#E15F99", "#1CA71C", "#FB0D0D", "#DA16FF", "#222A2A",
    "#B68100", "#750D86", "#EB663B", "#511CFB", "#00A08B", "#FB00D1",
    "#FC0080", "#B2828D", "#6C7C32", "#778AAE", "#862A16", "#A777F1",
    "#620042", "#1616A7", "#DA60CA", "#6C4516", "#0D2A63", "#AF0038",
]

_QUAD_STYLE = {
    "領先": ("🟩", "rgba(46,125,50,0.08)"),
    "改善": ("🟦", "rgba(25,118,210,0.08)"),
    "轉弱": ("🟨", "rgba(249,168,37,0.10)"),
    "落後": ("🟥", "rgba(198,40,40,0.08)"),
}


# ---------------------------------------------------------------------------
# 資料抓取（快取 15 分鐘）
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900, show_spinner="下載板塊 ETF 資料中…")
def cached_fetch(tickers: tuple[str, ...], bench: str, market: str, start: str, end: str):
    return data.fetch_prices(list(tickers), bench, market, start, end)


def build_color_map(cols: list[str]) -> dict[str, str]:
    return {c: _PALETTE[i % len(_PALETTE)] for i, c in enumerate(cols)}


# ---------------------------------------------------------------------------
# 圖表元件
# ---------------------------------------------------------------------------
def _add_quadrant_backdrop(fig: go.Figure, xr: tuple[float, float], yr: tuple[float, float]) -> None:
    """四象限底色 + 中心十字線 + 角落標籤（半透明白底）。"""
    quads = [
        (100, xr[1], 100, yr[1], "rgba(46,125,50,0.06)", "領先 Leading", xr[1], yr[1], "right", "top"),
        (100, xr[1], yr[0], 100, "rgba(249,168,37,0.07)", "轉弱 Weakening", xr[1], yr[0], "right", "bottom"),
        (xr[0], 100, yr[0], 100, "rgba(198,40,40,0.06)", "落後 Lagging", xr[0], yr[0], "left", "bottom"),
        (xr[0], 100, 100, yr[1], "rgba(25,118,210,0.06)", "改善 Improving", xr[0], yr[1], "left", "top"),
    ]
    for x0, x1, y0, y1, color, label, ax, ay, xanchor, yanchor in quads:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1, fillcolor=color, line_width=0, layer="below")
        fig.add_annotation(
            x=ax, y=ay, text=label, showarrow=False,
            xanchor=xanchor, yanchor=yanchor,
            font={"size": 12, "color": "#555"},
            bgcolor="rgba(255,255,255,0.65)",
        )
    fig.add_hline(y=100, line_color="#999", line_width=1)
    fig.add_vline(x=100, line_color="#999", line_width=1)


def _axis_range(rrg: dict[str, pd.DataFrame]) -> tuple[tuple[float, float], tuple[float, float]]:
    xs = pd.concat([df["ratio"] for df in rrg.values()])
    ys = pd.concat([df["mom"] for df in rrg.values()])
    def rng(s: pd.Series) -> tuple[float, float]:
        lo, hi = float(s.min()), float(s.max())
        lo, hi = min(lo, 99.0), max(hi, 101.0)
        pad = max(0.4, (hi - lo) * 0.10)
        return lo - pad, hi + pad
    return rng(xs), rng(ys)


def rrg_figure(
    rrg: dict[str, pd.DataFrame],
    market: str,
    mode: str,
    focus_cols: list[str],
    color_map: dict[str, str],
) -> go.Figure:
    """快照 = 每板塊一個大點；軌跡 = 畫尾巴。focus 非空時其餘淡化。"""
    fig = go.Figure()
    xr, yr = _axis_range(rrg)
    _add_quadrant_backdrop(fig, xr, yr)
    for col, df in rrg.items():
        name = sectors.display_name(market, col)
        dim = bool(focus_cols) and col not in focus_cols
        opacity = 0.18 if dim else 1.0
        color = color_map.get(col, "#333")
        symbol = "diamond" if sectors.is_defensive(market, col) else "circle"
        if mode == "軌跡" and len(df) > 1:
            fig.add_trace(
                go.Scatter(
                    x=df["ratio"], y=df["mom"], mode="lines+markers",
                    line={"color": color, "width": 1.6},
                    marker={"size": 5, "color": color},
                    opacity=opacity * 0.75, name=name, legendgroup=col,
                    showlegend=False, hoverinfo="skip",
                )
            )
        last = df.iloc[-1]
        fig.add_trace(
            go.Scatter(
                x=[last["ratio"]], y=[last["mom"]],
                mode="markers+text",
                marker={"size": 14, "color": color, "symbol": symbol,
                        "line": {"width": 1, "color": "white"}},
                text=[name], textposition="bottom right",
                textfont={"size": 11, "color": color},
                opacity=opacity, name=name, legendgroup=col,
                hovertemplate=(
                    f"{name}<br>RS-Ratio %{{x:.2f}}<br>RS-Mom %{{y:.2f}}"
                    f"<br>{last['quadrant']}（{df.index[-1].strftime('%Y-%m-%d')}）<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        height=620,
        xaxis={"title": "RS-Ratio（相對趨勢）", "range": list(xr)},
        yaxis={"title": "RS-Momentum（相對動能）", "range": list(yr)},
        showlegend=False,
        margin={"l": 50, "r": 30, "t": 30, "b": 50},
    )
    return fig


def rrg_animated_figure(
    full: dict[str, pd.DataFrame],
    market: str,
    color_map: dict[str, str],
    span: int,
    trail: int = 2,
) -> go.Figure | None:
    """輪動回放：plotly frames + 時間軸 slider + 播放/暫停。

    每幀只畫「現在＋上一點」共 trail 點的短箭，slider 預設停在最新期。
    全客戶端運算，不重抓資料。
    """
    all_dates = sorted(set().union(*[set(df.index) for df in full.values()]))
    dates = all_dates[-span:]
    if len(dates) < 2:
        return None
    tail = {col: df for col, df in full.items()}
    xr, yr = _axis_range({c: d[d.index.isin(dates)] for c, d in tail.items() if not d[d.index.isin(dates)].empty})

    def frame_traces(t: pd.Timestamp) -> list[go.Scatter]:
        traces = []
        for col, df in tail.items():
            name = sectors.display_name(market, col)
            color = color_map.get(col, "#333")
            symbol = "diamond" if sectors.is_defensive(market, col) else "circle"
            seg = df.loc[:t].tail(trail)
            if seg.empty:
                traces.append(go.Scatter(x=[], y=[], mode="markers", name=name))
                continue
            texts = [""] * (len(seg) - 1) + [name]
            sizes = [6] * (len(seg) - 1) + [13]
            traces.append(
                go.Scatter(
                    x=seg["ratio"], y=seg["mom"],
                    mode="lines+markers+text",
                    line={"color": color, "width": 1.5},
                    marker={"size": sizes, "color": color, "symbol": symbol,
                            "line": {"width": 1, "color": "white"}},
                    text=texts, textposition="bottom right",
                    textfont={"size": 10, "color": color},
                    name=name,
                    hovertemplate=f"{name}<br>RS-Ratio %{{x:.2f}}<br>RS-Mom %{{y:.2f}}<extra></extra>",
                )
            )
        return traces

    labels = [d.strftime("%Y-%m-%d") for d in dates]
    frames = [go.Frame(data=frame_traces(d), name=lab) for d, lab in zip(dates, labels)]
    fig = go.Figure(data=frames[-1].data, frames=frames)
    _add_quadrant_backdrop(fig, xr, yr)

    steps = [
        {
            "args": [[lab], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
            "label": lab,
            "method": "animate",
        }
        for lab in labels
    ]
    fig.update_layout(
        height=620,
        xaxis={"title": "RS-Ratio（相對趨勢）", "range": list(xr)},
        yaxis={"title": "RS-Momentum（相對動能）", "range": list(yr)},
        showlegend=False,
        margin={"l": 50, "r": 30, "t": 30, "b": 20},
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "x": 0.0, "y": -0.08, "xanchor": "left", "yanchor": "top",
                "buttons": [
                    {
                        "label": "▶ 播放",
                        "method": "animate",
                        "args": [None, {"frame": {"duration": 450, "redraw": False},
                                        "fromcurrent": True, "transition": {"duration": 250}}],
                    },
                    {
                        "label": "⏸ 暫停",
                        "method": "animate",
                        "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                          "mode": "immediate"}],
                    },
                ],
            }
        ],
        sliders=[
            {
                "steps": steps,
                "active": len(steps) - 1,  # 預設停在最新期
                "x": 0.12, "y": -0.05, "len": 0.88,
                "currentvalue": {"prefix": "期別：", "font": {"size": 13}},
            }
        ],
    )
    return fig


def render_quadrant_cards(summary: pd.DataFrame) -> None:
    """現況象限一覽卡：四欄（🟩領先 / 🟦改善 / 🟨轉弱 / 🟥落後）。"""
    cols = st.columns(4)
    for col_ui, quad in zip(cols, rotation.QUADRANT_ORDER):
        icon, _ = _QUAD_STYLE[quad]
        with col_ui:
            st.markdown(f"**{icon} {quad}**")
            sub = summary[summary["象限"] == quad]
            if sub.empty:
                st.caption("—")
            for _, row in sub.iterrows():
                st.caption(f"{row['板塊']}｜{row['RS-Ratio']:.1f}")


def style_signals(df: pd.DataFrame):
    """「多空」欄上色：利多綠 / 利空紅 / 中性灰。"""
    color = {"利多": "color: #2e7d32; font-weight: 600",
             "利空": "color: #c62828; font-weight: 600",
             "中性": "color: #757575"}
    return df.style.map(lambda v: color.get(v, ""), subset=["多空"])


def heatmap_fig(rel_df: pd.DataFrame, lab_df: pd.DataFrame, title: str) -> go.Figure:
    order = rel_df.mean(axis=1, skipna=True).sort_values().index
    rel = rel_df.loc[order] * 100.0
    lab = lab_df.loc[order]

    def cell_text(r: int, c: int) -> str:
        v = rel.iloc[r, c]
        if math.isnan(v):
            return ""
        return f"{lab.iloc[r, c]}<br>{v:+.1f}%"

    text = [[cell_text(r, c) for c in range(rel.shape[1])] for r in range(rel.shape[0])]
    zmax = max(1.0, float(pd.DataFrame(rel).abs().max().max()))
    fig = go.Figure(
        go.Heatmap(
            z=rel.values, x=list(rel.columns), y=list(rel.index),
            zmid=0, zmin=-zmax, zmax=zmax, colorscale="RdYlGn",
            text=text, texttemplate="%{text}", textfont={"size": 10},
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
    return fig


# ---------------------------------------------------------------------------
# 側邊欄
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("板塊輪動設定")
    market = st.selectbox("市場", ["美股", "台股"], index=0, key="rot_market")
    all_sectors = list(sectors.rotation_sectors(market).keys())
    sel_sectors = st.multiselect(
        "板塊（🛡️ = 防禦型）",
        options=all_sectors,
        default=all_sectors,
        format_func=lambda t: sectors.display_name(market, t),
        key=f"rot_sectors_{market}",
    )
    freq = st.selectbox("頻率", list(rotation.FREQ_PARAMS.keys()), index=0)
    lookback = st.slider("回看月數", 6, 36, 18)
    view_mode = st.radio("顯示模式", ["快照", "軌跡"], horizontal=True)
    tail_len = 1
    if view_mode == "軌跡":
        tail_len = st.slider("軌跡長度（期）", 3, 20, 8)
    focus = st.multiselect(
        "聚焦板塊（選了只突顯，其餘淡化）",
        options=sel_sectors,
        format_func=lambda t: sectors.display_name(market, t),
        key=f"rot_focus_{market}",
    )
    replay_span = st.slider("輪動回放跨度（期）", 8, 60, 26)
    signal_lookback = st.slider("訊號偵測回看（期）", 4, 20, 8)
    with st.expander("RRG 進階參數"):
        use_default = st.checkbox("用頻率預設", value=True)
        d_w, d_m = rotation.FREQ_PARAMS[freq]
        if use_default:
            window, mom_window = d_w, d_m
            st.caption(f"正規化窗 {d_w}、動能回看 {d_m}（{freq}預設）")
        else:
            window = st.slider("正規化滾動窗（期）", 6, 120, d_w)
            mom_window = st.slider("動能回看（期）", 1, 20, d_m)
    with st.expander("熱力圖進階"):
        hm_pct = st.slider("ZigZag 門檻 (%)", 3.0, 15.0, 5.0, 0.5) / 100.0
        hm_min_bars = st.slider("最短結構區間（交易日）", 3, 30, 8)
    go_btn = st.button("🚀 開始分析", type="primary", width="stretch")

# ---------------------------------------------------------------------------
# 主畫面
# ---------------------------------------------------------------------------
st.title("🔄 板塊輪動")
st.caption(
    "RRG：x = RS-Ratio（板塊 ÷ 大盤的相對趨勢）、y = RS-Momentum（相對動能），中心 100。"
    "順時針輪動：落後 → 改善 → 領先 → 轉弱 → 落後。"
    "（JdK 指標之公開重現，非 StockCharts 專有公式）"
)

if go_btn:
    st.session_state["rot_run"] = True
if not st.session_state.get("rot_run"):
    st.info("左側設好參數後按「🚀 開始分析」。")
    st.stop()
if len(sel_sectors) < 2:
    st.warning("請至少選 2 個板塊。")
    st.stop()

bench = sectors.rotation_benchmark(market)
end = pd.Timestamp.today().normalize()
start = end - pd.DateOffset(months=lookback)
prices, resolved, missing = cached_fetch(
    tuple(sel_sectors), bench, market, str(start.date()), str(end.date())
)
if missing:
    st.warning(f"以下代碼無資料，已略過：{', '.join(missing)}")
bench_col = resolved.get(data.SECTOR_KEY)
sector_cols = [resolved[t] for t in sel_sectors if t in resolved]
if not bench_col or len(sector_cols) < 2:
    st.error("大盤基準或板塊資料不足，無法計算。")
    st.stop()

full = rotation.compute_rrg_full(prices, sector_cols, bench_col, freq, window, mom_window)
if not full:
    st.error("資料長度不足以計算 RRG（正規化窗 + 動能回看太長），請放寬回看月數或調小參數。")
    st.stop()
rrg = {k: v.tail(max(tail_len, 1)) for k, v in full.items()}
color_map = build_color_map(sector_cols)
focus_cols = [resolved.get(t, t) for t in focus]

tab_rrg, tab_heat, tab_help = st.tabs(["🧭 RRG 輪動圖", "🔥 結構強弱熱力圖", "📖 使用說明"])

with tab_rrg:
    # 1. risk-on/off 提示
    regime = rotation.risk_regime(full, market)
    st.markdown(f"##### {regime}")

    # 2. 現況象限一覽卡
    summary = rotation.rrg_summary(full, market, sectors.display_name)
    render_quadrant_cards(summary)
    st.divider()

    # 3. 快照 / 軌跡主圖
    st.plotly_chart(rrg_figure(rrg, market, view_mode, focus_cols, color_map), width="stretch")

    # 4. 輪動回放（動畫）
    st.markdown("#### 🎞️ 輪動回放")
    st.caption("拉時間軸或按 ▶ 播放看板塊在象限間怎麼轉；每幀畫「現在＋上一期」的短箭頭。")
    anim = rrg_animated_figure(full, market, color_map, replay_span, trail=2)
    if anim is None:
        st.caption("回放期數不足。")
    else:
        st.plotly_chart(anim, width="stretch")

    # 5. 輪動訊號表
    st.markdown("#### 📶 輪動訊號")
    signals = rotation.rrg_pattern_signals(full, market, sectors.display_name, signal_lookback)
    if signals.empty:
        st.caption(f"最近 {signal_lookback} 期沒有象限轉換訊號。")
    else:
        st.dataframe(style_signals(signals), width="stretch", hide_index=True)
        st.download_button(
            "⬇️ 下載訊號 CSV",
            signals.to_csv(index=False).encode("utf-8-sig"),
            file_name="rrg_signals.csv",
            mime="text/csv",
        )

    # 6. 象限一覽表
    st.markdown("#### 📋 象限一覽")
    st.dataframe(summary, width="stretch", hide_index=True)
    st.download_button(
        "⬇️ 下載一覽 CSV",
        summary.to_csv(index=False).encode("utf-8-sig"),
        file_name="rrg_summary.csv",
        mime="text/csv",
    )

with tab_heat:
    st.caption("各板塊 vs 大盤：依大盤的 ZigZag 結構切段，看每段誰領漲、誰抗跌。")
    res = analysis.analyze(
        prices, stock_cols=sector_cols, sector_col=bench_col,
        pct=hm_pct, min_bars=hm_min_bars,
    )
    if res["struct_warn"]:
        st.warning(res["struct_warn"])
    if not res["legs"]:
        st.error("以目前參數切不出結構段，請調低熱力圖 ZigZag 門檻。")
    else:
        rel, lab = res["score_vs_sector"], res["qual_vs_sector"]
        rel = rel.rename(index=lambda t: sectors.display_name(market, t))
        lab = lab.rename(index=lambda t: sectors.display_name(market, t))
        st.plotly_chart(heatmap_fig(rel, lab, f"板塊 vs 大盤（{bench_col}）"), width="stretch")

with tab_help:
    st.markdown(
        """
### RRG 怎麼看？
- **x 軸 RS-Ratio**：板塊 ÷ 大盤的相對趨勢，>100 = 跑贏大盤。
- **y 軸 RS-Momentum**：RS-Ratio 的變化速度，>100 = 相對強度還在加速。
- **四象限**：🟩 領先（強且加速）→ 🟨 轉弱（強但減速）→ 🟥 落後（弱且減速）→
  🟦 改善（弱但加速）→ 回到領先。健康輪動是**順時針**。

### 快照 vs 軌跡 vs 回放
- **快照**：只看「現在」各板塊的位置，最快掌握大局。
- **軌跡**：拖著最近 N 期的尾巴，看得出移動方向與速度。
- **回放**：把時間軸倒回去逐期播放，適合復盤「上一輪 risk-off 是誰先轉弱」。

### 訊號表怎麼用？
象限轉換就是訊號：落後→改善（動能翻正，開始留意）、改善→領先（確認轉強，
順勢配置）、領先→轉弱（動能熄火，考慮獲利了結）、轉弱→落後（跌破大盤，避開）。
配合 🛡️ 防禦板塊觀察 risk-on/off：防禦群整體移向領先 = 市場在避險。

### 注意
- 週線適合看月級別輪動（預設），日線適合短線但雜訊多。
- RRG 是**相對**強弱：大盤大跌時「領先」板塊也可能絕對下跌，只是跌得少。
- 本工具用 JdK 指標的公開重現（z-score 中心 100），數值與 StockCharts
  略有差異，但象限判定與輪動方向一致。
        """
    )
