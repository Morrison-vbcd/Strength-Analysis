# -*- coding: utf-8 -*-
"""相對強弱核心邏輯（Wyckoff 比較式相對強弱）。純邏輯，無 Streamlit。

核心概念：
- RS（相對強弱）= 個股價格 / 基準價格。一段區間內 RS 上升 = 贏過基準（強）。
- 時間週期不是固定天數，而是用「參考序列」的 ZigZag 高低點切出的結構段（leg）。
- 熱力圖顏色 = 相對強弱（vs 基準），不是絕對漲跌。

對外統一入口：`analyze(prices, stock_cols, sector_col, pct, min_bars, basket_cols)`。
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

# 質化標籤（綠 = 相對強、紅 = 相對弱；顏色語意與標籤完全對齊）
GREEN_LABELS = {"逆勢抗跌", "抗跌", "領漲"}
RED_LABELS = {"跟漲但落後", "落後下跌", "同步破底"}


# ---------------------------------------------------------------------------
# 等權族群基準（鏈式等權指數：每日報酬 = 當日有資料個股的平均報酬）
# ---------------------------------------------------------------------------
def build_group_index(prices: pd.DataFrame, cols: list[str] | None = None) -> pd.Series:
    sub = prices[cols] if cols else prices
    rets = sub.pct_change(fill_method=None)
    mean_ret = rets.mean(axis=1)
    idx = (1.0 + mean_ret.fillna(0.0)).cumprod()
    idx.name = "GROUP"
    return idx


# ---------------------------------------------------------------------------
# ZigZag 結構切分
# ---------------------------------------------------------------------------
@dataclass
class Leg:
    start: pd.Timestamp
    end: pd.Timestamp
    direction: str  # "up" / "down"
    ongoing: bool = False  # 最後一段尚未被反轉確認

    @property
    def arrow(self) -> str:
        return "▲" if self.direction == "up" else "▼"

    def label(self) -> str:
        tag = f"{self.arrow} {self.start.strftime('%y/%m/%d')}→{self.end.strftime('%y/%m/%d')}"
        return tag + ("*" if self.ongoing else "")


def zigzag_pivots(series: pd.Series, threshold: float) -> list[tuple[int, str]]:
    """回傳 (位置索引, 'H'/'L') 轉折點清單，首尾以窗口起訖錨定。"""
    s = series.dropna()
    v = s.values
    n = len(v)
    if n < 2:
        return []
    pivots: list[tuple[int, str]] = []
    trend = 0  # 0=未定, 1=上, -1=下
    hi_i = lo_i = 0
    ext_i = 0
    for i in range(1, n):
        if trend == 0:
            if v[i] > v[hi_i]:
                hi_i = i
            if v[i] < v[lo_i]:
                lo_i = i
            if v[i] / v[lo_i] - 1.0 >= threshold:
                pivots.append((lo_i if lo_i > 0 else 0, "L"))
                if lo_i > 0:  # 錨定窗口起點
                    pivots.insert(0, (0, "H"))
                trend, ext_i = 1, i
            elif v[i] / v[hi_i] - 1.0 <= -threshold:
                pivots.append((hi_i if hi_i > 0 else 0, "H"))
                if hi_i > 0:
                    pivots.insert(0, (0, "L"))
                trend, ext_i = -1, i
        elif trend == 1:
            if v[i] >= v[ext_i]:
                ext_i = i
            elif v[i] / v[ext_i] - 1.0 <= -threshold:
                pivots.append((ext_i, "H"))
                trend, ext_i = -1, i
        else:
            if v[i] <= v[ext_i]:
                ext_i = i
            elif v[i] / v[ext_i] - 1.0 >= threshold:
                pivots.append((ext_i, "L"))
                trend, ext_i = 1, i
    # 收尾：最後一段以窗口終點錨定
    if trend == 0:
        pivots = [(0, "L" if v[-1] >= v[0] else "H")]
    pivots.append((n - 1, "H" if trend >= 0 else "L"))
    # 去除重複索引（threshold 觸發在第一根就轉折時可能重疊）
    dedup: list[tuple[int, str]] = []
    for p in pivots:
        if dedup and p[0] <= dedup[-1][0]:
            continue
        dedup.append(p)
    return dedup


def merge_short_legs(pivots: list[tuple[int, str]], min_bars: int) -> list[tuple[int, str]]:
    """把長度 < min_bars 的雜訊小段併入鄰段（維持 H/L 交替）。"""
    piv = list(pivots)
    while len(piv) > 2:
        lengths = [piv[k][0] - piv[k - 1][0] for k in range(1, len(piv))]
        short = [k for k in range(1, len(piv)) if lengths[k - 1] < min_bars]
        if not short:
            break
        # 先併掉最短的一段
        k = min(short, key=lambda kk: lengths[kk - 1])
        if k == 1:
            # 第一段太短：去掉第 1 個轉折，窗口起點錨改為相反型別
            piv = [(piv[0][0], piv[1][1])] + piv[2:]
        elif k == len(piv) - 1:
            # 最後一段太短：去掉倒數第 2 個轉折，終點錨改型
            piv = piv[:-2] + [(piv[-1][0], piv[-2][1])]
        else:
            # 內部段：成對移除兩端轉折，三段併成一段
            piv = piv[: k - 1] + piv[k + 1:]
    return piv


def build_legs(series: pd.Series, threshold: float, min_bars: int) -> list[Leg]:
    s = series.dropna()
    pivots = zigzag_pivots(s, threshold)
    if len(pivots) < 2:
        return []
    pivots = merge_short_legs(pivots, min_bars)
    legs: list[Leg] = []
    for k in range(1, len(pivots)):
        i0, _ = pivots[k - 1]
        i1, t1 = pivots[k]
        legs.append(
            Leg(
                start=s.index[i0],
                end=s.index[i1],
                direction="up" if t1 == "H" else "down",
                ongoing=(k == len(pivots) - 1),
            )
        )
    # 最後一段方向以實際漲跌修正（終點錨的型別是依趨勢猜的）
    if legs:
        last = legs[-1]
        seg = s.loc[last.start:last.end]
        if len(seg) >= 2:
            last.direction = "up" if seg.iloc[-1] >= seg.iloc[0] else "down"
    return legs


# ---------------------------------------------------------------------------
# 每段相對表現與質化標籤
# ---------------------------------------------------------------------------
def leg_return(series: pd.Series, leg: Leg) -> float:
    """個股在該 leg 的報酬；若該股在 leg 起點尚無資料 → NaN（資料不足）。"""
    s = series.dropna()
    if s.empty or s.index[0] > leg.start:
        return math.nan
    seg = s.loc[leg.start:leg.end]
    if len(seg) < 2:
        return math.nan
    return float(seg.iloc[-1] / seg.iloc[0] - 1.0)


def relative_return(stock_ret: float, base_ret: float) -> float:
    """RS 變化 = (1+個股報酬)/(1+基準報酬) - 1。>0 = 相對強。"""
    if math.isnan(stock_ret) or math.isnan(base_ret):
        return math.nan
    return (1.0 + stock_ret) / (1.0 + base_ret) - 1.0


def qualitative_label(direction: str, stock_ret: float, rel: float) -> str:
    """六種質化標籤，顏色語意與 rel 正負完全對齊（綠=rel>0，紅=rel<=0）。"""
    if math.isnan(rel):
        return "資料不足"
    if rel > 0:  # 相對強（綠）
        if direction == "up":
            return "領漲"
        return "逆勢抗跌" if stock_ret > 0 else "抗跌"
    # 相對弱（紅）
    if direction == "up":
        return "跟漲但落後" if stock_ret > 0 else "落後下跌"
    return "同步破底"


def build_heatmap(
    prices: pd.DataFrame, base: pd.Series, legs: list[Leg]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """回傳 (相對強弱% 矩陣, 質化標籤矩陣)；列=個股、欄=leg。"""
    rel_rows, lab_rows = {}, {}
    for t in prices.columns:
        rels, labs = [], []
        for leg in legs:
            sr = leg_return(prices[t], leg)
            br = leg_return(base, leg)
            rel = relative_return(sr, br)
            rels.append(rel)
            labs.append(qualitative_label(leg.direction, sr, rel))
        rel_rows[t] = rels
        lab_rows[t] = labs
    cols = [leg.label() for leg in legs]
    rel_df = pd.DataFrame.from_dict(rel_rows, orient="index", columns=cols)
    lab_df = pd.DataFrame.from_dict(lab_rows, orient="index", columns=cols)
    return rel_df, lab_df


# ---------------------------------------------------------------------------
# RS 序列（個股 / 基準，窗口起點=1.0；上市較晚者以自身首日=1.0）
# ---------------------------------------------------------------------------
def rs_series(prices: pd.DataFrame, base: pd.Series) -> pd.DataFrame:
    out = {}
    for t in prices.columns:
        s = prices[t].dropna()
        if s.empty:
            continue
        b = base.reindex(s.index).ffill()
        rs = (s / s.iloc[0]) / (b / b.iloc[0])
        out[t] = rs
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
# 資料涵蓋度
# ---------------------------------------------------------------------------
def stock_coverage(prices: pd.DataFrame, cols: list[str] | None = None) -> pd.DataFrame:
    """各標的資料起訖與筆數，供公平性檢查（上市較晚者跨窗口比較會偏差）。"""
    rows = []
    for t in cols or prices.columns:
        if t not in prices.columns:
            continue
        s = prices[t].dropna()
        rows.append(
            {
                "代碼": t,
                "資料起日": s.index[0].strftime("%Y-%m-%d") if not s.empty else "",
                "資料迄日": s.index[-1].strftime("%Y-%m-%d") if not s.empty else "",
                "筆數": int(len(s)),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 現況排名表
# ---------------------------------------------------------------------------
def ranking_table(
    prices: pd.DataFrame,
    base: pd.Series,
    legs: list[Leg],
    rel_df: pd.DataFrame,
    lab_df: pd.DataFrame,
) -> pd.DataFrame:
    if not legs:
        return pd.DataFrame()
    last_col = rel_df.columns[-1]
    recent_cols = rel_df.columns[-3:]
    rs = rs_series(prices, base)
    rows = []
    for t in prices.columns:
        s = prices[t].dropna()
        rs_t = rs[t].dropna() if t in rs.columns else pd.Series(dtype=float)
        rows.append(
            {
                "代碼": t,
                "最新段": legs[-1].label(),
                "最新段標籤": lab_df.loc[t, last_col],
                "最新段相對強弱%": round(rel_df.loc[t, last_col] * 100, 2)
                if not math.isnan(rel_df.loc[t, last_col])
                else math.nan,
                "近3段綠格數": int((rel_df.loc[t, recent_cols] > 0).sum()),
                "全窗口RS變化%": round((rs_t.iloc[-1] / rs_t.iloc[0] - 1.0) * 100, 2)
                if len(rs_t) >= 2
                else math.nan,
                "收盤價": round(float(s.iloc[-1]), 2) if not s.empty else math.nan,
                "資料起日": s.index[0].strftime("%Y-%m-%d") if not s.empty else "",
            }
        )
    df = pd.DataFrame(rows)
    df = df.sort_values("最新段相對強弱%", ascending=False, na_position="last").reset_index(drop=True)
    df.insert(0, "排名", range(1, len(df) + 1))
    return df


# ---------------------------------------------------------------------------
# 切結構參考序列的自動選擇
# ---------------------------------------------------------------------------
def pick_structure_series(
    group: pd.Series,
    benchmark: pd.Series | None,
    window_start: pd.Timestamp,
    coverage_tolerance_days: int = 10,
) -> tuple[pd.Series, str, str | None]:
    """板塊基準若涵蓋完整窗口才用它切結構，否則退回族群等權籃子。"""
    if benchmark is None or benchmark.dropna().empty:
        return group, "族群籃子", None
    bm = benchmark.dropna()
    if bm.index[0] <= window_start + pd.Timedelta(days=coverage_tolerance_days):
        return bm, "板塊基準", None
    warn = (
        f"板塊基準歷史不足（首筆資料 {bm.index[0].strftime('%Y-%m-%d')}，"
        f"晚於窗口起點 {window_start.strftime('%Y-%m-%d')}），"
        "切結構已退回「族群籃子」，避免結構被截短。"
    )
    return group, "族群籃子", warn


# ---------------------------------------------------------------------------
# Pattern（型態）識別：依已算出的 leg 質化標籤序列 + RS 線偵測，不重算價格。
# ---------------------------------------------------------------------------
PATTERN_CATALOG = [
    ("抗跌後領漲", "bull", "下跌段抗跌、隨後上漲段領漲——經典強勢輪動"),
    ("逆勢走強", "bull", "族群下跌時該股逆勢收紅"),
    ("連續領漲", "bull", "連兩個上漲段都領漲——持續領導"),
    ("谷底翻強", "bull", "先前弱勢破底/落後，首次翻為領漲——可能輪動起點"),
    ("RS創波段新高", "bull", "相對強弱線突破前波高點"),
    ("壓力段RS新高", "bull", "族群下跌段中 RS 創波段新高——壓力下驗證的強勢，優先級最高"),
    ("領漲熄火", "bear", "前一上漲段領漲、這段轉為落後——領導力衰退"),
    ("領漲背離", "bear", "標籤仍領漲、但 RS 段高點一波低於一波——力度未退、結構先衰（預警）"),
    ("連續落後", "bear", "連兩個上漲段都落後族群"),
    ("攻守俱弱", "bear", "跌段同步破底、漲段又落後——最弱組合"),
    ("RS創波段新低", "bear", "相對強弱線跌破前波低點"),
]
PATTERN_KIND = {name: kind for name, kind, _ in PATTERN_CATALOG}
PATTERN_NOTE = {name: note for name, _, note in PATTERN_CATALOG}
_STRONG_DOWN = {"抗跌", "逆勢抗跌"}
_WEAK_UP = {"跟漲但落後", "落後下跌"}


def pattern_names(kind: str | None = None) -> list[str]:
    return [n for n, k, _ in PATTERN_CATALOG if kind is None or k == kind]


def detect_patterns(
    qual_df: pd.DataFrame,
    legs: list[Leg],
    rs_lines: pd.DataFrame,
    stock_cols: list[str],
    selected: list[str] | None,
) -> tuple[pd.DataFrame, dict[tuple[str, str], set[str]]]:
    """回傳 (signals DataFrame[代號/型態/訊號/期間/日期/說明],
    marks dict[(代號, leg_label)] -> set{'bull','bear'})，供熱力圖加 ⭐/⚠️。"""
    sel = set(selected or [])
    cols = list(qual_df.columns)
    records: list[dict] = []
    marks: dict[tuple[str, str], set[str]] = {}

    def emit(t: str, name: str, leg_idx: int) -> None:
        if name not in sel:
            return
        kind = PATTERN_KIND[name]
        col = cols[leg_idx]
        records.append(
            {
                "代號": t,
                "型態": name,
                "訊號": "⭐ 強" if kind == "bull" else "⚠️ 弱",
                "狀態": "⏳進行中" if legs[leg_idx].ongoing else "✅已確認",
                "期間": col,
                "日期": legs[leg_idx].end.strftime("%Y-%m-%d"),
                "說明": PATTERN_NOTE[name],
            }
        )
        marks.setdefault((t, col), set()).add(kind)

    dirs = [l.direction for l in legs]
    up_idx = [i for i, d in enumerate(dirs) if d == "up"]
    down_idx = [i for i, d in enumerate(dirs) if d == "down"]

    for t in stock_cols:
        if t not in qual_df.index:
            continue
        tags = [qual_df.loc[t, c] for c in cols]

        # 抗跌後領漲：下跌段抗跌/逆勢抗跌，其後第一個上漲段領漲
        for i in down_idx:
            if tags[i] in _STRONG_DOWN:
                nxt = [j for j in up_idx if j > i]
                if nxt and tags[nxt[0]] == "領漲":
                    emit(t, "抗跌後領漲", nxt[0])
        # 逆勢走強：下跌段逆勢收紅
        for i in down_idx:
            if tags[i] == "逆勢抗跌":
                emit(t, "逆勢走強", i)
        # 相鄰兩個上漲段的組合
        for a, b in zip(up_idx, up_idx[1:]):
            if tags[a] == "領漲" and tags[b] == "領漲":
                emit(t, "連續領漲", b)
            if tags[a] == "領漲" and tags[b] in _WEAK_UP:
                emit(t, "領漲熄火", b)
            if tags[a] in _WEAK_UP and tags[b] in _WEAK_UP:
                emit(t, "連續落後", b)
        # 谷底翻強：曾弱勢（同步破底/落後下跌）後首次領漲，每檔只記一次
        weak_seen = False
        for i, tag in enumerate(tags):
            if tag in {"同步破底", "落後下跌"}:
                weak_seen = True
            elif weak_seen and tag == "領漲":
                emit(t, "谷底翻強", i)
                break
        # 攻守俱弱：上漲段落後，且其前一個下跌段同步破底
        for j in up_idx:
            prev_down = [i for i in down_idx if i < j]
            if prev_down and tags[j] in _WEAK_UP and tags[prev_down[-1]] == "同步破底":
                emit(t, "攻守俱弱", j)
        # RS 創波段新高/新低：走到 legs[i] 末日時，RS 突破之前所有段的極值
        if t in rs_lines.columns:
            rs = rs_lines[t].dropna()
            for i in range(1, len(legs)):
                cur = rs.loc[: legs[i].end]
                prev = rs.loc[: legs[i - 1].end]
                if cur.empty or prev.empty:
                    continue
                cur_v = float(cur.iloc[-1])
                if cur_v > float(prev.max()) * 1.001:
                    emit(t, "RS創波段新高", i)
                    # 壓力段RS新高：新高發生在族群下跌段、且該段標籤仍屬相對強
                    if dirs[i] == "down" and tags[i] in _STRONG_DOWN:
                        emit(t, "壓力段RS新高", i)
                if cur_v < float(prev.min()) * 0.999:
                    emit(t, "RS創波段新低", i)
            # 領漲背離：相鄰兩個上漲段都領漲，但本段 RS 高點低於前一上漲段高點
            for a, b in zip(up_idx, up_idx[1:]):
                if tags[a] != "領漲" or tags[b] != "領漲":
                    continue
                hi_a = rs.loc[legs[a].start: legs[a].end].max()
                hi_b = rs.loc[legs[b].start: legs[b].end].max()
                if pd.notna(hi_a) and pd.notna(hi_b) and float(hi_b) < float(hi_a) * 0.999:
                    emit(t, "領漲背離", b)

    sig_df = pd.DataFrame(records, columns=["代號", "型態", "訊號", "狀態", "期間", "日期", "說明"])
    if not sig_df.empty:
        sig_df = sig_df.sort_values(["日期", "代號"], ascending=[False, True]).reset_index(drop=True)
    return sig_df, marks


# ---------------------------------------------------------------------------
# 訊號統計：每種型態在「本族群、本窗口」的歷史應驗率
# ---------------------------------------------------------------------------
def pattern_forward_stats(
    qual_df: pd.DataFrame,
    legs: list[Leg],
    rs_lines: pd.DataFrame,
    stock_cols: list[str],
    rel_df: pd.DataFrame,
) -> pd.DataFrame:
    """對每個歷史訊號量「下一段」的相對表現，按型態彙總。

    - 只計「訊號所在段已確認、且下一段也已收」的樣本（不含進行中段，無前視）。
    - 應驗定義：bull 訊號 → 下一段相對族群 > 0；bear 訊號 → 下一段 < 0。
    回傳 DataFrame[型態/多空/樣本數/應驗率%/下一段相對報酬中位%/平均%]。
    """
    sig, _ = detect_patterns(qual_df, legs, rs_lines, stock_cols, pattern_names())
    if sig.empty or len(legs) < 2:
        return pd.DataFrame()
    col_to_idx = {leg.label(): i for i, leg in enumerate(legs)}
    cols = list(rel_df.columns)
    samples: dict[str, list[float]] = {}
    for _, r in sig.iterrows():
        i = col_to_idx.get(r["期間"])
        if i is None or i + 1 >= len(legs):
            continue
        if legs[i].ongoing or legs[i + 1].ongoing:
            continue  # 進行中段不計，避免前視
        fwd = rel_df.loc[r["代號"], cols[i + 1]]
        if isinstance(fwd, float) and math.isnan(fwd):
            continue
        samples.setdefault(r["型態"], []).append(float(fwd))
    rows = []
    for name in pattern_names():
        vals = samples.get(name)
        if not vals:
            continue
        kind = PATTERN_KIND[name]
        hits = sum(1 for v in vals if (v > 0 if kind == "bull" else v < 0))
        s = pd.Series(vals)
        rows.append(
            {
                "型態": name,
                "多空": "⭐ 強" if kind == "bull" else "⚠️ 弱",
                "樣本數": len(vals),
                "應驗率%": round(100.0 * hits / len(vals), 1),
                "下一段相對報酬中位%": round(float(s.median()) * 100, 2),
                "平均%": round(float(s.mean()) * 100, 2),
            }
        )
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["多空", "應驗率%"], ascending=[True, False]).reset_index(drop=True)
    return out


# ---------------------------------------------------------------------------
# 統一入口
# ---------------------------------------------------------------------------
def analyze(
    prices: pd.DataFrame,
    stock_cols: list[str],
    sector_col: str | None,
    pct: float = 0.05,
    min_bars: int = 8,
    basket_cols: list[str] | None = None,
) -> dict:
    """一次算完：族群基準、結構切分、雙熱力圖、RS 線、排名、涵蓋度。

    - stock_cols：要比較的個股欄名。
    - sector_col：板塊/大盤基準欄名（None = 只做族群內比較）。
    - basket_cols：等權籃子的成分（預設 = stock_cols）。

    回傳 keys：group / struct_name / struct_warn / legs /
    score_vs_group / qual / score_vs_sector / qual_vs_sector /
    rs_lines / ranking / coverage。legs 為空時其餘鍵為 None。
    """
    stock_cols = [c for c in stock_cols if c in prices.columns]
    group = build_group_index(prices, basket_cols or stock_cols)
    bench = prices[sector_col] if sector_col and sector_col in prices.columns else None
    window_start = prices.index[0]
    struct, struct_name, warn = pick_structure_series(group, bench, window_start)
    legs = build_legs(struct, pct, min_bars)
    out: dict = {
        "group": group,
        "struct_name": struct_name,
        "struct_warn": warn,
        "legs": legs,
        "score_vs_group": None,
        "qual": None,
        "score_vs_sector": None,
        "qual_vs_sector": None,
        "rs_lines": None,
        "ranking": None,
        "coverage": stock_coverage(prices, stock_cols),
    }
    if not legs:
        return out
    stock_px = prices[stock_cols]
    rel_g, lab_g = build_heatmap(stock_px, group, legs)
    out["score_vs_group"], out["qual"] = rel_g, lab_g
    if bench is not None:
        rel_s, lab_s = build_heatmap(stock_px, bench, legs)
        out["score_vs_sector"], out["qual_vs_sector"] = rel_s, lab_s
    out["rs_lines"] = rs_series(stock_px, group)
    out["ranking"] = ranking_table(stock_px, group, legs, rel_g, lab_g)
    return out
