# -*- coding: utf-8 -*-
"""預設觀察清單（依同質性研究分級）與板塊基準對應。與 Mac 端保持同步。

每筆 watchlist：
- core：核心標的（分析主角）
- ref：參考股（同質群體，空白分隔）
- grade：同質性分級 A（高度同質，RS 比較最有意義）/ B（中度）/ C（主題式，異質性高）
- use：建議用法
- note：備註

台股代碼不帶交易所後綴，由 data 端解析時自動補 .TW（上櫃自動退 .TWO）。
"""
from __future__ import annotations

WATCHLISTS: dict[str, dict[str, dict]] = {
    "美股": {
        "（自訂 / 清空）": {"core": "", "ref": "", "grade": "", "use": "", "note": ""},
        "AI 運算 / GPU": {
            "core": "NVDA", "ref": "AMD AVGO", "grade": "A",
            "use": "AI 加速器三雄相對強弱", "note": "同吃 AI capex，權重股",
        },
        "記憶體 / 儲存": {
            "core": "MU", "ref": "SNDK WDC STX", "grade": "A",
            "use": "記憶體循環誰先動", "note": "DRAM/NAND/HDD 高度同週期",
        },
        "半導體設備": {
            "core": "AMAT", "ref": "LRCX KLAC ASML", "grade": "A",
            "use": "設備股景氣領先訊號", "note": "同吃晶圓廠 capex",
        },
        "AI 網通 / 交換器": {
            "core": "AVGO", "ref": "MRVL ANET", "grade": "B",
            "use": "AI 資料中心網路鏈", "note": "AVGO 業務較雜，含軟體",
        },
        "類比 / 車用晶片": {
            "core": "TXN", "ref": "ADI MCHP ON NXPI", "grade": "A",
            "use": "類比景氣循環比較", "note": "工業/車用曝險相近",
        },
        "晶圓代工 / IDM": {
            "core": "TSM", "ref": "INTC GFS", "grade": "B",
            "use": "代工版圖消長", "note": "INTC 轉型中，異質性升高",
        },
        "AI 電力 / 核能": {
            "core": "CEG", "ref": "VST NRG TLN", "grade": "B",
            "use": "AI 用電題材輪動", "note": "同題材但電廠組合不同",
        },
        "資安": {
            "core": "CRWD", "ref": "PANW ZS FTNT S", "grade": "A",
            "use": "資安板塊內強弱", "note": "皆訂閱制，估值敏感度同向",
        },
        "雲 / 數據軟體": {
            "core": "SNOW", "ref": "DDOG MDB NET", "grade": "A",
            "use": "高成長軟體風險偏好", "note": "利率敏感群",
        },
        "大型科技 (七雄)": {
            "core": "NVDA", "ref": "AAPL MSFT GOOGL AMZN META TSLA", "grade": "C",
            "use": "指數權重股領導力", "note": "業務異質，僅看資金流向",
        },
        "電商 / 平台": {
            "core": "AMZN", "ref": "SHOP MELI SE", "grade": "C",
            "use": "電商題材輪動", "note": "區域市場不同，主題式比較",
        },
        "支付 / 金融科技": {
            "core": "V", "ref": "MA AXP PYPL", "grade": "A",
            "use": "支付網路雙雄+延伸", "note": "V/MA 同質性極高",
        },
        "大型銀行 / 投行": {
            "core": "JPM", "ref": "BAC WFC C GS MS", "grade": "B",
            "use": "金融股內部輪動", "note": "商銀 vs 投行景氣點不同",
        },
        "能源 E&P": {
            "core": "EOG", "ref": "DVN FANG OXY", "grade": "A",
            "use": "頁岩油同業比較", "note": "同受油價驅動",
        },
    },
    "台股": {
        "（自訂 / 清空）": {"core": "", "ref": "", "grade": "", "use": "", "note": ""},
        "晶圓 / 晶片代工": {
            "core": "2330", "ref": "2303 6770", "grade": "B",
            "use": "代工龍頭 vs 二線", "note": "製程世代差距大",
        },
        "IC 設計": {
            "core": "2454", "ref": "3034 3443 4966 3661", "grade": "B",
            "use": "設計股資金輪動", "note": "終端應用不同",
        },
        "記憶體": {
            "core": "2344", "ref": "2408 8299 3260", "grade": "A",
            "use": "記憶體循環", "note": "同受 DRAM/NAND 報價驅動",
        },
        "AI 伺服器 / 代工": {
            "core": "2317", "ref": "2382 3231 2376 6669", "grade": "A",
            "use": "AI 伺服器鏈強弱", "note": "同吃 AI 伺服器訂單",
        },
        "散熱": {
            "core": "3017", "ref": "3324 6230", "grade": "A",
            "use": "散熱族群比較", "note": "氣冷→液冷轉換期",
        },
        "PCB / ABF 載板": {
            "core": "3037", "ref": "6213 8046 2368", "grade": "B",
            "use": "板類景氣輪動", "note": "載板與傳統板週期不同",
        },
        "光通訊 / CPO": {
            "core": "4977", "ref": "3163 6869", "grade": "B",
            "use": "CPO 題材輪動", "note": "題材催化為主",
        },
        "網通": {
            "core": "2345", "ref": "6285 3596", "grade": "B",
            "use": "網通族群比較", "note": "客戶結構不同",
        },
        "被動元件": {
            "core": "2327", "ref": "2492 2375", "grade": "A",
            "use": "被動元件循環", "note": "同受 MLCC 報價驅動",
        },
        "重電 / 電力": {
            "core": "1503", "ref": "1519 1513 1504", "grade": "A",
            "use": "重電基建輪動", "note": "同吃台電強韌電網",
        },
        "金控": {
            "core": "2881", "ref": "2882 2891 2884", "grade": "A",
            "use": "金控內部強弱", "note": "利率/壽險曝險略異",
        },
    },
}

# 板塊 → 基準 ETF 對應（已定案，勿改）
SECTOR_BENCHMARKS: dict[str, dict[str, str]] = {
    "美股": {
        "半導體": "SOXX",
        "科技": "XLK",
        "通訊": "XLC",
        "金融": "XLF",
        "能源": "XLE",
        "生技": "XBI",
        "記憶體": "DRAM",
        "混合": "QQQ",
    },
    "台股": {
        "大盤": "0050.TW",
        "半導體": "00891.TW",
        "電子": "0052.TW",
        "5G": "00881.TW",
        "金融": "0055.TW",
        "電動車": "00893.TW",
        # 台股無純 DRAM ETF，以美元計價的 US DRAM 當代理（RS 會夾帶匯率漂移）
        "記憶體": "DRAM",
    },
}


def watchlist_options(market: str) -> list[str]:
    return list(WATCHLISTS.get(market, {}).keys())


def watchlist_core(market: str, name: str) -> str:
    return WATCHLISTS.get(market, {}).get(name, {}).get("core", "")


def watchlist_ref(market: str, name: str) -> str:
    return WATCHLISTS.get(market, {}).get(name, {}).get("ref", "")


def watchlist_meta(market: str, name: str) -> dict | None:
    meta = WATCHLISTS.get(market, {}).get(name)
    if not meta or not meta.get("core"):
        return None
    return meta


def watchlist_tickers(market: str, name: str) -> str:
    """core + ref 合併字串（相容舊介面）。"""
    meta = WATCHLISTS.get(market, {}).get(name, {})
    return " ".join(x for x in [meta.get("core", ""), meta.get("ref", "")] if x).strip()


def sector_options(market: str) -> list[str]:
    return list(SECTOR_BENCHMARKS.get(market, {}).keys())


def benchmark_for_sector(market: str, sector: str) -> str:
    return SECTOR_BENCHMARKS.get(market, {}).get(sector, "")
