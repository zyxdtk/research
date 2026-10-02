#!/usr/bin/env python3
"""搜狗移动版搜索工具——新闻/事件类数据获取

写报告时获取时效性信息（财报点评、行业事件、政策动态）的工具。
搜狗移动版(m.sogou.com)反爬较弱，是免费搜索里较稳定的通道。

用法:
  python3 search.py "2026年9月 新势力 交付量"          # 摘要卡片模式（推荐）
  python3 search.py "长鑫科技 招股书" --raw           # 原始文本扫描模式

输出: 相关摘要卡片（title + content），每条含来源媒体与时间。

已知坑（2026-10会话实测）:
  - 百度/必应直接curl会被反爬拦截（302/验证码），搜狗移动版可用
  - 结果可能返回历史文章（如2024年），必须核对时间戳
  - 频率过高会返回空，两次查询间建议 sleep 2-3 秒
  - 网页正文级提取不可靠，摘要卡片是主要产出；需要全文时改用 browser 工具
"""
import html
import re
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"}


def search(query: str, out_n: int = 15, raw: bool = False):
    url = "https://m.sogou.com/web/searchList.jsp?keyword=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers=UA)
    raw_html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", errors="ignore")

    # 摘要卡片: title/content JSON 片段（含转义）
    cards = re.findall(r'\\"title\\":\\"(.*?)\\",\\"content\\":\\"(.*?)\\"', raw_html)
    if not cards:
        cards = re.findall(r'"title":"(.*?)","content":"(.*?)"', raw_html)

    seen, n = set(), 0
    for t, c in cards:
        t = t.encode().decode("unicode_escape", errors="ignore") if "\\u" in t else t
        c = c.encode().decode("unicode_escape", errors="ignore") if "\\u" in c else c
        c = re.sub(r"<[^>]+>", "", c)
        key = t[:30]
        if key in seen or len(c) < 20:
            continue
        seen.add(key)
        print(f"[{t[:60]}] {c[:220]}")
        print("---")
        n += 1
        if n >= out_n:
            return

    if n == 0 and raw:
        # fallback: 普通文本扫描
        txt = html.unescape(re.sub(r"<[^>]+>", " ", raw_html))
        txt = re.sub(r"\s+", " ", txt)
        for m in re.finditer(r".{30}(净利|业绩|半年报|财报|营收|交付|销量|融资|IPO).{80}", txt):
            print(m.group(0)[:130])
            print("---")
            n += 1
            if n >= out_n:
                break
    if n == 0:
        print("（无结果，可能被限流——稍后重试或换查询词）")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    raw = "--raw" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--raw" and not a.startswith("--")]
    search(args[0], int(args[1]) if len(args) > 1 else 15, raw)
    time.sleep(2)  # 防限流
