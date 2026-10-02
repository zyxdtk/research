#!/usr/bin/env python3
"""腾讯行情数据工具（qt.gtimg.cn 实时行情 + ifzq.gtimg.cn 历史K线）

写行业/个股报告时的标准数据源。所有接口免费、无需登录，但有频率限制，
批量查询请合并 codes 参数（逗号分隔一次请求）。

用法:
  python3 quotes.py price hk01211,sh600487,sz300308     # 实时价+涨跌%+时间
  python3 quotes.py cap  hk01211,sh600487               # 实时价+总市值(亿)
  python3 quotes.py kline hk02513 2026-09-01 2026-10-02 # 港股日K（开/收/高/低）
  python3 quotes.py kline sz300308 2026-07-28 2026-08-03 # A股日K

代码前缀: hkXXXX=港股(5位) shXXXX=沪A szXXXX=深A usXXXX=美股(仅实时价)
市值单位: 亿（港股为亿港元，A股为亿人民币）

报告口径惯例:
  - 区间涨跌: 用 kline 拉基准日+现价对比，如 7/30→10/2
  - 年化PE粗算 = 总市值 ÷ (H1归母净利 × 2)，注意标注"H1×2年化口径"
"""
import json
import sys
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read()


def realtime(codes: str):
    """实时行情。codes: 逗号分隔，如 'hk01211,sh600487'"""
    raw = _get(f"https://qt.gtimg.cn/q={codes}").decode("gbk", errors="ignore")
    rows = []
    for line in raw.strip().split(";"):
        line = line.strip()
        if "=" not in line or '"~"' not in line and "~" not in line:
            continue
        f = line.split("~")
        if len(f) < 47:
            continue
        rows.append({
            "name": f[1], "price": f[3], "change_pct": f[32] + "%",
            "time": f[30], "mcap_yi": f[45],  # 总市值，单位亿
        })
    return rows


def kline(code: str, start: str, end: str, count: int = 320):
    """历史日K。港股走 hkfqkline，A股走 fqkline（均前复权 qfq）"""
    if code.startswith("hk"):
        url = (f"https://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get?"
               f"param={code},day,{start},{end},{count},qfq")
    else:
        url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
               f"param={code},day,{start},{end},{count},qfq")
    d = json.loads(_get(url))
    k = list(d["data"].values())[0]
    kl = k.get("qfqday") or k.get("day") or []
    return [{"date": r[0], "open": r[1], "close": r[2], "high": r[3], "low": r[4]} for r in kl]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "price":
        for r in realtime(sys.argv[2]):
            print(f"{r['name']}\t{r['price']}\t{r['change_pct']}\t{r['time']}")
    elif cmd == "cap":
        for r in realtime(sys.argv[2]):
            print(f"{r['name']}\t最新:{r['price']}\t总市值:{r['mcap_yi']}亿")
    elif cmd == "kline":
        for r in kline(sys.argv[2], sys.argv[3], sys.argv[4]):
            print(f"{r['date']}\t开{r['open']}\t收{r['close']}\t高{r['high']}\t低{r['low']}")
    else:
        print(__doc__)
