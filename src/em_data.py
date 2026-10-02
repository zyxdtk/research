#!/usr/bin/env python3
"""东方财富数据中心API工具——财报数据（业绩报表/主营构成/毛利率）

写报告时的财务数据标准来源（正式财报口径，可信度高）。
所有接口免费，datacenter.eastmoney.com，columns=ALL 时字段最全。

用法:
  python3 em_data.py finance 603986,002409,300308   # 业绩报表：营收/净利/同比（近5个报告期）
  python3 em_data.py biz 300308 2026-06-30          # 主营构成：分业务/分地区收入+毛利率
  python3 em_data.py gm 300308 2026-06-30           # 毛利率+研发费用

A股代码：6位数字（沪市6开头/深市0或3开头）。BIZ接口按报告期过滤，
2026H1分部未披露时回退 2025-12-31（年报口径），输出会标注实际使用的报告期。

报告口径惯例:
  - H1同比 = (H1净利-去年同期)/去年同期，接口字段 SJLTZ 已算好
  - 年化PE = 市值 ÷ (H1净利×2)，配合 quotes.py cap 的市值使用
  - ROE用接口 WEIGHTAVG_ROE（加权平均，报告披露口径）
"""
import json
import sys
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def _fetch(report_name: str, columns: str, filt: str, page_size=12, sort: str = ""):
    """sort: 形如 'REPORTDATE,-1'；部分接口（如MAINOP主营构成）无REPORTDATE列，必须传空"""
    sort_part = ""
    if sort:
        col, order = sort.split(",")
        sort_part = f"&sortColumns={col}&sortTypes={order}"
    url = (f"https://datacenter.eastmoney.com/securities/api/data/v1/get?"
           f"reportName={report_name}&columns={columns}"
           f"&filter={urllib.parse.quote(filt)}&pageSize={page_size}"
           f"{sort_part}&source=HSF10&client=PC")
    req = urllib.request.Request(url, headers=UA)
    d = json.load(urllib.request.urlopen(req, timeout=20))
    return (d.get("result") or {}).get("data") or []


def finance(codes: str):
    """业绩报表：营收/净利/同比/ROE，近5个报告期"""
    for code in codes.split(","):
        code = code.strip()
        rows = _fetch("RPT_LICO_FN_CPD", "ALL",
                      f'(SECURITY_CODE="{code}")', page_size=10, sort="REPORTDATE,-1")
        for r in rows:
            rd = (r.get("REPORTDATE") or "")[:10]
            if rd.endswith(("12-31", "06-30", "03-31", "09-30")):
                rev, np_ = r.get("TOTAL_OPERATE_INCOME"), r.get("PARENT_NETPROFIT")
                rev_s = f"{rev/1e8:.2f}" if rev else "?"
                np_s = f"{np_/1e8:.2f}" if np_ else "?"
                print(f"{r.get('SECURITY_NAME_ABBR')} {rd} "
                      f"营收:{rev_s}亿(+{r.get('YSTZ'):.1f}%) "
                      f"净利:{np_s}亿(+{r.get('SJLTZ'):.1f}%) "
                      f"ROE:{r.get('WEIGHTAVG_ROE')}")


def _secucode(code: str) -> str:
    suffix = "SH" if code.startswith("6") else ("BJ" if code.startswith(("4", "8")) else "SZ")
    return f"{code}.{suffix}"


def biz(code: str, report_date: str = ""):
    """主营构成：分产品/分地区收入与毛利率。report_date为空时自动回退年报"""
    dates = [report_date] if report_date else []
    dates += ["2026-06-30", "2025-12-31"]
    for rd in dates:
        rows = _fetch("RPT_F10_FN_MAINOP",
                      "SECUCODE,REPORT_DATE,MAINOP_TYPE,ITEM_NAME,MAIN_BUSINESS_INCOME,MBI_RATIO,GROSS_RPOFIT_RATIO",
                      f'(SECUCODE="{_secucode(code)}")(REPORT_DATE=\'{rd}\')', page_size=40)
        if rows:
            print(f"== 主营构成 {rd}")
            for r in rows:
                inc = r.get("MAIN_BUSINESS_INCOME")
                print(f"  {r.get('MAINOP_TYPE')} | {r.get('ITEM_NAME')} | "
                      f"收入{round(inc/1e8,1) if inc else '?'}亿 | "
                      f"占比{round((r.get('MBI_RATIO') or 0)*100,1)}% | "
                      f"毛利率{round((r.get('GROSS_RPOFIT_RATIO') or 0)*100,1)}%")
            return
    print("主营构成：各报告期均未返回数据")


def gm(code: str, report_date: str = "2026-06-30"):
    """毛利率+研发费用（利润表口径计算）"""
    rows = _fetch("RPT_F10_FINANCE_GINCOME",
                  "REPORT_DATE,TOTAL_OPERATE_INCOME,OPERATE_COST,RESEARCH_EXPENSE",
                  f'(SECUCODE="{_secucode(code)}")(REPORT_DATE=\'{report_date}\')', page_size=5)
    for r in rows:
        rev, cost, rd_exp = r.get("TOTAL_OPERATE_INCOME"), r.get("OPERATE_COST"), r.get("RESEARCH_EXPENSE")
        gm_v = (rev - cost) / rev * 100 if rev and cost else None
        print(f"{report_date} 毛利率:{gm_v:.1f}%" if gm_v else report_date,
              f"研发:{round(rd_exp/1e8,1) if rd_exp else '?'}亿")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "finance":
        finance(sys.argv[2])
    elif cmd == "biz":
        biz(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    elif cmd == "gm":
        gm(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "2026-06-30")
    else:
        print(__doc__)
