# -*- coding: utf-8 -*-
"""資料抓取層：yfinance 批次下載 + 台股 .TW/.TWO 自動退補。

`fetch_prices(tickers, bench_ticker, market, start, end)`
→ (prices_df, resolved_dict, missing_list)

- prices_df：日線收盤價（auto_adjust），欄名 = 解析後代碼。
- resolved：輸入代碼 → 實際欄名；大盤/板塊基準的鍵固定為 "__SECTOR__"。
- missing：完全抓不到資料的輸入代碼。
"""
from __future__ import annotations

import pandas as pd
import yfinance as yf

SECTOR_KEY = "__SECTOR__"


def normalize(token: str, market: str) -> str:
    """台股純數字代碼補 .TW；一律大寫。"""
    t = token.strip().upper()
    if market == "台股" and t and t.replace("B", "").isdigit():
        # 00679B 之類的債券 ETF 也要補
        if not t.endswith((".TW", ".TWO")):
            t += ".TW"
    return t


def _download(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """批次抓收盤價；回傳欄名 = ticker 的 DataFrame（抓不到的欄整欄 NaN 或缺）。"""
    if not tickers:
        return pd.DataFrame()
    raw = yf.download(
        tickers,
        start=start,
        end=str((pd.Timestamp(end) + pd.Timedelta(days=1)).date()),
        auto_adjust=True,
        progress=False,
        group_by="column",
    )
    if raw is None or raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:  # 單一 ticker
        close = raw[["Close"]].rename(columns={"Close": tickers[0]})
    close = close.reindex(columns=tickers)
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close.dropna(how="all")


def fetch_prices(
    tickers: list[str],
    bench_ticker: str | None,
    market: str,
    start: str,
    end: str,
) -> tuple[pd.DataFrame, dict[str, str], list[str]]:
    """抓清單 + 基準。台股 .TW 抓不到自動退 .TWO（上櫃）再試一次。"""
    originals = [t for t in dict.fromkeys(x.strip() for x in tickers) if t]
    want = {orig: normalize(orig, market) for orig in originals}
    fetch_list = list(dict.fromkeys(want.values()))
    if bench_ticker:
        bench_norm = normalize(bench_ticker, market)
        if bench_norm not in fetch_list:
            fetch_list.append(bench_norm)
    else:
        bench_norm = None

    prices = _download(fetch_list, start, end)

    def has_data(col: str) -> bool:
        return col in prices.columns and not prices[col].dropna().empty

    # 台股上櫃退補：.TW 沒資料 → 換 .TWO 再抓一批
    if market == "台股":
        retry_map = {
            c: c[:-3] + ".TWO"
            for c in fetch_list
            if c.endswith(".TW") and not has_data(c)
        }
        if retry_map:
            p2 = _download(list(retry_map.values()), start, end)
            if not p2.empty:
                prices = pd.concat([prices.drop(columns=list(retry_map), errors="ignore"), p2], axis=1)
            for old, new in retry_map.items():
                for orig, norm in want.items():
                    if norm == old:
                        want[orig] = new
                if bench_norm == old:
                    bench_norm = new

    resolved: dict[str, str] = {}
    missing: list[str] = []
    for orig, norm in want.items():
        if has_data(norm):
            resolved[orig] = norm
        else:
            missing.append(orig)
    if bench_ticker:
        if has_data(bench_norm):
            resolved[SECTOR_KEY] = bench_norm
        else:
            missing.append(bench_ticker)

    keep = [c for c in prices.columns if not prices[c].dropna().empty]
    return prices[keep].dropna(how="all"), resolved, missing
