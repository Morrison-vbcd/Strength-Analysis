# -*- coding: utf-8 -*-
"""深色交易終端視覺主題——整個 app 的視覺單一來源。

- COLORS / SERIES8 / PALETTE24 / HEAT_DIVERGING：色彩 tokens。
  SERIES8 採 dataviz 參考調色盤的深色八色序（已通過 CVD 相鄰對驗證，
  順序即安全機制，勿重排）；超過 8 條線 plotly 會循環，實務清單 ≤8 檔。
  PALETTE24 供 RRG 板塊圖（每點都有直接標籤，identity 不靠顏色單獨承載）。
- 熱力圖改用「紅↔中性深灰↔綠」發散色階（中點中性、不再用黃色中點），
  紅綠語意與標籤完全不變。
- inject()：注入自訂 CSS（卡片化 metric、側欄、字體細節）。
- apply(fig)：套 Plotly 深色版面（透明底、格線、字色、hover 樣式）。

.streamlit/config.toml 的主題值必須與 COLORS 同步。
"""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

COLORS = {
    "bg": "#0d1117",         # 頁面底
    "bg2": "#161b22",        # 側欄 / 卡片
    "bg3": "#1c2330",        # hover / 內凹
    "border": "#262d37",
    "text": "#e6edf3",
    "text_dim": "#8b949e",
    "accent": "#22c37e",     # 主色（多頭綠）
    "red": "#e5534b",
    "grid": "#21262e",
    "baseline": "#3d4550",
}

# dataviz 參考深色八色序（順序 = CVD 安全機制，勿重排）
SERIES8 = ["#3987e5", "#008300", "#d55181", "#c98500",
           "#199e70", "#d95926", "#9085e9", "#e66767"]

# RRG 板塊圖用的高對比亮色盤（Plotly Light24；identity 由直接標籤承載）
PALETTE24 = [
    "#FD3216", "#00FE35", "#6A76FC", "#FED4C4", "#FE00CE", "#0DF9FF",
    "#F6F926", "#FF9616", "#479B55", "#EEA6FB", "#DC587D", "#D626FF",
    "#6E899C", "#00B5F7", "#B68E00", "#C9FBE5", "#FF0092", "#22FFA7",
    "#E3EE9E", "#86CE00", "#BC7196", "#7E7DCD", "#FC6955", "#E48F72",
]

# 相對強弱熱力圖：紅（弱）↔ 中性深灰 ↔ 綠（強），中點貼近卡片底色
HEAT_DIVERGING = [[0.0, "#d84a52"], [0.5, "#232a32"], [1.0, "#1fa25f"]]
HEAT_TEXT = "#e6edf3"          # 熱力圖格內文字（三段色皆可讀）
DOWNLEG_FILL = "rgba(229,83,75,0.10)"   # RS 線圖 ▼段底色

# 單序列圖的角色色（配對頁等；標題已載明身分，不需圖例）
LINE_RATIO = "#22c37e"
LINE_Z = "#3987e5"
LINE_SPREAD = "#9085e9"
LINE_EQUITY = "#c98500"

_CSS = f"""
<style>
/* ---- 卡片化 metric ---- */
[data-testid="stMetric"] {{
    background: {COLORS["bg2"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 12px 16px;
}}
[data-testid="stMetricLabel"] {{ color: {COLORS["text_dim"]}; }}
/* ---- 側欄 ---- */
[data-testid="stSidebar"] {{
    border-right: 1px solid {COLORS["border"]};
}}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
    font-size: 0.95rem;
    letter-spacing: 0.06em;
    text-transform: none;
    color: {COLORS["text_dim"]};
}}
/* ---- 標題與表格數字 ---- */
h1 {{ letter-spacing: 0.02em; }}
[data-testid="stDataFrame"] {{ font-variant-numeric: tabular-nums; }}
/* ---- expander 邊框 ---- */
[data-testid="stExpander"] {{
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
}}
</style>
"""


def inject() -> None:
    """每頁開頭呼叫一次：注入自訂 CSS。"""
    st.markdown(_CSS, unsafe_allow_html=True)


def apply(fig: go.Figure) -> go.Figure:
    """套 Plotly 深色版面。不動已設定的軸範圍/高度/標題。"""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": COLORS["text"], "size": 12},
        colorway=SERIES8,
        hoverlabel={
            "bgcolor": COLORS["bg3"],
            "bordercolor": COLORS["border"],
            "font": {"color": COLORS["text"], "size": 12},
        },
        legend={"font": {"color": COLORS["text_dim"]}},
    )
    fig.update_xaxes(
        gridcolor=COLORS["grid"], zerolinecolor=COLORS["baseline"],
        linecolor=COLORS["baseline"], tickcolor=COLORS["baseline"],
    )
    fig.update_yaxes(
        gridcolor=COLORS["grid"], zerolinecolor=COLORS["baseline"],
        linecolor=COLORS["baseline"], tickcolor=COLORS["baseline"],
    )
    return fig
