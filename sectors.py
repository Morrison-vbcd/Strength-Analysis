# -*- coding: utf-8 -*-
"""板塊輪動（RRG）的板塊 ETF 宇宙定義。

- 進攻板塊：景氣循環/成長曝險。
- 防禦板塊（defensive=True）：risk-off 時資金避風港，顯示加 🛡️ 前綴。
"""
from __future__ import annotations

# market → {"bench": 大盤基準, "sectors": {ticker: (顯示名, 是否防禦)}}
ROTATION_UNIVERSE: dict[str, dict] = {
    "美股": {
        "bench": "SPY",
        "sectors": {
            "XLK": ("科技", False),
            "XLC": ("通訊", False),
            "XLY": ("非必需消費", False),
            "XLF": ("金融", False),
            "XLI": ("工業", False),
            "XLB": ("原物料", False),
            "XLE": ("能源", False),
            "XLRE": ("房地產", False),
            "SMH": ("半導體", False),
            "XBI": ("生技", False),
            "XLV": ("醫療保健", True),
            "XLP": ("必需消費", True),
            "XLU": ("公用事業", True),
            "GLD": ("黃金", True),
            "TLT": ("長天期美債", True),
        },
    },
    "台股": {
        "bench": "0050.TW",
        "sectors": {
            "00891.TW": ("半導體", False),
            "0052.TW": ("電子", False),
            "00881.TW": ("5G通訊", False),
            "0055.TW": ("金融", False),
            "00893.TW": ("電動車", False),
            "0056.TW": ("高股息", True),
            "00713.TW": ("低波高息", True),
            "00679B.TW": ("美債20年", True),
        },
    },
}


def rotation_benchmark(market: str) -> str:
    return ROTATION_UNIVERSE[market]["bench"]


def rotation_sectors(market: str) -> dict[str, str]:
    """ticker → 顯示名（不含 🛡️）。"""
    return {t: name for t, (name, _) in ROTATION_UNIVERSE[market]["sectors"].items()}


def is_defensive(market: str, ticker: str) -> bool:
    info = ROTATION_UNIVERSE.get(market, {}).get("sectors", {}).get(ticker)
    return bool(info and info[1])


def display_name(market: str, ticker: str) -> str:
    """顯示名：防禦型加 🛡️ 前綴，例：🛡️公用事業 XLU。"""
    info = ROTATION_UNIVERSE.get(market, {}).get("sectors", {}).get(ticker)
    if not info:
        return ticker
    name, defensive = info
    prefix = "🛡️" if defensive else ""
    return f"{prefix}{name} {ticker}"
