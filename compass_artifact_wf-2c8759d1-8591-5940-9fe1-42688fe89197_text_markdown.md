# 美股標的 → 熱點板塊 → 同質性參考清單（2026 年 7 月）

## TL;DR
- 本資料建立涵蓋 46 個主題板塊、340+ 檔美股標的的結構化 JSON 對照表與 ticker 反查索引，供桌面交易程式產出「同質性參考清單」用於 RS 比較與配對交易；2026 年 7 月市場正處於「去 AI 集中化、往實體經濟/小型股輪動」的環境（Russell 2000 上半年上漲 22%，為 1991 年以來最佳上半年，CNBC 2026/6/30）。
- 每個板塊皆以「同質子群」為單位（如資安分 endpoint/SASE/identity；半導體分 GPU/ASIC/記憶體/設備/EDA/晶圓代工/類比/光通訊/連接晶片），綜合型股票（AVGO、MRVL、TXN、BKR 等）指派到單一主板塊並在相關板塊以 related_tickers 註記剔除，避免異質混籃。
- 板塊評級：純同質可直接配對者為 A（如大型銀行、支付網路、E&P、EDA）；適合動能輪動、配對需嚴選者為 B（多數）；純主題連動、成分基本面異質者為 C 不建議配對（量子、加密財庫、太空、eVTOL、稀土開發商）。**所有相關係數/協整結果一律需使用者自行跑數據；市值層級為 2026 年 7 月概估，須以即時資料確認。**

## Key Findings

**2026 年 7 月市場實況（影響 RS 基準，務必納入）**
- **輪動方向**：據 Morningstar（2026）與 CNBC（2026/7/6），industrial、consumer defensive、energy 領漲，資金流出 technology/communication services；Russell 2000 上半年 +22%（1991 年來最佳），S&P 500 +9.6%、Nasdaq +12.8%。
- **半導體估值重置**：費半指數狂漲約 130% 後於 2026 年 7 月重挫，全球晶片股單週蒸發逾 1 兆美元；7/7 單日 Micron 跌 13%、Intel 七個交易日跌 21%、AMD 跌 7%（Intellectia.AI 2026/7/7；Forbes 2026/7/8）。Morgan Stanley 稱為「mid-cycle reset rather than a top」。這代表半導體各子群近期 beta 極高、RS 排名波動大。
- **量子/加密/太空高波動**：量子四雄（IONQ/RGTI/QBTS/QUBT）2026/6/22 川普量子行政命令後大漲、7 月 risk-off 時 IONQ 單日 -8%、其餘 -6%（247wallst 2026/7/13）；加密財庫股因 BTC/ETH 回檔多數深度套牢（BitMine 半年 -60%）。

**必須注意的成分變動 / 短交易歷史（影響 RS 基準）**
- **Synopsys 收購 Ansys**（2025/7/17 完成，ANSS 下市；光學軟體剝離給 Keysight）。
- **Wolfspeed (WOLF)** 2025/6/30 聲請 Chapter 11、2025/9/29 重整後上市，舊股註銷、交易歷史重置——RS 基準只能從 2025/9 起算。
- **Palo Alto (PANW) 收購 CyberArk**（2026/2 完成）+ Chronosphere（$33.5 億）。
- **Rocket Lab (RKLB)** 宣布 $80 億收購 Iridium（2026/6）；**Constellation (CEG)** 2026/1 完成 $220 億收購 Calpine。
- 近期 IPO/短歷史：**ALAB**（2024/3）、**CRDO**（2022/1）、**GFS**（2021/10）、**CRCL**（2025 IPO）、**CRWV / NBIS**（neocloud，短歷史高波動）。

---

## Details

### (A) 完整 JSON 資料結構

```json
{
  "meta": {
    "as_of": "2026-07",
    "description": "美股標的→熱點板塊→同質性 peers 對照表，供 RS 比較與 Pair Trading 使用。市值為概估須以即時資料確認；相關係數/協整一律需自行跑數據。",
    "rating_definitions": {
      "A": "純同質，可直接配對（基本面驅動高度一致）",
      "B": "適合動能輪動/RS 排名；配對需嚴選子群並自行驗證協整",
      "C": "僅主題連動，成分基本面異質或投機，不建議配對"
    },
    "cap_tier_definitions": {
      "mega": ">2000億美元", "large": "100–2000億", "mid": "20–100億", "small": "<20億"
    },
    "usage_note": "查詢 ticker→先查 ticker_index 取主板塊(陣列第一個)→列出該板塊 tickers 排除自己為推薦 peers；related_tickers 顯示為『參考但已剔除(綜合型)』；rating=C 在 UI 警示『不建議配對，僅供主題監控』。"
  },
  "sectors": {
    "ai_gpu": {"name_zh":"AI 運算/GPU","rating":"B","best_use":"momentum","driver":"AI 資料中心資本支出/GPU 出貨",
      "tickers":[
        {"ticker":"NVDA","company":"NVIDIA","cap_tier":"mega","purity":"pure","notes":"AI GPU 龍頭"},
        {"ticker":"AMD","company":"Advanced Micro Devices","cap_tier":"large","purity":"diversified","notes":"MI350/355 系列；兼 CPU"}],
      "related_tickers":[{"ticker":"AVGO","reason":"綜合型，主籃為 ai_asic_networking"},{"ticker":"TSM","reason":"綜合型，主籃為 foundry"}],
      "pair_candidates":[["NVDA","AMD"]],
      "notes":"僅兩檔純同質；GPU 加速器高度同向但 NVDA 市值遠大於 AMD，配對需 beta 調整。需自行跑數據。"},

    "ai_asic_networking": {"name_zh":"AI 客製晶片/網通交換","rating":"B","best_use":"momentum","driver":"超大規模業者自研 ASIC 與 AI 網通需求",
      "tickers":[
        {"ticker":"AVGO","company":"Broadcom","cap_tier":"mega","purity":"diversified","notes":"客製 ASIC(Google/Meta)+VMware 軟體；主籃"},
        {"ticker":"MRVL","company":"Marvell Technology","cap_tier":"large","purity":"diversified","notes":"客製矽+光學 DSP+網通"},
        {"ticker":"ANET","company":"Arista Networks","cap_tier":"mega","purity":"pure","notes":"AI 以太網交換，非光學"}],
      "related_tickers":[{"ticker":"ALAB","reason":"連接晶片，主籃 ai_connectivity_silicon"}],
      "pair_candidates":[["AVGO","MRVL"]],
      "notes":"AVGO/MRVL 皆客製矽同質；ANET 為交換系統，配對需謹慎。需自行跑數據。"},

    "memory_storage": {"name_zh":"記憶體/儲存","rating":"A","best_use":"both","driver":"DRAM/NAND/HBM 報價循環",
      "tickers":[
        {"ticker":"MU","company":"Micron Technology","cap_tier":"large","purity":"pure","notes":"美股唯一純記憶體大廠(DRAM/NAND/HBM)"},
        {"ticker":"WDC","company":"Western Digital","cap_tier":"large","purity":"pure","notes":"HDD/NAND"},
        {"ticker":"STX","company":"Seagate Technology","cap_tier":"large","purity":"pure","notes":"HDD 為主"},
        {"ticker":"SNDK","company":"Sandisk","cap_tier":"mid","purity":"pure","notes":"NAND；2025 由 WDC 分拆，短交易歷史"}],
      "pair_candidates":[["WDC","STX"],["MU","WDC"]],
      "notes":"報價驅動高度同質；WDC/STX 為最可能協整的 HDD 配對。SNDK 分拆後歷史短。需自行跑數據。"},

    "semi_equipment": {"name_zh":"半導體設備(WFE)","rating":"A","best_use":"both","driver":"晶圓廠資本支出(WFE)",
      "tickers":[
        {"ticker":"AMAT","company":"Applied Materials","cap_tier":"large","purity":"pure","notes":"沉積/蝕刻"},
        {"ticker":"LRCX","company":"Lam Research","cap_tier":"large","purity":"pure","notes":"蝕刻/沉積"},
        {"ticker":"KLAC","company":"KLA Corp","cap_tier":"large","purity":"pure","notes":"製程控制/量測"},
        {"ticker":"ASML","company":"ASML Holding","cap_tier":"mega","purity":"pure","notes":"微影龍頭；ADR"},
        {"ticker":"ENTG","company":"Entegris","cap_tier":"mid","purity":"pure","notes":"材料/耗材"},
        {"ticker":"CAMT","company":"Camtek","cap_tier":"mid","purity":"pure","notes":"先進封裝檢測；ADR"}],
      "pair_candidates":[["AMAT","LRCX"],["LRCX","KLAC"]],
      "notes":"WFE 週期驅動一致；AMAT/LRCX 為經典協整候選。需自行跑數據。"},

    "eda": {"name_zh":"EDA 設計軟體/IP","rating":"A","best_use":"pairs","driver":"晶片設計活動/研發支出",
      "tickers":[
        {"ticker":"SNPS","company":"Synopsys","cap_tier":"large","purity":"pure","notes":"2025/7 完成 $350 億收購 Ansys(ANSS 下市)，光學軟體剝離給 Keysight—財報基準變動"},
        {"ticker":"CDNS","company":"Cadence Design Systems","cap_tier":"large","purity":"pure","notes":"最大純 EDA"}],
      "related_tickers":[{"ticker":"KEYS","reason":"綜合型測試量測，主籃另計"}],
      "pair_candidates":[["SNPS","CDNS"]],
      "notes":"雙寡頭高度同質，經典配對；惟 SNPS 併 Ansys 後營收結構改變，需重設協整窗口。需自行跑數據。"},

    "foundry": {"name_zh":"晶圓代工/IDM","rating":"B","best_use":"momentum","driver":"先進/成熟製程產能利用率",
      "tickers":[
        {"ticker":"TSM","company":"Taiwan Semiconductor","cap_tier":"mega","purity":"pure","notes":"先進製程龍頭；ADR"},
        {"ticker":"INTC","company":"Intel","cap_tier":"large","purity":"diversified","notes":"IDM 轉型代工；18A 良率延後"},
        {"ticker":"GFS","company":"GlobalFoundries","cap_tier":"large","purity":"pure","notes":"成熟/特殊製程；2025 併 AMF(SiPho)+Infinilink；IPO 2021/10"},
        {"ticker":"UMC","company":"United Microelectronics","cap_tier":"large","purity":"pure","notes":"成熟製程；ADR"},
        {"ticker":"TSEM","company":"Tower Semiconductor","cap_tier":"large","purity":"pure","notes":"類比/RF/SiPho 特殊製程；ADR"}],
      "pair_candidates":[["GFS","UMC"]],
      "notes":"TSM 領先幅度過大，先進 vs 成熟製程異質；GFS/UMC(成熟製程)較同質。需自行跑數據。"},

    "analog_auto": {"name_zh":"類比/車用/功率半導體","rating":"B","best_use":"both","driver":"工業/車用終端需求循環",
      "tickers":[
        {"ticker":"TXN","company":"Texas Instruments","cap_tier":"mega","purity":"diversified","notes":"類比+嵌入式龍頭"},
        {"ticker":"ADI","company":"Analog Devices","cap_tier":"large","purity":"diversified","notes":"類比/混訊"},
        {"ticker":"NXPI","company":"NXP Semiconductors","cap_tier":"large","purity":"diversified","notes":"車用/工業/邊緣"},
        {"ticker":"MCHP","company":"Microchip Technology","cap_tier":"large","purity":"diversified","notes":"MCU/類比"},
        {"ticker":"ON","company":"ON Semiconductor","cap_tier":"large","purity":"diversified","notes":"功率/感測(車用)"},
        {"ticker":"STM","company":"STMicroelectronics","cap_tier":"large","purity":"diversified","notes":"類比/功率/MCU；ADR"},
        {"ticker":"WOLF","company":"Wolfspeed","cap_tier":"small","purity":"pure","notes":"純 SiC 功率；2025/9/29 重整後上市，舊股註銷、交易歷史重置"}],
      "pair_candidates":[["TXN","ADI"],["NXPI","ON"]],
      "notes":"TXN/ADI(廣義類比)最同質；WOLF 因重整交易歷史短、極端波動，勿與大廠配對。需自行跑數據。"},

    "optical_cpo": {"name_zh":"光通訊/CPO 元件","rating":"B","best_use":"momentum","driver":"資料中心光模組/CPO 需求",
      "tickers":[
        {"ticker":"COHR","company":"Coherent","cap_tier":"large","purity":"diversified","notes":"光學/雷射/材料+光模組；2022 由 II-VI 併購沿用歷史"},
        {"ticker":"LITE","company":"Lumentum Holdings","cap_tier":"large","purity":"pure","notes":"純光子(收發器/雷射)"},
        {"ticker":"FN","company":"Fabrinet","cap_tier":"large","purity":"pure","notes":"光學代工(泰國)"},
        {"ticker":"CIEN","company":"Ciena","cap_tier":"large","purity":"pure","notes":"光網路系統(非元件)"},
        {"ticker":"AAOI","company":"Applied Optoelectronics","cap_tier":"mid","purity":"pure","notes":"光模組小型高波動"}],
      "pair_candidates":[["LITE","COHR"]],
      "notes":"LITE/COHR 光元件同質；CIEN 為系統商、應視為子群邊界。需自行跑數據。"},

    "ai_connectivity_silicon": {"name_zh":"AI 連接晶片(retimer/SerDes)","rating":"B","best_use":"momentum","driver":"AI 機櫃內互連(PCIe/CXL/AEC)需求",
      "tickers":[
        {"ticker":"ALAB","company":"Astera Labs","cap_tier":"large","purity":"pure","notes":"PCIe/CXL retimer；IPO 2024/3 短歷史"},
        {"ticker":"CRDO","company":"Credo Technology","cap_tier":"large","purity":"pure","notes":"AEC/SerDes；IPO 2022/1"}],
      "related_tickers":[{"ticker":"MRVL","reason":"綜合型，主籃 ai_asic_networking"}],
      "pair_candidates":[["ALAB","CRDO"]],
      "notes":"純連接晶片高度同向但皆短交易歷史、極高 beta，配對前需長窗口。需自行跑數據。"},

    "ai_power_ipp": {"name_zh":"AI 電力/IPP","rating":"A","best_use":"both","driver":"AI 資料中心用電需求/電價",
      "tickers":[
        {"ticker":"CEG","company":"Constellation Energy","cap_tier":"large","purity":"pure","notes":"最大核電機隊；2026/1 完成併 Calpine—營收基準大變"},
        {"ticker":"VST","company":"Vistra","cap_tier":"large","purity":"pure","notes":"核+氣+儲能 IPP"},
        {"ticker":"TLN","company":"Talen Energy","cap_tier":"large","purity":"pure","notes":"IPP，供電 AWS"},
        {"ticker":"NRG","company":"NRG Energy","cap_tier":"large","purity":"pure","notes":"零售+發電"}],
      "pair_candidates":[["VST","CEG"],["VST","TLN"]],
      "notes":"IPP 對電價/AI 用電高度同向；CEG 併 Calpine 後需重設基準。需自行跑數據。"},

    "nuclear_smr": {"name_zh":"核能/SMR 開發商","rating":"C","best_use":"momentum","driver":"SMR 商轉里程碑/政策題材",
      "tickers":[
        {"ticker":"OKLO","company":"Oklo","cap_tier":"large","purity":"pure","notes":"SMR，前營收，Sam Altman 背景"},
        {"ticker":"SMR","company":"NuScale Power","cap_tier":"mid","purity":"pure","notes":"SMR，營收微小"},
        {"ticker":"NNE","company":"Nano Nuclear Energy","cap_tier":"small","purity":"pure","notes":"微型反應爐，前營收"},
        {"ticker":"BWXT","company":"BWX Technologies","cap_tier":"large","purity":"diversified","notes":"核工程/燃料(有實質營收)"}],
      "pair_candidates":[["OKLO","SMR"]],
      "notes":"前營收開發商由里程碑/題材驅動、基本面異質，僅主題連動，不建議均值回歸配對。需自行跑數據。"},

    "data_center_reit": {"name_zh":"資料中心 REIT","rating":"A","best_use":"both","driver":"超大規模業者 AI 資本支出/機櫃租賃",
      "tickers":[
        {"ticker":"EQIX","company":"Equinix","cap_tier":"large","purity":"pure","notes":"互連/colocation 龍頭"},
        {"ticker":"DLR","company":"Digital Realty","cap_tier":"large","purity":"pure","notes":"批發/hyperscale"},
        {"ticker":"IRM","company":"Iron Mountain","cap_tier":"large","purity":"diversified","notes":"儲存轉型資料中心，高 beta"}],
      "pair_candidates":[["EQIX","DLR"]],
      "notes":"EQIX/DLR 為經典同質配對；IRM 業務混雜、beta 較高。需自行跑數據。"},

    "neocloud": {"name_zh":"GPU 雲/Neocloud","rating":"C","best_use":"momentum","driver":"GPU 租賃需求/GPU 折舊",
      "tickers":[
        {"ticker":"CRWV","company":"CoreWeave","cap_tier":"large","purity":"pure","notes":"GPU 雲；2025 IPO 短歷史"},
        {"ticker":"NBIS","company":"Nebius Group","cap_tier":"large","purity":"pure","notes":"GPU 雲"},
        {"ticker":"IREN","company":"IREN","cap_tier":"mid","purity":"diversified","notes":"礦工轉 AI 算力"},
        {"ticker":"APLD","company":"Applied Digital","cap_tier":"mid","purity":"diversified","notes":"資料中心/HPC 租賃"}],
      "pair_candidates":[["CRWV","NBIS"]],
      "notes":"短歷史、GPU 折舊/財務槓桿差異大，主題連動為主，不建議配對。需自行跑數據。"},

    "ai_server_odm": {"name_zh":"AI 伺服器/ODM","rating":"B","best_use":"both","driver":"GPU 機櫃出貨/hyperscaler 訂單",
      "tickers":[
        {"ticker":"SMCI","company":"Super Micro Computer","cap_tier":"mid","purity":"pure","notes":"液冷機櫃；治理/財報疑慮致高波動"},
        {"ticker":"DELL","company":"Dell Technologies","cap_tier":"large","purity":"diversified","notes":"AI 伺服器 backlog 大+PC"},
        {"ticker":"HPE","company":"Hewlett Packard Enterprise","cap_tier":"large","purity":"diversified","notes":"GreenLake+Cray"}],
      "pair_candidates":[["DELL","HPE"]],
      "notes":"DELL/HPE 較同質；SMCI 純度高但治理風險使 RS 失真，配對需謹慎。需自行跑數據。"},

    "power_cooling": {"name_zh":"資料中心電源/散熱","rating":"B","best_use":"both","driver":"高密度運算電力/液冷需求",
      "tickers":[
        {"ticker":"VRT","company":"Vertiv Holdings","cap_tier":"large","purity":"pure","notes":"電源/熱管理純 play"},
        {"ticker":"ETN","company":"Eaton","cap_tier":"large","purity":"diversified","notes":"電力管理(多元工業)"},
        {"ticker":"MOD","company":"Modine Manufacturing","cap_tier":"mid","purity":"diversified","notes":"熱管理"},
        {"ticker":"NVT","company":"nVent Electric","cap_tier":"mid","purity":"diversified","notes":"電氣連接/機櫃"}],
      "pair_candidates":[["VRT","ETN"]],
      "notes":"VRT 最純；ETN/MOD 為綜合工業，driver 部分重疊。需自行跑數據。"},

    "cybersecurity_endpoint": {"name_zh":"資安-端點/XDR","rating":"A","best_use":"pairs","driver":"端點防護/XDR 支出",
      "tickers":[
        {"ticker":"CRWD","company":"CrowdStrike","cap_tier":"large","purity":"pure","notes":"端點龍頭"},
        {"ticker":"S","company":"SentinelOne","cap_tier":"mid","purity":"pure","notes":"端點挑戰者"}],
      "pair_candidates":[["CRWD","S"]],
      "notes":"同子群純同質；市值差距大需 beta 調整。需自行跑數據。"},

    "cybersecurity_sase": {"name_zh":"資安-網路/SASE/防火牆","rating":"B","best_use":"both","driver":"零信任/SASE/防火牆支出",
      "tickers":[
        {"ticker":"PANW","company":"Palo Alto Networks","cap_tier":"large","purity":"pure","notes":"平台化；2026/2 併 CyberArk+Chronosphere"},
        {"ticker":"ZS","company":"Zscaler","cap_tier":"large","purity":"pure","notes":"SASE 純 play"},
        {"ticker":"FTNT","company":"Fortinet","cap_tier":"large","purity":"pure","notes":"防火牆+ASIC 硬體"},
        {"ticker":"NET","company":"Cloudflare","cap_tier":"large","purity":"pure","notes":"邊緣/雲安全"},
        {"ticker":"CHKP","company":"Check Point","cap_tier":"large","purity":"pure","notes":"防火牆"}],
      "pair_candidates":[["PANW","FTNT"],["ZS","NET"]],
      "notes":"PANW 併 CyberArk 後含 identity，基準改變；ZS/NET 較純雲安全。需自行跑數據。"},

    "cybersecurity_identity": {"name_zh":"資安-身分/IAM","rating":"B","best_use":"pairs","driver":"身分存取管理需求",
      "tickers":[
        {"ticker":"OKTA","company":"Okta","cap_tier":"large","purity":"pure","notes":"IAM 純 play"},
        {"ticker":"SAIL","company":"SailPoint","cap_tier":"mid","purity":"pure","notes":"身分治理；重新上市短歷史"}],
      "related_tickers":[{"ticker":"PANW","reason":"併 CyberArk 後含 identity，主籃 cybersecurity_sase"}],
      "pair_candidates":[["OKTA","SAIL"]],
      "notes":"CyberArk 已被 PANW 併購下市。需自行跑數據。"},

    "observability_data": {"name_zh":"雲數據/可觀測性","rating":"B","best_use":"both","driver":"企業 AI 工作負載/用量計費",
      "tickers":[
        {"ticker":"DDOG","company":"Datadog","cap_tier":"large","purity":"pure","notes":"可觀測性龍頭"},
        {"ticker":"SNOW","company":"Snowflake","cap_tier":"large","purity":"pure","notes":"資料雲"},
        {"ticker":"MDB","company":"MongoDB","cap_tier":"large","purity":"pure","notes":"NoSQL 資料庫"},
        {"ticker":"ESTC","company":"Elastic","cap_tier":"mid","purity":"pure","notes":"搜尋/SIEM/可觀測"},
        {"ticker":"GTLB","company":"GitLab","cap_tier":"mid","purity":"pure","notes":"DevSecOps"}],
      "pair_candidates":[["DDOG","MDB"]],
      "notes":"皆用量計費 SaaS，同向但終端不同(資料庫 vs 監控)，配對需嚴選。需自行跑數據。"},

    "ai_app_software": {"name_zh":"AI 應用/企業軟體","rating":"B","best_use":"momentum","driver":"企業 AI 軟體採用/IT 支出",
      "tickers":[
        {"ticker":"PLTR","company":"Palantir Technologies","cap_tier":"mega","purity":"pure","notes":"AIP；估值極高"},
        {"ticker":"NOW","company":"ServiceNow","cap_tier":"large","purity":"pure","notes":"工作流平台"},
        {"ticker":"CRM","company":"Salesforce","cap_tier":"large","purity":"pure","notes":"CRM+Agentforce"},
        {"ticker":"PATH","company":"UiPath","cap_tier":"mid","purity":"pure","notes":"RPA→agentic"},
        {"ticker":"AI","company":"C3.ai","cap_tier":"small","purity":"pure","notes":"企業 AI 應用"}],
      "pair_candidates":[["NOW","CRM"]],
      "notes":"估值/成長率差異極大，PLTR 為離群值。需自行跑數據。"},

    "quantum": {"name_zh":"量子運算","rating":"C","best_use":"momentum","driver":"量子里程碑/政策題材",
      "tickers":[
        {"ticker":"IONQ","company":"IonQ","cap_tier":"large","purity":"pure","notes":"離子阱；現金最多"},
        {"ticker":"RGTI","company":"Rigetti Computing","cap_tier":"mid","purity":"pure","notes":"超導；$1億 CHIPS 補助"},
        {"ticker":"QBTS","company":"D-Wave Quantum","cap_tier":"mid","purity":"pure","notes":"量子退火(最商業化)"},
        {"ticker":"QUBT","company":"Quantum Computing Inc","cap_tier":"mid","purity":"pure","notes":"光子/最投機"}],
      "pair_candidates":[["IONQ","RGTI"]],
      "notes":"前獲利、題材驅動、架構不同(離子阱/超導/退火/光子)—高度同向但基本面異質，僅主題監控。需自行跑數據。"},

    "crypto_miners": {"name_zh":"加密礦工","rating":"B","best_use":"both","driver":"BTC 價格/算力/電費",
      "tickers":[
        {"ticker":"MARA","company":"MARA Holdings","cap_tier":"mid","purity":"pure","notes":"BTC 挖礦+持幣"},
        {"ticker":"RIOT","company":"Riot Platforms","cap_tier":"mid","purity":"pure","notes":"BTC 挖礦"},
        {"ticker":"CLSK","company":"CleanSpark","cap_tier":"mid","purity":"pure","notes":"BTC 挖礦"},
        {"ticker":"CORZ","company":"Core Scientific","cap_tier":"mid","purity":"diversified","notes":"挖礦+HPC 租賃"},
        {"ticker":"WULF","company":"TeraWulf","cap_tier":"mid","purity":"diversified","notes":"挖礦+AI 算力"}],
      "pair_candidates":[["MARA","RIOT"]],
      "notes":"MARA/RIOT/CLSK 純礦工最同質；CORZ/WULF 因 AI 轉型 driver 分歧。需自行跑數據。"},

    "crypto_exchange": {"name_zh":"加密交易所/券商","rating":"B","best_use":"momentum","driver":"加密交易量/幣價",
      "tickers":[
        {"ticker":"COIN","company":"Coinbase Global","cap_tier":"large","purity":"pure","notes":"最大合規交易所"},
        {"ticker":"HOOD","company":"Robinhood Markets","cap_tier":"large","purity":"diversified","notes":"券商+加密"},
        {"ticker":"BLSH","company":"Bullish","cap_tier":"mid","purity":"pure","notes":"機構交易所；2025 IPO"},
        {"ticker":"GEMI","company":"Gemini","cap_tier":"mid","purity":"pure","notes":"交易所；近期上市"}],
      "pair_candidates":[["COIN","HOOD"]],
      "notes":"HOOD 券商業務占比高，與純交易所 driver 部分不同。需自行跑數據。"},

    "crypto_treasury_btc": {"name_zh":"加密財庫-BTC","rating":"C","best_use":"momentum","driver":"BTC 價格/mNAV 溢價",
      "tickers":[
        {"ticker":"MSTR","company":"Strategy (MicroStrategy)","cap_tier":"large","purity":"pure","notes":"最大 BTC 財庫"},
        {"ticker":"XXI","company":"Twenty One Capital","cap_tier":"mid","purity":"pure","notes":"BTC 財庫"}],
      "pair_candidates":[["MSTR","XXI"]],
      "notes":"BTC 價格+籌資結構/mNAV 溢價驅動，槓桿與成本基礎差異大，僅主題連動。需自行跑數據。"},

    "crypto_treasury_eth": {"name_zh":"加密財庫-ETH","rating":"C","best_use":"momentum","driver":"ETH 價格/mNAV 溢價",
      "tickers":[
        {"ticker":"BMNR","company":"BitMine Immersion","cap_tier":"mid","purity":"pure","notes":"最大 ETH 財庫；半年 -60%"},
        {"ticker":"SBET","company":"SharpLink Gaming","cap_tier":"small","purity":"pure","notes":"ETH 財庫"}],
      "pair_candidates":[["BMNR","SBET"]],
      "notes":"ETH 價格驅動、深度套牢，僅主題監控。需自行跑數據。"},

    "stablecoin_fintech": {"name_zh":"穩定幣/金融科技","rating":"B","best_use":"momentum","driver":"穩定幣採用/GENIUS Act/支付量",
      "tickers":[
        {"ticker":"CRCL","company":"Circle Internet Group","cap_tier":"large","purity":"pure","notes":"USDC 發行商；2025 IPO 高波動"},
        {"ticker":"SOFI","company":"SoFi Technologies","cap_tier":"large","purity":"diversified","notes":"數位銀行+SoFiUSD 穩定幣"},
        {"ticker":"UPST","company":"Upstart Holdings","cap_tier":"mid","purity":"pure","notes":"AI 放貸"}],
      "pair_candidates":[["SOFI","UPST"]],
      "notes":"CRCL 純穩定幣，SOFI 為銀行—driver 不同；配對需分辨。需自行跑數據。"},

    "robotics_humanoid": {"name_zh":"機器人-人形/服務","rating":"C","best_use":"momentum","driver":"人形量產里程碑/題材",
      "tickers":[
        {"ticker":"SERV","company":"Serve Robotics","cap_tier":"small","purity":"pure","notes":"人行道配送(微型)"},
        {"ticker":"RR","company":"Richtech Robotics","cap_tier":"small","purity":"pure","notes":"服務/人形(早期)"}],
      "related_tickers":[{"ticker":"TSLA","reason":"綜合型，主籃 china_ev 對應之美國 EV/robotics，實際主籃見 tesla 特例"},{"ticker":"NVDA","reason":"機器人平台，主籃 ai_gpu"}],
      "pair_candidates":[["SERV","RR"]],
      "notes":"微型投機、前營收，僅主題監控。TSLA/NVDA 為大型綜合型不併入。需自行跑數據。"},

    "robotics_industrial": {"name_zh":"機器人-工業/自動化","rating":"B","best_use":"both","driver":"製造業資本支出/自動化滲透",
      "tickers":[
        {"ticker":"ISRG","company":"Intuitive Surgical","cap_tier":"large","purity":"pure","notes":"手術機器人"},
        {"ticker":"ROK","company":"Rockwell Automation","cap_tier":"large","purity":"pure","notes":"工業自動化"},
        {"ticker":"SYM","company":"Symbotic","cap_tier":"mid","purity":"pure","notes":"倉儲自動化"},
        {"ticker":"TER","company":"Teradyne","cap_tier":"large","purity":"diversified","notes":"半導體測試+協作機器人"}],
      "pair_candidates":[["ROK","TER"]],
      "notes":"終端市場差異大(手術/工廠/倉儲)，配對需同終端。需自行跑數據。"},

    "space_launch": {"name_zh":"太空-發射/系統","rating":"C","best_use":"momentum","driver":"發射/國防合約/SpaceX IPO 題材",
      "tickers":[
        {"ticker":"RKLB","company":"Rocket Lab","cap_tier":"large","purity":"pure","notes":"發射+衛星；宣布併 Iridium"},
        {"ticker":"LUNR","company":"Intuitive Machines","cap_tier":"mid","purity":"pure","notes":"月球物流；股東權益為負"},
        {"ticker":"FLY","company":"Firefly Aerospace","cap_tier":"mid","purity":"pure","notes":"發射/月球；近期上市"},
        {"ticker":"VOYG","company":"Voyager Technologies","cap_tier":"mid","purity":"diversified","notes":"太空平台;近期上市"}],
      "pair_candidates":[["RKLB","LUNR"]],
      "notes":"里程碑/合約驅動、多前營收，僅主題連動。需自行跑數據。"},

    "space_satcom": {"name_zh":"太空-衛星通訊/觀測","rating":"C","best_use":"momentum","driver":"衛星部署/連網合約",
      "tickers":[
        {"ticker":"ASTS","company":"AST SpaceMobile","cap_tier":"large","purity":"pure","notes":"直連手機衛星;發射延遲風險"},
        {"ticker":"PL","company":"Planet Labs","cap_tier":"mid","purity":"pure","notes":"地球影像"},
        {"ticker":"IRDM","company":"Iridium Communications","cap_tier":"mid","purity":"pure","notes":"衛星通訊;RKLB 併購中"},
        {"ticker":"SATS","company":"EchoStar","cap_tier":"mid","purity":"diversified","notes":"衛星/頻譜"}],
      "pair_candidates":[["ASTS","PL"]],
      "notes":"商業模式異質(直連/影像/語音)，僅主題監控。需自行跑數據。"},

    "drones_defense": {"name_zh":"無人機/國防科技","rating":"B","best_use":"both","driver":"國防預算/無人系統採購",
      "tickers":[
        {"ticker":"AVAV","company":"AeroVironment","cap_tier":"large","purity":"pure","notes":"遊蕩彈藥/小型無人機"},
        {"ticker":"KTOS","company":"Kratos Defense","cap_tier":"large","purity":"pure","notes":"噴射無人機/CCA"},
        {"ticker":"RCAT","company":"Red Cat Holdings","cap_tier":"small","purity":"pure","notes":"陸軍 SRR 合約;NDAA 合規"},
        {"ticker":"ONDS","company":"Ondas Holdings","cap_tier":"small","purity":"pure","notes":"無人機/邊境"},
        {"ticker":"UMAC","company":"Unusual Machines","cap_tier":"small","purity":"pure","notes":"NDAA 合規零件"}],
      "pair_candidates":[["AVAV","KTOS"]],
      "notes":"合約時點造成 lumpy 波動;大型(AVAV/KTOS)與小型(RCAT/ONDS)分層。需自行跑數據。"},

    "defense_primes": {"name_zh":"國防主承包商","rating":"A","best_use":"both","driver":"國防預算/backlog/Golden Dome",
      "tickers":[
        {"ticker":"LMT","company":"Lockheed Martin","cap_tier":"large","purity":"pure","notes":"F-35/THAAD/PAC-3"},
        {"ticker":"RTX","company":"RTX Corp","cap_tier":"large","purity":"diversified","notes":"飛彈+商用引擎"},
        {"ticker":"NOC","company":"Northrop Grumman","cap_tier":"large","purity":"pure","notes":"B-21/Sentinel"},
        {"ticker":"GD","company":"General Dynamics","cap_tier":"large","purity":"diversified","notes":"造船+Gulfstream"},
        {"ticker":"LHX","company":"L3Harris","cap_tier":"large","purity":"pure","notes":"國防電子"}],
      "pair_candidates":[["LMT","NOC"]],
      "notes":"LMT/NOC 純國防最同質;RTX/GD 有商用業務。需自行跑數據。"},

    "evtol": {"name_zh":"eVTOL 電動飛行","rating":"C","best_use":"momentum","driver":"FAA 認證里程碑",
      "tickers":[
        {"ticker":"JOBY","company":"Joby Aviation","cap_tier":"large","purity":"pure","notes":"垂直整合;Uber/Toyota"},
        {"ticker":"ACHR","company":"Archer Aviation","cap_tier":"mid","purity":"pure","notes":"Midnight"},
        {"ticker":"EVTL","company":"Vertical Aerospace","cap_tier":"small","purity":"pure","notes":"英國;2026 -70%"},
        {"ticker":"EH","company":"EHang Holdings","cap_tier":"mid","purity":"pure","notes":"中國自主載具;ADR"}],
      "pair_candidates":[["JOBY","ACHR"]],
      "notes":"二元認證風險、前營收，僅主題監控;JOBY/ACHR 相對同質但估值差異大。需自行跑數據。"},

    "rare_earth": {"name_zh":"稀土/關鍵礦物","rating":"C","best_use":"momentum","driver":"對中脫鉤政策/磁鐵需求",
      "tickers":[
        {"ticker":"MP","company":"MP Materials","cap_tier":"large","purity":"pure","notes":"唯一運營稀土礦(Mountain Pass);國防價格地板 $110/kg NdPr"},
        {"ticker":"USAR","company":"USA Rare Earth","cap_tier":"mid","purity":"pure","notes":"礦到磁鐵一體化;開發中"},
        {"ticker":"UUUU","company":"Energy Fuels","cap_tier":"mid","purity":"diversified","notes":"鈾+稀土加工"},
        {"ticker":"CRML","company":"Critical Metals","cap_tier":"small","purity":"pure","notes":"格陵蘭 Tanbreez;高波動"}],
      "pair_candidates":[["MP","USAR"]],
      "notes":"MP 有實質營收;其餘多為開發商前營收，政策題材驅動、基本面異質。需自行跑數據。"},

    "uranium": {"name_zh":"鈾礦/核燃料","rating":"B","best_use":"both","driver":"鈾現貨價/核電需求",
      "tickers":[
        {"ticker":"CCJ","company":"Cameco","cap_tier":"large","purity":"pure","notes":"最大西方鈾生產商"},
        {"ticker":"UEC","company":"Uranium Energy","cap_tier":"mid","purity":"pure","notes":"美國 ISR"},
        {"ticker":"DNN","company":"Denison Mines","cap_tier":"mid","purity":"pure","notes":"加拿大 Athabasca"},
        {"ticker":"UUUU","company":"Energy Fuels","cap_tier":"mid","purity":"diversified","notes":"鈾+稀土"},
        {"ticker":"LEU","company":"Centrus Energy","cap_tier":"mid","purity":"pure","notes":"濃縮"}],
      "pair_candidates":[["CCJ","UEC"]],
      "notes":"鈾價驅動同向;UUUU 因稀土 driver 分歧。需自行跑數據。"},

    "glp1": {"name_zh":"GLP-1 減肥藥","rating":"B","best_use":"both","driver":"肥胖藥銷售/臨床試驗",
      "tickers":[
        {"ticker":"LLY","company":"Eli Lilly","cap_tier":"mega","purity":"diversified","notes":"Mounjaro/Zepbound 領先"},
        {"ticker":"NVO","company":"Novo Nordisk","cap_tier":"large","purity":"diversified","notes":"Wegovy;ADR;較 52 週高 -45%"},
        {"ticker":"VKTX","company":"Viking Therapeutics","cap_tier":"mid","purity":"pure","notes":"VK2735 臨床期;前營收二元風險"}],
      "pair_candidates":[["LLY","NVO"]],
      "notes":"LLY/NVO 為商業化雙雄較同質;VKTX 為前營收臨床股，勿與大廠配對。需自行跑數據。"},

    "big_pharma": {"name_zh":"大型製藥","rating":"B","best_use":"both","driver":"藥品銷售/專利懸崖/管線",
      "tickers":[
        {"ticker":"MRK","company":"Merck","cap_tier":"large","purity":"pure","notes":"Keytruda"},
        {"ticker":"PFE","company":"Pfizer","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"ABBV","company":"AbbVie","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"BMY","company":"Bristol Myers Squibb","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"JNJ","company":"Johnson & Johnson","cap_tier":"mega","purity":"diversified","notes":"藥+醫材"}],
      "pair_candidates":[["MRK","BMY"]],
      "notes":"個別專利懸崖/管線差異大，配對需檢視營收集中度。需自行跑數據。"},

    "biotech": {"name_zh":"大型生技","rating":"B","best_use":"both","driver":"新藥核准/臨床數據",
      "tickers":[
        {"ticker":"AMGN","company":"Amgen","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"GILD","company":"Gilead Sciences","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"VRTX","company":"Vertex Pharmaceuticals","cap_tier":"large","purity":"pure","notes":"囊腫纖維化"},
        {"ticker":"REGN","company":"Regeneron","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"BIIB","company":"Biogen","cap_tier":"mid","purity":"pure","notes":""}],
      "pair_candidates":[["AMGN","GILD"]],
      "notes":"管線特異性高，臨床事件造成個股跳空。需自行跑數據。"},

    "china_ecommerce": {"name_zh":"中概-電商/科技","rating":"B","best_use":"both","driver":"中國消費/監管/ADR 退市風險",
      "tickers":[
        {"ticker":"BABA","company":"Alibaba","cap_tier":"large","purity":"diversified","notes":"電商+雲+AI;VIE 結構"},
        {"ticker":"PDD","company":"PDD Holdings","cap_tier":"large","purity":"pure","notes":"拼多多/Temu;VIE"},
        {"ticker":"JD","company":"JD.com","cap_tier":"large","purity":"pure","notes":"電商;VIE"},
        {"ticker":"BIDU","company":"Baidu","cap_tier":"large","purity":"diversified","notes":"搜尋+AI;VIE"}],
      "pair_candidates":[["BABA","JD"]],
      "notes":"皆 ADR/VIE 結構，共同退市與地緣風險溢價;BABA 業務較 JD/PDD 多元。需自行跑數據。"},

    "china_ev": {"name_zh":"中概-電動車","rating":"B","best_use":"both","driver":"中國 EV 交付量/補貼",
      "tickers":[
        {"ticker":"NIO","company":"NIO","cap_tier":"mid","purity":"pure","notes":"換電;ADR"},
        {"ticker":"XPEV","company":"XPeng","cap_tier":"mid","purity":"pure","notes":"ADR"},
        {"ticker":"LI","company":"Li Auto","cap_tier":"large","purity":"pure","notes":"增程;ADR"}],
      "pair_candidates":[["NIO","XPEV"]],
      "notes":"交付量驅動同向;NIO/XPEV 較同規模。需自行跑數據。"},

    "big_banks": {"name_zh":"大型銀行/投行","rating":"A","best_use":"both","driver":"利率/淨利差/投行活動",
      "tickers":[
        {"ticker":"JPM","company":"JPMorgan Chase","cap_tier":"mega","purity":"diversified","notes":"最大全能銀行"},
        {"ticker":"BAC","company":"Bank of America","cap_tier":"large","purity":"diversified","notes":""},
        {"ticker":"WFC","company":"Wells Fargo","cap_tier":"large","purity":"diversified","notes":"資產上限已解除"},
        {"ticker":"C","company":"Citigroup","cap_tier":"large","purity":"diversified","notes":""},
        {"ticker":"GS","company":"Goldman Sachs","cap_tier":"large","purity":"pure","notes":"投行為主"},
        {"ticker":"MS","company":"Morgan Stanley","cap_tier":"large","purity":"diversified","notes":"投行+財管"}],
      "pair_candidates":[["JPM","BAC"],["GS","MS"]],
      "notes":"貨幣中心銀行高度同質(JPM/BAC/WFC/C);投行雙雄(GS/MS)另成子群。需自行跑數據。"},

    "regional_banks": {"name_zh":"區域銀行","rating":"A","best_use":"both","driver":"利率/淨利差/CRE 曝險",
      "tickers":[
        {"ticker":"USB","company":"U.S. Bancorp","cap_tier":"large","purity":"diversified","notes":""},
        {"ticker":"PNC","company":"PNC Financial","cap_tier":"large","purity":"diversified","notes":"併 FirstBank"},
        {"ticker":"TFC","company":"Truist Financial","cap_tier":"large","purity":"diversified","notes":""},
        {"ticker":"FITB","company":"Fifth Third Bancorp","cap_tier":"mid","purity":"diversified","notes":""},
        {"ticker":"MTB","company":"M&T Bank","cap_tier":"mid","purity":"diversified","notes":""},
        {"ticker":"RF","company":"Regions Financial","cap_tier":"mid","purity":"diversified","notes":""},
        {"ticker":"HBAN","company":"Huntington Bancshares","cap_tier":"mid","purity":"diversified","notes":""}],
      "pair_candidates":[["FITB","RF"],["USB","PNC"]],
      "notes":"區域銀行對利率/CRE 高度同向，KRE 成分經典配對。需自行跑數據。"},

    "payment_networks": {"name_zh":"支付網路/處理","rating":"A","best_use":"both","driver":"消費刷卡量/跨境支付",
      "tickers":[
        {"ticker":"V","company":"Visa","cap_tier":"mega","purity":"pure","notes":"卡網路"},
        {"ticker":"MA","company":"Mastercard","cap_tier":"mega","purity":"pure","notes":"卡網路"},
        {"ticker":"AXP","company":"American Express","cap_tier":"large","purity":"diversified","notes":"卡網路+放貸"},
        {"ticker":"PYPL","company":"PayPal","cap_tier":"large","purity":"pure","notes":"數位支付"},
        {"ticker":"FI","company":"Fiserv","cap_tier":"large","purity":"pure","notes":"商戶處理"},
        {"ticker":"FOUR","company":"Shift4 Payments","cap_tier":"mid","purity":"pure","notes":"商戶收單"}],
      "pair_candidates":[["V","MA"]],
      "notes":"V/MA 為全市場最同質配對之一;AXP 含放貸 driver 不同。需自行跑數據。"},

    "brokers": {"name_zh":"券商/交易所","rating":"B","best_use":"both","driver":"交易量/資產管理規模",
      "tickers":[
        {"ticker":"SCHW","company":"Charles Schwab","cap_tier":"large","purity":"pure","notes":"折扣券商"},
        {"ticker":"IBKR","company":"Interactive Brokers","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"HOOD","company":"Robinhood Markets","cap_tier":"large","purity":"diversified","notes":"零售+加密;亦見 crypto_exchange"},
        {"ticker":"CME","company":"CME Group","cap_tier":"large","purity":"pure","notes":"期貨交易所"},
        {"ticker":"ICE","company":"Intercontinental Exchange","cap_tier":"large","purity":"diversified","notes":"交易所+數據"}],
      "pair_candidates":[["SCHW","IBKR"]],
      "notes":"券商(SCHW/IBKR/HOOD)與交易所(CME/ICE)為不同子群。需自行跑數據。"},

    "energy_ep": {"name_zh":"能源-E&P/上游","rating":"A","best_use":"both","driver":"油價(WTI)/產量",
      "tickers":[
        {"ticker":"COP","company":"ConocoPhillips","cap_tier":"large","purity":"pure","notes":"最大獨立 E&P;最流動"},
        {"ticker":"EOG","company":"EOG Resources","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"FANG","company":"Diamondback Energy","cap_tier":"large","purity":"pure","notes":"Permian 純;併 Endeavor"},
        {"ticker":"OXY","company":"Occidental Petroleum","cap_tier":"large","purity":"diversified","notes":"Berkshire 持股;化工"},
        {"ticker":"DVN","company":"Devon Energy","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"CTRA","company":"Coterra Energy","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"PR","company":"Permian Resources","cap_tier":"large","purity":"pure","notes":"Permian 純"},
        {"ticker":"APA","company":"APA Corp","cap_tier":"large","purity":"pure","notes":"併 Callon"},
        {"ticker":"AR","company":"Antero Resources","cap_tier":"large","purity":"pure","notes":"氣為主(Appalachia)"}],
      "pair_candidates":[["FANG","PR"],["EOG","DVN"]],
      "notes":"油價驅動高度同質;Permian 純 play(FANG/PR)最可能協整;氣weighted(AR)另分。需自行跑數據。"},

    "oilfield_services": {"name_zh":"能源-油服","rating":"A","best_use":"both","driver":"上游資本支出/鑽井活動",
      "tickers":[
        {"ticker":"SLB","company":"SLB (Schlumberger)","cap_tier":"large","purity":"pure","notes":"最大油服;最流動"},
        {"ticker":"HAL","company":"Halliburton","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"BKR","company":"Baker Hughes","cap_tier":"large","purity":"diversified","notes":"油服+LNG 渦輪機"},
        {"ticker":"WFRD","company":"Weatherford International","cap_tier":"mid","purity":"pure","notes":"最小/流動性較低"}],
      "pair_candidates":[["SLB","HAL"]],
      "notes":"SLB/HAL 為經典油服配對;BKR 含工業/LNG driver 分歧。需自行跑數據。"},

    "midstream": {"name_zh":"能源-中游/管線","rating":"A","best_use":"both","driver":"油氣輸送量/費率",
      "tickers":[
        {"ticker":"ENB","company":"Enbridge","cap_tier":"large","purity":"pure","notes":"最大;C-corp(加拿大)"},
        {"ticker":"WMB","company":"Williams Companies","cap_tier":"large","purity":"pure","notes":"C-corp"},
        {"ticker":"EPD","company":"Enterprise Products Partners","cap_tier":"large","purity":"pure","notes":"MLP(K-1);最流動 MLP"},
        {"ticker":"KMI","company":"Kinder Morgan","cap_tier":"large","purity":"pure","notes":"C-corp"},
        {"ticker":"ET","company":"Energy Transfer","cap_tier":"large","purity":"pure","notes":"MLP(K-1)"},
        {"ticker":"OKE","company":"ONEOK","cap_tier":"large","purity":"pure","notes":"C-corp"},
        {"ticker":"MPLX","company":"MPLX LP","cap_tier":"large","purity":"pure","notes":"MLP(K-1);Marathon 關聯"}],
      "pair_candidates":[["WMB","KMI"],["EPD","MPLX"]],
      "notes":"費率型收益穩定同向;注意 C-corp(WMB/KMI/OKE) 與 MLP(EPD/ET/MPLX 發 K-1) 稅務結構差異，配對建議同結構。需自行跑數據。"},

    "airlines": {"name_zh":"航空","rating":"A","best_use":"both","driver":"客運需求/油價/座位收益",
      "tickers":[
        {"ticker":"DAL","company":"Delta Air Lines","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"UAL","company":"United Airlines","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"AAL","company":"American Airlines","cap_tier":"mid","purity":"pure","notes":""},
        {"ticker":"LUV","company":"Southwest Airlines","cap_tier":"mid","purity":"pure","notes":"廉航"}],
      "pair_candidates":[["DAL","UAL"]],
      "notes":"DAL/UAL(全服務)最同質;LUV 商模不同。需自行跑數據。"},

    "cruise_travel": {"name_zh":"郵輪/旅遊","rating":"A","best_use":"both","driver":"休閒旅遊需求/預訂量",
      "tickers":[
        {"ticker":"CCL","company":"Carnival","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"RCL","company":"Royal Caribbean","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"NCLH","company":"Norwegian Cruise Line","cap_tier":"mid","purity":"pure","notes":""}],
      "pair_candidates":[["CCL","RCL"]],
      "notes":"郵輪三雄高度同質，經典配對。需自行跑數據。"},

    "homebuilders": {"name_zh":"房建商","rating":"A","best_use":"both","driver":"房貸利率/新屋需求",
      "tickers":[
        {"ticker":"DHI","company":"D.R. Horton","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"LEN","company":"Lennar","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"PHM","company":"PulteGroup","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"NVR","company":"NVR Inc","cap_tier":"large","purity":"pure","notes":""}],
      "pair_candidates":[["DHI","LEN"]],
      "notes":"對房貸利率高度同向，經典配對。需自行跑數據。"},

    "utilities": {"name_zh":"公用事業","rating":"A","best_use":"both","driver":"利率/受管制電網/用電成長",
      "tickers":[
        {"ticker":"NEE","company":"NextEra Energy","cap_tier":"large","purity":"pure","notes":"再生能源+受管制"},
        {"ticker":"DUK","company":"Duke Energy","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"SO","company":"Southern Company","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"D","company":"Dominion Energy","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"AEP","company":"American Electric Power","cap_tier":"large","purity":"pure","notes":""}],
      "pair_candidates":[["DUK","SO"]],
      "notes":"受管制公用事業對利率敏感、同向;注意與 ai_power_ipp(非管制 IPP)區隔。需自行跑數據。"},

    "big_retail": {"name_zh":"零售","rating":"B","best_use":"both","driver":"消費支出/同店銷售",
      "tickers":[
        {"ticker":"WMT","company":"Walmart","cap_tier":"mega","purity":"pure","notes":"折扣零售"},
        {"ticker":"COST","company":"Costco","cap_tier":"large","purity":"pure","notes":"會員倉儲"},
        {"ticker":"TGT","company":"Target","cap_tier":"large","purity":"pure","notes":""},
        {"ticker":"HD","company":"Home Depot","cap_tier":"large","purity":"pure","notes":"家居"},
        {"ticker":"LOW","company":"Lowe's","cap_tier":"large","purity":"pure","notes":"家居"}],
      "pair_candidates":[["HD","LOW"],["WMT","COST"]],
      "notes":"HD/LOW(家居)、WMT/COST(大賣場)分子群最同質。需自行跑數據。"},

    "restaurants": {"name_zh":"餐飲","rating":"B","best_use":"both","driver":"消費支出/同店銷售",
      "tickers":[
        {"ticker":"MCD","company":"McDonald's","cap_tier":"large","purity":"pure","notes":"速食"},
        {"ticker":"SBUX","company":"Starbucks","cap_tier":"large","purity":"pure","notes":"咖啡"},
        {"ticker":"CMG","company":"Chipotle","cap_tier":"large","purity":"pure","notes":"快休閒"},
        {"ticker":"YUM","company":"Yum! Brands","cap_tier":"large","purity":"pure","notes":"KFC/Taco Bell"}],
      "pair_candidates":[["MCD","YUM"]],
      "notes":"品類差異(速食/咖啡/快休閒)需分子群配對。需自行跑數據。"}
  },
  "ticker_index": {
    "NVDA":["ai_gpu"],"AMD":["ai_gpu"],"AVGO":["ai_asic_networking"],"MRVL":["ai_asic_networking","ai_connectivity_silicon"],"ANET":["ai_asic_networking"],
    "MU":["memory_storage"],"WDC":["memory_storage"],"STX":["memory_storage"],"SNDK":["memory_storage"],
    "AMAT":["semi_equipment"],"LRCX":["semi_equipment"],"KLAC":["semi_equipment"],"ASML":["semi_equipment"],"ENTG":["semi_equipment"],"CAMT":["semi_equipment"],
    "SNPS":["eda"],"CDNS":["eda"],"KEYS":["eda"],
    "TSM":["foundry"],"INTC":["foundry"],"GFS":["foundry"],"UMC":["foundry"],"TSEM":["foundry"],
    "TXN":["analog_auto"],"ADI":["analog_auto"],"NXPI":["analog_auto"],"MCHP":["analog_auto"],"ON":["analog_auto"],"STM":["analog_auto"],"WOLF":["analog_auto"],
    "COHR":["optical_cpo"],"LITE":["optical_cpo"],"FN":["optical_cpo"],"CIEN":["optical_cpo"],"AAOI":["optical_cpo"],
    "ALAB":["ai_connectivity_silicon"],"CRDO":["ai_connectivity_silicon"],
    "CEG":["ai_power_ipp"],"VST":["ai_power_ipp"],"TLN":["ai_power_ipp"],"NRG":["ai_power_ipp"],
    "OKLO":["nuclear_smr"],"SMR":["nuclear_smr"],"NNE":["nuclear_smr"],"BWXT":["nuclear_smr"],
    "EQIX":["data_center_reit"],"DLR":["data_center_reit"],"IRM":["data_center_reit"],
    "CRWV":["neocloud"],"NBIS":["neocloud"],"IREN":["neocloud","crypto_miners"],"APLD":["neocloud"],
    "SMCI":["ai_server_odm"],"DELL":["ai_server_odm"],"HPE":["ai_server_odm"],
    "VRT":["power_cooling"],"ETN":["power_cooling"],"MOD":["power_cooling"],"NVT":["power_cooling"],
    "CRWD":["cybersecurity_endpoint"],"S":["cybersecurity_endpoint"],
    "PANW":["cybersecurity_sase"],"ZS":["cybersecurity_sase"],"FTNT":["cybersecurity_sase"],"NET":["cybersecurity_sase"],"CHKP":["cybersecurity_sase"],
    "OKTA":["cybersecurity_identity"],"SAIL":["cybersecurity_identity"],
    "DDOG":["observability_data"],"SNOW":["observability_data"],"MDB":["observability_data"],"ESTC":["observability_data"],"GTLB":["observability_data"],
    "PLTR":["ai_app_software"],"NOW":["ai_app_software"],"CRM":["ai_app_software"],"PATH":["ai_app_software"],"AI":["ai_app_software"],
    "IONQ":["quantum"],"RGTI":["quantum"],"QBTS":["quantum"],"QUBT":["quantum"],
    "MARA":["crypto_miners"],"RIOT":["crypto_miners"],"CLSK":["crypto_miners"],"CORZ":["crypto_miners"],"WULF":["crypto_miners"],
    "COIN":["crypto_exchange"],"HOOD":["crypto_exchange","brokers","stablecoin_fintech"],"BLSH":["crypto_exchange"],"GEMI":["crypto_exchange"],
    "MSTR":["crypto_treasury_btc"],"XXI":["crypto_treasury_btc"],"BMNR":["crypto_treasury_eth"],"SBET":["crypto_treasury_eth"],
    "CRCL":["stablecoin_fintech"],"SOFI":["stablecoin_fintech"],"UPST":["stablecoin_fintech"],
    "SERV":["robotics_humanoid"],"RR":["robotics_humanoid"],"ISRG":["robotics_industrial"],"ROK":["robotics_industrial"],"SYM":["robotics_industrial"],"TER":["robotics_industrial"],
    "RKLB":["space_launch"],"LUNR":["space_launch"],"FLY":["space_launch"],"VOYG":["space_launch"],
    "ASTS":["space_satcom"],"PL":["space_satcom"],"IRDM":["space_satcom"],"SATS":["space_satcom"],
    "AVAV":["drones_defense"],"KTOS":["drones_defense"],"RCAT":["drones_defense"],"ONDS":["drones_defense"],"UMAC":["drones_defense"],
    "LMT":["defense_primes"],"RTX":["defense_primes"],"NOC":["defense_primes"],"GD":["defense_primes"],"LHX":["defense_primes"],
    "JOBY":["evtol"],"ACHR":["evtol"],"EVTL":["evtol"],"EH":["evtol"],
    "MP":["rare_earth"],"USAR":["rare_earth"],"UUUU":["rare_earth","uranium"],"CRML":["rare_earth"],
    "CCJ":["uranium"],"UEC":["uranium"],"DNN":["uranium"],"LEU":["uranium"],
    "LLY":["glp1"],"NVO":["glp1"],"VKTX":["glp1"],
    "MRK":["big_pharma"],"PFE":["big_pharma"],"ABBV":["big_pharma"],"BMY":["big_pharma"],"JNJ":["big_pharma"],
    "AMGN":["biotech"],"GILD":["biotech"],"VRTX":["biotech"],"REGN":["biotech"],"BIIB":["biotech"],
    "BABA":["china_ecommerce"],"PDD":["china_ecommerce"],"JD":["china_ecommerce"],"BIDU":["china_ecommerce"],
    "NIO":["china_ev"],"XPEV":["china_ev"],"LI":["china_ev"],
    "JPM":["big_banks"],"BAC":["big_banks"],"WFC":["big_banks"],"C":["big_banks"],"GS":["big_banks"],"MS":["big_banks"],
    "USB":["regional_banks"],"PNC":["regional_banks"],"TFC":["regional_banks"],"FITB":["regional_banks"],"MTB":["regional_banks"],"RF":["regional_banks"],"HBAN":["regional_banks"],
    "V":["payment_networks"],"MA":["payment_networks"],"AXP":["payment_networks"],"PYPL":["payment_networks"],"FI":["payment_networks"],"FOUR":["payment_networks"],
    "SCHW":["brokers"],"IBKR":["brokers"],"CME":["brokers"],"ICE":["brokers"],
    "COP":["energy_ep"],"EOG":["energy_ep"],"FANG":["energy_ep"],"OXY":["energy_ep"],"DVN":["energy_ep"],"CTRA":["energy_ep"],"PR":["energy_ep"],"APA":["energy_ep"],"AR":["energy_ep"],
    "SLB":["oilfield_services"],"HAL":["oilfield_services"],"BKR":["oilfield_services"],"WFRD":["oilfield_services"],
    "ENB":["midstream"],"WMB":["midstream"],"EPD":["midstream"],"KMI":["midstream"],"ET":["midstream"],"OKE":["midstream"],"MPLX":["midstream"],
    "DAL":["airlines"],"UAL":["airlines"],"AAL":["airlines"],"LUV":["airlines"],
    "CCL":["cruise_travel"],"RCL":["cruise_travel"],"NCLH":["cruise_travel"],
    "DHI":["homebuilders"],"LEN":["homebuilders"],"PHM":["homebuilders"],"NVR":["homebuilders"],
    "NEE":["utilities"],"DUK":["utilities"],"SO":["utilities"],"D":["utilities"],"AEP":["utilities"],
    "WMT":["big_retail"],"COST":["big_retail"],"TGT":["big_retail"],"HD":["big_retail"],"LOW":["big_retail"],
    "MCD":["restaurants"],"SBUX":["restaurants"],"CMG":["restaurants"],"YUM":["restaurants"],
    "TSLA":["ai_app_software"]
  }
}
```

### (B) Schema 說明文件與程式實作建議

**欄位語意**
- `meta.rating_definitions / cap_tier_definitions`：UI 提示文字來源。
- `sectors.<key>`：`key` 為 snake_case 供程式使用。
  - `name_zh`：繁中+（可加）英文顯示名。
  - `rating`：A/B/C，決定 UI 是否顯示「不建議配對」警示。
  - `best_use`：`momentum`（只做 RS 排名/動能輪動）/`pairs`（可做均值回歸配對）/`both`。
  - `driver`：一句話主驅動因子，用於 UI 說明「為何同籃」。
  - `tickers[]`：每檔含 `ticker`/`company`/`cap_tier`/`purity`/`notes`。
  - `related_tickers[]`：綜合型被剔除的參考標的，UI 顯示為「參考但已剔除（綜合型）」，**不列入預設 peers**。
  - `pair_candidates[]`：1-2 組最可能協整的候選，UI 標註「需自行跑協整檢定」。
  - `notes`：資料注意事項（IPO/分拆/併購/ADR/短歷史）。
- `ticker_index`：反查索引，**主板塊放陣列第一個**。

**查詢與顯示流程（建議）**
1. 使用者輸入 ticker → 先查 `ticker_index[TICKER]`；查無則回「冷門標的，暫無推薦」。
2. 取陣列第一個為主板塊，讀 `sectors[主板塊]`。
3. 推薦 peers = 該板塊 `tickers[]` 排除輸入標的本身。
4. `related_tickers` 另區塊顯示為「參考（綜合型已剔除，原因見 reason）」。
5. 若 `rating === "C"`：UI 頂部紅色警示「僅主題連動，不建議配對，建議僅作動能監控」。
6. 若 `best_use === "momentum"`：隱藏/淡化配對按鈕，只顯示 RS 排名。
7. 顯示 `driver` 作為「同籃理由」；顯示每檔 `notes`（尤其 IPO/重整/併購/ADR 警示）。
8. `pair_candidates` 以醒目標籤呈現，並固定附註「需自行以歷史資料跑相關係數與協整檢定（如 Engle-Granger / Johansen），本表不提供任何統計數值」。
9. 一檔可屬多板塊（如 HOOD、UUUU、IREN、MRVL）→ 提供板塊切換下拉，預設主板塊。
10. `cap_tier` 僅供分層/beta 提示，UI 應標「概估，請以即時行情確認」。

## Recommendations
1. **上線前先接即時市值/流動性 API 校正 `cap_tier` 與剔除停牌/下市標的**（本表為 2026/7 概估）。門檻建議：日均量 < 30 萬股或市值 < 3 億美元者，標記「流動性不足，配對慎用」。
2. **配對交易只在 rating A/B 且 `best_use` 含 `pairs` 的板塊開放**；使用者點「產生配對」時，強制先跑一段（建議 ≥ 250 交易日）協整檢定，p 值門檻 < 0.05 才允許建倉——**本表不提供任何統計值，須即時計算**。
3. **對 rating C（量子、加密財庫、太空、eVTOL、稀土開發商、SMR、neocloud）僅開放 RS 動能排名**，UI 明確警示不做均值回歸。
4. **對有成分變動旗標的標的設「基準重置日」**：WOLF（2025/9/29）、SNDK（2025 分拆）、CEG（2026/1 併 Calpine）、SNPS（2025/7 併 Ansys）、PANW（2026/2 併 CyberArk）、ALAB/CRDO/CRCL/CRWV（IPO 日）——RS 與協整窗口不得跨越該日。
5. **半導體板塊近期 beta 極高（2026/7 單週全球晶片股蒸發逾 1 兆美元）**：建議在 UI 對 ai_gpu / memory_storage / foundry / ai_connectivity_silicon 顯示「近期高波動，RS 排名易失真」提示，並縮小配對部位。
6. **調整觸發條件**：若某主題明顯退燒（成分被併/下市、板塊日均量腰斬、龍頭連兩季負成長），將該板塊 rating 下調一級並在下一版移出或合併子群。

## Caveats
- **絕未提供任何相關係數或協整數值**；所有 `pair_candidates` 僅為「基本面同質性」判斷，統計驗證一律須使用者自行以即時歷史資料計算。
- **市值層級為 2026 年 7 月概估**，且 2026/7/16 為晶片股大跌交易日，半導體市值偏低；務必以即時資料確認 mega/large/mid/small 分層。
- **分類依據為公開資料**（GICS 子產業、公司財報營收結構、產業研究與新聞），惟部分 2026 年數據引用自二手財經媒體（Motley Fool、24/7 Wall St、Yahoo Finance、StockTitan、Gotrade、Intellectia、Forbes、CNBC 等），非皆一手財報；重大分類（綜合型剔除、子群邊界）建議上線前以公司 10-K/10-Q 營收分部再核。
- **綜合型判定具主觀性**：如 AVGO/MRVL（AI 晶片 vs 網通）、OXY（E&P vs 化工）、BKR（油服 vs LNG）、HOOD（券商 vs 加密）、IRM（儲存 vs 資料中心）等，已就主營收驅動指派主板塊並以 related_tickers 標記，使用者可依自身策略調整。
- **ADR / VIE / 雙重上市風險**：中概股（BABA/PDD/JD/BIDU 為 VIE、NIO/XPEV/LI/EH 為 ADR）、TSM/ASML/UMC/TSEM/NVO/STM/ENB 等 ADR 或外國註冊，含退市/匯率/地緣風險，RS 基準可能與美國本土股脫節。
- **本資料為結構化參考，非投資建議**；板塊輪動熱點會隨市場快速變化，建議每季重新盤點成分與 rating。
- 因研究工具額度限制，光通訊/EDA/晶圓代工/類比/能源子群部分數據以委派子代理彙整的公開資料為主，個別小型股（如 AAOI、CRML、SAIL、VOYG）市值與流動性波動大，上線前務必即時校正。