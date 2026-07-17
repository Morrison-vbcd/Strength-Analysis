# -*- coding: utf-8 -*-
"""美股同質性 peers 推薦。純邏輯，無 Streamlit。

資料來源：peers_us.json（Claude Research 2026-07 產出：46 板塊 / 340+ 檔，
含 A/B/C 同質性評級、綜合型剔除註記、配對候選）。
每季換版只更新 JSON，不動程式。

查詢流程（照研究建議）：
ticker → ticker_index 反查（主板塊 = 陣列第一個）→ 該板塊 tickers 排除自己 = 推薦 peers；
related_tickers 顯示為「綜合型已剔除」；rating C 需在 UI 警示「僅主題連動，不建議配對」。
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "peers_us.json")


@lru_cache(maxsize=1)
def _db() -> dict:
    with open(_PATH, encoding="utf-8") as f:
        return json.load(f)


def as_of() -> str:
    return _db()["meta"].get("as_of", "")


def rating_note(rating: str) -> str:
    return _db()["meta"]["rating_definitions"].get(rating, "")


def sector_name(key: str) -> str:
    sec = _db()["sectors"].get(key)
    return sec["name_zh"] if sec else key


def lookup_sectors(ticker: str) -> list[str]:
    """回傳該 ticker 所屬板塊 key 清單（主板塊在前）；查無回空清單。"""
    return list(_db()["ticker_index"].get(ticker.strip().upper(), []))


def recommend(ticker: str, sector_key: str | None = None) -> dict | None:
    """回傳推薦結果 dict；ticker 不在清單內回 None。

    keys: ticker / sector_key / sectors_all / name_zh / rating / rating_note /
    best_use / driver / peers（排除自己的 tickers dict 清單）/ related /
    pair_candidates / notes
    """
    t = ticker.strip().upper()
    keys = lookup_sectors(t)
    if not keys:
        return None
    key = sector_key if sector_key in keys else keys[0]
    sec = _db()["sectors"][key]
    return {
        "ticker": t,
        "sector_key": key,
        "sectors_all": keys,
        "name_zh": sec["name_zh"],
        "rating": sec["rating"],
        "rating_note": rating_note(sec["rating"]),
        "best_use": sec["best_use"],
        "driver": sec["driver"],
        "peers": [d for d in sec["tickers"] if d["ticker"] != t],
        "related": sec.get("related_tickers", []),
        "pair_candidates": sec.get("pair_candidates", []),
        "notes": sec.get("notes", ""),
    }


def integrity_check() -> list[str]:
    """資料完整性檢查（給測試用）：回傳問題清單，空 = 通過。"""
    db = _db()
    problems: list[str] = []
    for t, keys in db["ticker_index"].items():
        for k in keys:
            if k not in db["sectors"]:
                problems.append(f"ticker_index[{t}] 指向不存在的板塊 {k}")
    for k, sec in db["sectors"].items():
        for d in sec["tickers"]:
            idx = db["ticker_index"].get(d["ticker"])
            if not idx:
                problems.append(f"板塊 {k} 的 {d['ticker']} 不在 ticker_index")
        if sec["rating"] not in ("A", "B", "C"):
            problems.append(f"板塊 {k} rating 異常: {sec['rating']}")
    return problems
