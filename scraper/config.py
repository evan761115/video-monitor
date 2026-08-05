# -*- coding: utf-8 -*-
"""
媒體來源設定
------------
method:
  "rss"        -> 該媒體有官方 RSS，直接用 feedparser 讀取，最穩定。
  "youtube"    -> 用該媒體官方 YouTube 頻道內建的 RSS 當主要來源（不用 API 金鑰、
                  不用爬蟲，比爬新聞網站文字列表穩定很多）。
  "html"       -> 前兩者都沒有，需要直接爬該媒體的影音／娛樂列表頁。
                  selector 需要你打開瀏覽器「開發人員工具」比對實際頁面後填入，
                  這裡先放一個常見結構的預設值，不保證每站都適用，需要自行調整維護。

youtube_channel_id:
  YouTube 頻道格式固定：https://www.youtube.com/feeds/videos.xml?channel_id=頻道ID
  即使 method 不是 "youtube"，只要這欄有值，主要來源失敗時也會自動改用它當備援。

  怎麼找頻道 ID：
    1. Google 搜尋「媒體名稱 YouTube」找到官方頻道
    2. 打開頻道頁面，如果網址已經是 /channel/UCxxxxxxxx 形式，UC 開頭那串就是了
    3. 如果網址是 @手把（例如 /@TVBSSTAR），在頻道頁按右鍵「檢視網頁原始碼」，
       用 Ctrl+F 搜尋 "channel_id="，後面那串 UC 開頭的字串就是

status: "confirmed"（已實際驗證可用） / "unverified"（尚未驗證，需自行確認）

目前現況（2026/08 整理）：
  - 全部 14 家都改用官方 YouTube 頻道當來源，確保看到的是「影音」而不是純文字新聞。
  - 每家的頻道 ID 都已查好、確認頻道真實存在，但頻道實際更新的內容還沒有在
    真正的網路環境下實際執行驗證過，第一次跑 GitHub Actions 之後，
    麻煩檢查一下 Actions 的執行紀錄，確認每家都有抓到東西。
  - 「抓不到資料的媒體，程式會直接跳過、不會出現在網頁上」，不會顯示
    「尚未取得資料」這種空位，維持畫面乾淨。
"""

SOURCES = [
    {
        "id": "ltn",
        "name": "自由娛樂",
        "color": "#0891B2",
        "method": "youtube",
        "url": "https://ent.ltn.com.tw/",
        "status": "confirmed",
        "youtube_channel_id": "UCM3EQ8dzKqzuOwLHM5nSVqQ",
        "note": "自由時報官方「自由娛樂頻道」YouTube，已驗證頻道存在。",
    },
    {
        "id": "udn",
        "name": "聯合新聞網",
        "color": "#1D4ED8",
        "method": "youtube",
        "url": "https://udn.com/rssfeed/news/2/6638/7314?ch=news",
        "status": "unverified",
        "youtube_channel_id": "UCeF6JP-sxqJnznCAQo_K66g",
        "note": "udn RSS 頻道代碼需自行確認；已找到官方「噓！星聞」YouTube 頻道，可直接當主要來源。",
    },
    {
        "id": "ettoday", "name": "東森新聞", "color": "#059669",
        "method": "youtube",
        "url": "https://star.ettoday.net/news/videonews",
        "status": "unverified",
        "selector": {"item": "article", "title": "h3, h2", "link": "a", "time": "time"},
        "youtube_channel_id": "UCX157UE-NdaUGQJDkQ-XKnw",
        "note": "ETtoday（原東森新聞電子報）robots.txt 不允許自動存取列表頁；已找到官方「ETtoday星光雲」YouTube 頻道，建議直接用 YouTube 當主要來源。",
    },
    {
        "id": "setn", "name": "三立新聞網", "color": "#DC2626",
        "method": "youtube",
        "url": "https://star.setn.com/",
        "status": "unverified",
        "selector": {"item": ".newsimg-list li, .card", "title": "h3, .infoshow", "link": "a", "time": ".time"},
        "youtube_channel_id": "UC2hslcZZSHF1u_KW4LPrRPA",
        "note": "已找到官方「娛樂星聞」YouTube 頻道，可直接當主要來源，不用煩惱網頁 selector。",
    },
    {
        "id": "chinatimes", "name": "中時電子報", "color": "#7C3AED",
        "method": "youtube",
        "url": "https://<你的RSSHub網域>/chinatimes/entertainment",
        "status": "unverified",
        "youtube_channel_id": "UCwRnPA_4nczgXL4qLSva4SQ",
        "note": "官方無公開 RSS；RSSHub 公用示範站常被中時擋 403。已找到官方「中時娛樂影音」YouTube 頻道，建議直接用 YouTube 當主要來源。",
    },
    {
        "id": "nownews", "name": "NOWnews", "color": "#EA580C",
        "method": "youtube",
        "url": "https://www.nownews.com/cat/entertainment/",
        "status": "unverified",
        "selector": {"item": "article", "title": "h2, h3", "link": "a", "time": "time"},
        "youtube_channel_id": "UCg8EwsqYmiw7G267xxPyXsg",
        "note": "已找到官方 NOWNEWS YouTube 頻道，可直接當主要來源。",
    },
    {
        "id": "appledaily", "name": "壹蘋新聞", "color": "#BE123C",
        "method": "youtube",
        "url": "https://tw.nextapple.com/entertainment",
        "status": "unverified",
        "selector": {"item": "article, .article-item", "title": "h2, h3", "link": "a", "time": "time"},
        "youtube_channel_id": "UC-nyoCh8UmaRic641ZZ8eNw",
        "note": "已找到官方壹蘋新聞網 YouTube 頻道，可直接當主要來源。",
    },
    {
        "id": "mnews", "name": "鏡新聞", "color": "#0D9488",
        "method": "youtube",
        "url": "https://www.mnews.tw/category/entertainment",
        "status": "unverified",
        "selector": {"item": "article", "title": "h2, h3", "link": "a", "time": "time"},
        "youtube_channel_id": "UC4LjkybVKXCDlneVXlKAbmw",
        "note": "已找到官方鏡新聞 YouTube 頻道，可直接當主要來源。",
    },
    {
        "id": "mirrorweekly", "name": "鏡週刊", "color": "#B45309",
        "method": "youtube",
        "url": "https://www.mirrormedia.mg/category/entertainment",
        "status": "unverified",
        "selector": {"item": "article, .story-item", "title": "h2, h3", "link": "a", "time": "time"},
        "youtube_channel_id": "UCYkldEK001GxR884OZMFnRw",
        "note": "已找到官方鏡週刊 YouTube 頻道，可直接當主要來源。",
    },
    {
        "id": "tvbs", "name": "TVBS", "color": "#E63946",
        "method": "youtube",
        "url": "https://news.tvbs.com.tw/entertainment",
        "status": "unverified",
        "selector": {"item": "a.list_item, li", "title": "h3, .txt", "link": "a", "time": ".time"},
        "youtube_channel_id": "UC6mKt23kUUH4jhRwnP6UDqA",
        "note": "已找到官方「TVBS娛樂頭條」YouTube 頻道，可直接當主要來源，不用煩惱網頁 selector。",
    },
    {
        "id": "vl", "name": "緯來新聞", "color": "#F97316",
        "method": "youtube",
        "url": "https://news.vl.com.tw/category/entertainment",
        "status": "unverified",
        "selector": {"item": "article", "title": "h2, h3", "link": "a", "time": "time"},
        "youtube_channel_id": "UChjlMD6F1rx2gy2g2FM9xJA",
        "note": "需人工核對實際 DOM 結構；已找到官方緯來新聞網 YouTube 頻道，可直接當主要來源。",
    },
    {
        "id": "cna", "name": "中央社", "color": "#16A34A",
        "method": "youtube",
        "url": "https://www.cna.com.tw/",
        "status": "confirmed",
        "youtube_channel_id": "UC7ymKGCl6EVLh7z6sq7TBZA",
        "note": "中央社官方 YouTube 頻道（CNA Taiwan），已驗證頻道存在。內容偏國際新聞/時事，非純娛樂，但屬於官方發布的真實影音內容。",
    },
    {
        "id": "ftv", "name": "民視", "color": "#0EA5E9",
        "method": "youtube",
        "url": "https://www.ftvnews.com.tw/",
        "status": "unverified",
        "youtube_channel_id": "UCU7fH2nrs8HNAfWBp9iQASA",
        "note": "已找到官方「民視綜藝娛樂 Formosa TV Entertainments」YouTube 頻道，內容偏綜藝節目片段，不完全是新聞快訊格式，但屬於官方發布的影音內容。",
    },
    {
        "id": "gtv", "name": "八大電視", "color": "#DB2777",
        "method": "youtube",
        "url": "https://www.gtv.com.tw/",
        "status": "unverified",
        "youtube_channel_id": "UC-soAGoggvBpjr_eVAzxYpA",
        "note": "已找到官方「GTV八大電視」YouTube 頻道；八大是台灣主要綜藝/戲劇製作台，內容以戲劇綜藝片段為主，不完全是新聞快訊格式。",
    },
]
