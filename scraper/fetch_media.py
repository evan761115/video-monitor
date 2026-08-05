# -*- coding: utf-8 -*-
"""
影音熱點雷達 - 資料抓取腳本
============================
把 config.py 裡列出的媒體來源，統一整理成前端網頁看得懂的 data.json。

執行方式：
    pip install -r requirements.txt
    export YOUTUBE_API_KEY=你的金鑰      # Mac/Linux
    python fetch_media.py

輸出：
    ./data.json  （前端 index.html 會用 fetch('data.json') 讀取這份檔案）

老實說在前面（很重要，請先讀完再用）：
--------------------------------------------------------------
1. YouTube 頻道現在改用「YouTube Data API v3」正式 API 抓取，需要一把免費的
   API 金鑰（Google Cloud Console 申請），透過環境變數 YOUTUBE_API_KEY 傳進來。
   之前用免費、不用金鑰的 /feeds/videos.xml 端點，會被 GitHub Actions 這類
   雲端主機的共用 IP 直接 404 擋掉，換成正式 API 就不會有這個問題。

2. 這些媒體的 YouTube 頻道大多不公開精確觀看數，所以本腳本不會生出假的
   觀看數字。排序依據是「該頻道自己發布的時間順序」，前端會顯示「站方排序」
   而不是「觀看數」，這樣才不會顯示不存在的假數據。

3. 抓不到資料的媒體（頻道被下架、改名、或臨時連不上），會直接跳過、
   不會寫進 data.json，網頁上也不會出現空白或「尚未取得資料」的卡片，
   保持畫面乾淨。要知道哪家被跳過，看執行紀錄裡的 [跳過] 訊息即可。

4. 請遵守各媒體網站的使用條款，這份腳本僅供內部監測比較用途，
   不要拿去做商業散布或大量非法重製全文。
"""

import json
import os
import re
import time
from datetime import datetime, timezone

import feedparser
import requests
from bs4 import BeautifulSoup

from config import SOURCES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}
TIMEOUT = 15
MAX_ITEMS = 10
MAX_RETRIES = 3

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


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
    """用 YouTube Data API v3 抓該頻道最新上傳的影片，順便拿縮圖網址。

    做法：每個頻道的「所有上傳影片」都會自動有一個播放清單，
    ID 就是把頻道 ID 開頭的 UC 換成 UU（YouTube 的固定規則），
    查那個播放清單，比查整個頻道更省配額、也更穩定。
    """
    if not YOUTUBE_API_KEY:
        raise RuntimeError(
            "沒有設定 YOUTUBE_API_KEY 環境變數。請先申請 YouTube Data API v3 金鑰，"
            "本機測試用 `export YOUTUBE_API_KEY=你的金鑰`，"
            "GitHub Actions 則是在 repo Settings → Secrets 設定同名的 secret。"
        )

    uploads_playlist_id = "UU" + channel_id[2:] if channel_id.startswith("UC") else channel_id

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(
                f"{YOUTUBE_API_BASE}/playlistItems",
                params={
                    "part": "snippet",
                    "playlistId": uploads_playlist_id,
                    "maxResults": MAX_ITEMS,
                    "key": YOUTUBE_API_KEY,
                },
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            if resp.status_code == 403:
                # 常見原因：金鑰額度用完、或金鑰還沒啟用 YouTube Data API v3
                raise RuntimeError(f"403 權限錯誤（可能是金鑰額度用完或 API 未啟用）：{resp.text[:200]}")
            resp.raise_for_status()
            data = resp.json()

            items = []
            for video in data.get("items", [])[:MAX_ITEMS]:
                snippet = video.get("snippet", {})
                video_id = snippet.get("resourceId", {}).get("videoId", "")
                thumbnails = snippet.get("thumbnails", {})
                thumb = (
                    thumbnails.get("medium", {}).get("url")
                    or thumbnails.get("default", {}).get("url")
                    or ""
                )
                published = snippet.get("publishedAt", "")
                time_str = ""
                if published:
                    try:
                        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                        time_str = dt.astimezone().strftime("%m/%d %H:%M")
                    except ValueError:
                        pass
                items.append({
                    "title": snippet.get("title", "").strip(),
                    "link": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
                    "time": time_str,
                    "tag": "影音",
                    "thumbnail": thumb,
                })
            return items
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"

        if attempt < MAX_RETRIES:
            time.sleep(2 * attempt)

    raise RuntimeError(f"重試 {MAX_RETRIES} 次後仍失敗：{last_error}")


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
    for i, source in enumerate(SOURCES):
        if i > 0:
            # 每家之間停一下，不要一次密集炸 YouTube，降低被當機器人擋掉的機會。
            time.sleep(1.5)

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
            entry["status"] = f"error: {type(exc).__name__}: {exc}"
            print(f"[警告] {source['name']}（{source['id']}）主要來源抓取失敗：{type(exc).__name__}: {exc}")

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
            # 照要求：抓不到資料的媒體直接跳過、不寫進 data.json，
            # 不留「尚未取得資料」這種空位在畫面上。
            print(f"[跳過] {source['name']} 目前抓不到資料，這次不會出現在網頁上。")
            continue

        result.append(entry)

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "media": result,
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\n完成：{len(result)} / {len(SOURCES)} 家媒體成功寫入 data.json")
    if len(result) < len(SOURCES):
        skipped = [s['name'] for s in SOURCES if s['id'] not in {e['id'] for e in result}]
        print(f"這次沒抓到、被跳過的媒體：{', '.join(skipped)}")


if __name__ == "__main__":
    build()
