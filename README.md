# 相對強弱分析工具（Wyckoff Comparative Relative Strength）

本機執行的 Streamlit 股票相對強弱分析工具，三個分頁：

| 分頁 | 功能 |
|---|---|
| 📊 個股相對強弱 | 核心標的 vs 同質參考股，ZigZag 結構段熱力圖、現況排名、RS 線、型態訊號（⭐強/⚠️弱、含已確認/進行中狀態）、訊號歷史應驗率統計、復盤模式（含逐週/逐月步進器） |
| 🔄 板塊輪動 | RRG 相對輪動圖（快照/軌跡/動畫回放）、risk-on/off 判定、象限轉換訊號表（未收盤期自動標示 ⏳）、板塊 vs 大盤結構熱力圖 |
| 🔗 配對交易 | 共整合檢定（Engle-Granger + ADF）、β 對沖比、spread z-score、半衰期、進出場提示、歷史回測（滾動 β、次日成交、含停損） |

支援台股（代碼自動補 .TW，上櫃自動退 .TWO）與美股。資料來源 Yahoo Finance（免費，延遲約 15 分鐘）。

**訊號怎麼讀、什麼時候能信**：見 [使用手冊.md](使用手冊.md)。

## 安裝與啟動（Windows）

1. 安裝 [Python 3.10+](https://www.python.org/downloads/)，安裝時**務必勾選「Add python.exe to PATH」**。
2. 雙擊 `run.bat`。首次執行會自動建立虛擬環境並安裝套件，
   **約需 2~5 分鐘（statsmodels 較大，請耐心等待）**；之後啟動只要幾秒。
3. 瀏覽器自動開啟 http://localhost:8501，左側切換三個分頁。

mac / linux：`bash run.sh`。

需求：Streamlit >= 1.36（使用 st.navigation 路由）。

## 核心概念（個股相對強弱頁）

- **RS（相對強弱）= 個股價格 / 基準價格**。一段區間內 RS 上升 = 贏過基準（強）。
- **時間週期不是固定天數**，而是用參考序列的 ZigZag 高低點切出的結構段（▲上漲段 / ▼下跌段）。
- **熱力圖顏色 = 相對強弱（vs 基準），不是絕對漲跌**。紅格可能只是漲得比族群少。
- 質化標籤與顏色語意對齊：綠 = `逆勢抗跌`/`抗跌`/`領漲`；紅 = `跟漲但落後`/`落後下跌`/`同步破底`。
- **🕰️ 復盤模式**：以指定過去日期當「當下」，之後資料一律截斷，回測當時的判讀。

## 檔案結構

```
app.py               # 路由進入點（st.navigation，唯一呼叫 set_page_config 的地方）
home.py              # 分頁：個股相對強弱
sector_rotation.py   # 分頁：板塊輪動（RRG）
pair_trading.py      # 分頁：配對交易
analysis.py          # 邏輯：ZigZag 結構、RS、熱力圖、型態偵測、analyze() 入口
rotation.py          # 邏輯：RRG 計算（JdK 公開重現）、象限訊號
pairtrade.py         # 邏輯：共整合/ADF、z-score、半衰期
benchmarks.py        # 預設觀察清單（同質性分級）與板塊基準
sectors.py           # RRG 板塊 ETF 宇宙（含防禦板塊 🛡️）
data.py              # yfinance 抓價 + .TW/.TWO 退補
param_sweep.py       # （工具）ZigZag 參數掃描
```

## FAQ

**Q：熱力圖紅色代表下跌嗎？**
不是。顏色是「相對」強弱：紅 = 輸給族群，可能只是漲得比較少。

**Q：RRG 數值和 StockCharts 不一樣？**
本工具用 JdK RS-Ratio/Momentum 的公開重現（rolling z-score 中心 100），
非 StockCharts 專有公式；數值略異但象限判定與輪動方向一致。

**Q：配對交易顯示 🔴 不建議配對？**
代表這兩檔的價差在統計上不會均值回歸（共整合不成立），
硬做等於在賭發散不收斂。換一對更同質的標的。

**Q：台股代碼要打後綴嗎？**
不用，純數字會自動補 .TW；上市抓不到會自動退 .TWO（上櫃，如 8299 群聯）。

**Q：首次啟動很慢？**
statsmodels + scipy 安裝需要幾分鐘，只有第一次會這樣。

## 已知限制

- yfinance 免費資料：延遲約 15 分鐘、偶有缺漏，重要決策以券商行情為準。
- 上市較晚的標的早期結構段為「資料不足」；個股頁可勾「對齊共同起算日」。
- 台股「記憶體」板塊基準用美元計價 US DRAM 代理，RS 夾帶匯率漂移。
