# -*- coding: utf-8 -*-
"""配對交易頁：共整合檢定 + spread z-score 均值回歸判讀。

注意：st.set_page_config 只在 app.py（路由）呼叫，此檔不可再呼叫。
"""
from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data
import pairtrade


@st.cache_data(ttl=900, show_spinner="下載價格資料中…")
def cached_fetch(tickers: tuple[str, ...], market: str, start: str, end: str):
    return data.fetch_prices(list(tickers), None, market, start, end)


def _apply_pair_preset():
    name = st.session_state.get("pair_pick", "")
    a, b, _ = pairtrade.PAIR_PRESETS.get(name, ("", "", ""))
    if a:
        st.session_state["pair_a"] = a
        st.session_state["pair_b"] = b


for key in ("pair_a", "pair_b"):
    if key not in st.session_state:
        st.session_state[key] = ""

# ---------------------------------------------------------------------------
# 側邊欄
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("配對交易設定")
    market = st.selectbox("市場", ["美股", "台股"], index=0, key="pair_market")
    st.selectbox(
        "配對候選（選了自動帶入，可自行修改）",
        list(pairtrade.PAIR_PRESETS.keys()),
        key="pair_pick",
        on_change=_apply_pair_preset,
    )
    note = pairtrade.PAIR_PRESETS.get(st.session_state.get("pair_pick", ""), ("", "", ""))[2]
    if note:
        st.caption(note)
    ticker_a = st.text_input("標的 A（分子腿）", key="pair_a", placeholder="例：V")
    ticker_b = st.text_input("標的 B（分母腿）", key="pair_b", placeholder="例：MA")
    lookback = st.slider("回看月數", 12, 60, 36)
    z_window = st.slider("z-score 視窗（交易日）", 20, 120, 60)
    entry = st.slider("進場門檻（±σ）", 1.0, 3.0, 2.0, 0.25)
    go_btn = st.button("🚀 開始分析", type="primary", width="stretch")

# ---------------------------------------------------------------------------
# 主畫面
# ---------------------------------------------------------------------------
st.title("🔗 配對交易")
st.caption(
    "挑兩檔高同質標的，檢定 log 價差是否共整合（均值回歸），"
    "z-score 摸到 ±σ 門檻做「多便宜、空昂貴」的配對。"
)

if go_btn:
    st.session_state["pair_run"] = True
if not st.session_state.get("pair_run"):
    st.info("左側選配對（V ↔ MA 最經典）後按「🚀 開始分析」。")
    st.stop()

a_raw = (st.session_state.get("pair_a") or "").strip().upper()
b_raw = (st.session_state.get("pair_b") or "").strip().upper()
if not a_raw or not b_raw or a_raw == b_raw:
    st.warning("請輸入兩檔不同的標的。")
    st.stop()

end = pd.Timestamp.today().normalize()
start = end - pd.DateOffset(months=lookback)
prices, resolved, missing = cached_fetch(
    (a_raw, b_raw), market, str(start.date()), str(end.date())
)
if missing:
    st.error(f"抓不到資料：{', '.join(missing)}")
    st.stop()
col_a, col_b = resolved[a_raw], resolved[b_raw]
sa, sb = prices[col_a].dropna(), prices[col_b].dropna()

try:
    res = pairtrade.compute_pair(sa, sb, z_window=z_window)
except ValueError as ex:
    st.error(f"資料不足：{ex}")
    st.stop()

# ---- 判讀 ----
tag, text = pairtrade.verdict(res)
st.subheader(tag)
st.markdown(text)
st.markdown(f"**{pairtrade.signal(res['cur_z'], entry)}**")

hl = res["half_life"]
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("β（對沖比）", f"{res['beta']:.3f}")
c2.metric("EG 共整合 p", f"{res['eg_p']:.3f}")
c3.metric("ADF p", f"{res['adf_p']:.3f}")
c4.metric("半衰期（天）", f"{hl:.0f}" if math.isfinite(hl) else "∞")
c5.metric("現況 z-score", f"{res['cur_z']:+.2f}")

# ---- 圖 1：RS 比值 ----
ratio = pairtrade.rebased_ratio(sa, sb)
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=ratio.index, y=ratio, name=f"{col_a}/{col_b}",
                          line={"color": "#2e7d32", "width": 1.8}))
fig1.add_hline(y=100, line_dash="dot", line_color="gray")
fig1.update_layout(
    title=f"{col_a} ÷ {col_b} 比值（起點 = 100，向上 = A 相對走強）",
    height=320, margin={"l": 40, "r": 20, "t": 50, "b": 30},
)
st.plotly_chart(fig1, width="stretch")

# ---- 圖 2：z-score 帶圖 ----
z = res["z"].dropna()
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=z.index, y=z, name="z-score", line={"color": "#1565c0", "width": 1.6}))
for lv, color in [(entry, "#c62828"), (-entry, "#2e7d32")]:
    fig2.add_hline(y=lv, line_dash="dash", line_color=color)
fig2.add_hline(y=0, line_color="gray", line_width=1)
fig2.update_layout(
    title=f"spread z-score（視窗 {z_window} 日；±{entry:.1f}σ = 進場門檻）",
    height=320, margin={"l": 40, "r": 20, "t": 50, "b": 30},
)
st.plotly_chart(fig2, width="stretch")

# ---- 圖 3：log-spread ----
sp = res["spread"]
fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=sp.index, y=sp, name="log-spread",
                          line={"color": "#6a1b9a", "width": 1.4}))
fig3.add_hline(y=float(sp.mean()), line_dash="dot", line_color="gray")
fig3.update_layout(
    title=f"log-spread = ln({col_a}) − β·ln({col_b}) − α",
    height=300, margin={"l": 40, "r": 20, "t": 50, "b": 30},
)
st.plotly_chart(fig3, width="stretch")

with st.expander("📖 使用說明"):
    st.markdown(
        f"""
### 這頁在做什麼？
配對交易 = 市場中性策略：不賭方向，只賭「兩檔高同質股票的價差會回到常態」。

### 統計檢定怎麼讀？
- **β（對沖比）**：做 1 單位 A 要對沖 β 單位 B（以 log 價迴歸估計）。
- **Engle-Granger 共整合 p < 0.05**：兩檔股票長期綁在一起，價差不會無限發散。
- **ADF p < 0.05**：spread 是定態序列（會回到均值）。
- **半衰期**：spread 偏離後回到一半所需天數。5–60 天最可操作——太短吃不到肉、
  太長資金效率差且基本面可能已改變。

### 進出場（現況門檻 ±{entry:.1f}σ）
- z ≥ +{entry:.1f}σ：A 相對太貴 → **空 A、多 B**（各按 β 對沖）。
- z ≤ −{entry:.1f}σ：A 相對太便宜 → **多 A、空 B**。
- z 回到 0 附近：平倉。z 繼續衝到 ±3σ 以上：認錯停損（結構可能已改變）。

### 風險提醒
- 共整合是「過去成立」，購併、拆分、商業模式轉變會讓關係永久斷裂——
  基本面事件（財報、購併傳聞）期間不要進場。
- 台股融券有規費與強制回補（除權息、股東會），實務摩擦成本比美股高。
        """
    )
