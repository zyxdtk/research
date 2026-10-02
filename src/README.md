# src/ — 报告数据工具集

写行业/个股分析报告时的数据获取工具。所有接口免费、无需登录。配合 skill `research-report-data` 使用。

## 工具

| 工具 | 用途 | 典型用法 |
|------|------|---------|
| `quotes.py` | 腾讯行情：实时价/市值/历史K线 | `python3 quotes.py cap hk01211,sh600487` |
| `em_data.py` | 东财财报：业绩/主营构成/毛利率 | `python3 em_data.py finance 603986,300308` |
| `search.py` | 搜狗移动搜索：新闻/事件摘要 | `python3 search.py "2026年9月 交付量"` |

## 快速示例

```bash
# 1. 拿一组公司实时价+市值（港股hk/沪A sh/深A sz，逗号分隔一次请求）
python3 src/quotes.py cap hk02513,hk00700,sh600487

# 2. 区间涨跌：先拉基准日K线，对比现价
python3 src/quotes.py kline hk02513 2026-09-08 2026-10-02

# 3. 财报数据（营收/净利/同比/ROE，近5个报告期）
python3 src/em_data.py finance 603986,002409

# 4. 主营构成（分业务收入+毛利率；H1分部未披露时自动回退年报）
python3 src/em_data.py biz 300308 2026-06-30

# 5. 新闻/事件（摘要卡片，含来源媒体）
python3 src/search.py "Anthropic IPO 估值"
```

## 报告口径惯例（已在各工具 docstring 中重复）

- **年化PE粗算** = 总市值 ÷ (H1归母净利 × 2)，标注"H1×2年化口径"
- **区间涨跌** = K线基准日收盘 vs 现价，报告标注两个日期
- **同比**用东财接口 SJLTZ/YSTZ 字段（已算好，勿重算）
- **主营构成** H1分部未披露时用年报口径，输出会标注实际报告期
- **搜索结果必须核对时间戳**，搜狗可能返回历史文章

## 已知坑（实测记录）

- 百度/必应直接 curl 会被反爬拦截 → 用搜狗移动版
- 东财主营构成接口 REPORT_DATE 用 `'2026-06-30'` 格式（单引号包裹）
- 腾讯行情返回 GBK 编码，字段以 `~` 分隔，市值在第 46 字段
- 搜索频率过高返回空 → 查询间 sleep 2-3 秒
- pymupdf 读某些 PDF 会挂死 → PDF 文本用 `pdftotext`（brew install poppler）
