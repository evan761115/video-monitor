# -*- coding: utf-8 -*-
"""
影音熱點雷達 - 資料抓取腳本
============================
把 config.py 裡列出的媒體來源，統一整理成前端網頁看得懂的 data.json。

執行方式：
    pip install -r requirements.txt
    python fetch_media.py

輸出：
    ./data.json  （前端 index.html 會用 fetch('data.json') 讀取這份檔案）

老實說在前面（很重要，請先讀完再用）：
--------------------------------------------------------------
1. 這些新聞網站幾乎都「不公開影音的實際觀看數」，所以本腳本不會生出假的觀看數字。
   排序依據是「該媒體網站自己排出來的順序」（通常就是編輯設定的熱門/最新順序），
   前端會顯示「站方排序」而不是「觀看數」，這樣才不會顯示不存在的假數據。

2. method="rss" 的來源最穩定，因為是媒體官方提供的正式格式。
   method="html" 的來源，selector 是「猜測值」，網站改版就會失效，
   你需要用瀏覽器開發人員工具（F12）比對實際的 HTML 結構後，
   到 config.py 把 selector 修正成正確的值。

3. method="rsshub" 的來源，建議自己架一份 RSSHub（開源專案，GitHub: DIYgod/RSSHub），
   公用示範站常被目標網站擋掉。自架後把 config.py 的網址換成你自己的 RSSHub 網域即可。

4. 請遵守各媒體網站的使用條款（服務條款/robots.txt），這份腳本僅供內部監測比較用途，
   不要拿去做商業散布或大量非法重製全文。
"""

import json
import re
import time
from datetime import datetime, timezone

import feedparser
import requests
from bs4 import BeautifulSoup

from config import SOURCES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}
TIMEOUT = 12
MAX_ITEMS = 10


def fetch_rss(source):
    """讀官方 RSS。回傳 list of dict。"""
    feed = feedparser.parse(source["url"])
    items = []
    for entry in feed.entries[:MAX_ITEMS]:
        items.append({
            "title": entry.get("title", "").strip(),
            "link": entry.get("link", ""),
            "time": format_time(entry),
            "tag": (entry.get("tags")[0]["term"] if entry.get("tags") else "娛樂"),
        })
    return items


def fetch_youtube(channel_id):
    """讀 YouTube 頻道內建的 RSS（官方功能，不用 API 金鑰）。"""
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:MAX_ITEMS]:
        items.append({
            "title": entry.get("title", "").strip(),
            "link": entry.get("link", ""),
            "time": format_time(entry),
            "tag": "影音",
        })
    return items


def fetch_html(source):
    """用 requests + BeautifulSoup 爬列表頁，selector 來自 config.py。"""
    resp = requests.get(source["url"], headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    sel = source.get("selector", {})
    nodes = soup.select(sel.get("item", "article"))[:MAX_ITEMS]

    items = []
    for node in nodes:
        title_el = node.select_one(sel.get("title", "h3"))
        link_el = node if node.name == "a" else node.select_one(sel.get("link", "a"))
        time_el = node.select_one(sel.get("time", "time"))

        title = title_el.get_text(strip=True) if title_el else node.get_text(strip=True)[:60]
        link = link_el.get("href", "") if link_el else ""
        if link and link.startswith("/"):
            base = re.match(r"https?://[^/]+", source["url"])
            link = (base.group(0) if base else "") + link

        if not title:
            continue

        items.append({
            "title": title,
            "link": link,
            "time": time_el.get_text(strip=True) if time_el else "",
            "tag": "娛樂",
        })
    return items


def format_time(entry):
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            dt = datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
            return dt.astimezone().strftime("%m/%d %H:%M")
    return ""


def build():
    result = []
    for source in SOURCES:
        entry = {
            "id": source["id"],
            "name": source["name"],
            "color": source["color"],
            "status": "ok",
            "items": [],
        }
        # 依 method 決定主要抓取方式；如果主要方式失敗或抓到空的，
        # 只要這家有設定 youtube_channel_id，就自動改抓該媒體的官方 YouTube 頻道。
        try:
            if source["method"] == "rss":
                entry["items"] = fetch_rss(source)
            elif source["method"] == "youtube":
                entry["items"] = fetch_youtube(source["youtube_channel_id"])
            elif source["method"] in ("html", "rsshub"):
                entry["items"] = fetch_html(source)
        except Exception as exc:
            entry["status"] = f"error: {exc}"
            print(f"[警告] {source['name']}（{source['id']}）主要來源抓取失敗：{exc}")

        if not entry["items"] and source.get("youtube_channel_id") and source["method"] != "youtube":
            try:
                entry["items"] = fetch_youtube(source["youtube_channel_id"])
                if entry["items"]:
                    entry["status"] = "ok (youtube fallback)"
                    print(f"[提示] {source['name']} 改用 YouTube 頻道資料。")
            except Exception as exc:
                entry["status"] = f"error: youtube fallback failed: {exc}"
                print(f"[警告] {source['name']}（{source['id']}）YouTube 備援也抓取失敗：{exc}")

        if not entry["items"]:
            entry["status"] = entry["status"] if entry["status"] != "ok" else "empty"
            print(f"[提醒] {source['name']} 目前沒有抓到資料，selector 或 youtube_channel_id 可能需要調整。")

        result.append(entry)

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "media": result,
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\n完成，寫入 data.json（{len(result)} 家媒體）")


if __name__ == "__main__":
    build()
