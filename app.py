# -*- coding: utf-8 -*-
"""路由進入點：st.set_page_config 只在這裡呼叫一次，分頁檔不可再呼叫。

需求 Streamlit >= 1.36（st.navigation / st.Page）。
"""
import streamlit as st

st.set_page_config(page_title="相對強弱分析", page_icon="📊", layout="wide")

pg = st.navigation(
    [
        st.Page("home.py", title="個股相對強弱", icon="📊", default=True),
        st.Page("sector_rotation.py", title="板塊輪動", icon="🔄"),
        st.Page("pair_trading.py", title="配對交易", icon="🔗"),
    ]
)
pg.run()
