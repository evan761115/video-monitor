# 影音熱點雷達｜使用說明

## 現況總覽（共 14 家）

| 媒體 | 資料來源 | 狀態 |
|---|---|---|
| 自由娛樂、中央社 | 官方新聞 RSS | ✅ 已驗證，穩定 |
| 聯合新聞網、東森新聞、三立新聞網、中時電子報、NOWnews、壹蘋新聞、鏡新聞、鏡週刊、TVBS、緯來新聞、民視、八大電視 | 官方 YouTube 頻道 RSS | ✅ 頻道 ID 已查好、程式邏輯正確；**建議第一次跑完 GitHub Actions 後，去 Actions 的執行紀錄確認每家都有抓到資料**（YouTube 頻道會不會臨時調整內容政策不是我能保證的事） |

原本清單裡的「時報週刊」找不到官方 YouTube 頻道、網頁也抓不穩，已經移除。
新加入「中央社」（國家通訊社，官方 RSS，公信力高）、「民視」「八大電視」
（台灣主要綜藝/戲劇/新聞台，官方 YouTube 頻道已找到）。

民視、八大這兩家的頻道內容比較偏向綜藝節目片段，不是純粹的「新聞快訊」格式，
如果你只想要新聞快訊風格，可以之後在 `scraper/config.py` 裡把它們刪掉即可。

**這些新聞網站幾乎都不公開「影音觀看數」**，所以腳本不會生出假數字，改用「站方排序」呈現。

## 檔案結構

```
index.html                          前端網頁
scraper/
  config.py                         12 家媒體的來源設定
  fetch_media.py                    抓取腳本，執行後產生 data.json
  requirements.txt
.github/workflows/update-data.yml   GitHub Actions：每 15 分鐘自動重跑一次
```

## 放到 GitHub 上（推薦，全部免費，設定一次之後全自動）

**Step 1／建立 Repository**
1. 到 https://github.com/new 建立一個新 repository（Public 或 Private 都可以，Private 也能用 GitHub Pages，但需要付費方案才能開 Pages——不確定的話選 Public 最省事）
2. 不用勾任何初始化選項，建立空的 repo 就好

**Step 2／把檔案上傳上去**
1. 進到剛建好的 repo 頁面，點 **「uploading an existing file」**（或 Add file → Upload files）
2. 把這個資料夾裡的**所有檔案和資料夾**（`index.html`、`scraper/`、`.github/`、`README.md`）整個拖進去
   - 注意：`.github` 資料夾名稱開頭是點，有些檔案總管預設會隱藏，記得連同 `.github/workflows/update-data.yml` 一起上傳，這是自動排程的關鍵
3. 點 **Commit changes**

**Step 3／開啟自動排程**
1. 點 repo 上方的 **Actions** 分頁
2. 如果看到提示要啟用 workflow，點 **I understand my workflows, go ahead and enable them**
3. 左側應該會看到「更新影音監測資料」這個 workflow，點進去，右邊點 **Run workflow** 手動觸發一次，確認能順利跑完（綠勾勾）
   - 如果跑出來是叉叉，點進去看 log，通常是某家媒體抓取出錯，不影響其他家，可以先無視，之後再照下面「修正某家媒體」處理
   - 之後它會照 `.github/workflows/update-data.yml` 設定的排程，每 15 分鐘自動重跑一次，不用再手動點

**Step 4／開啟 GitHub Pages（讓網頁有網址可以看）**
1. 進 repo 的 **Settings → Pages**
2. Source 選 **Deploy from a branch**，Branch 選 **main**、資料夾選 **/(root)**，按 Save
3. 等 1-2 分鐘，畫面會出現一個網址，長得像
   `https://你的帳號.github.io/repo名稱/`
   打開它就是正式版網頁，之後每次 Actions 重新產生 data.json，這個網址都會自動顯示最新內容

完成以上四步之後，你不用再做任何事——網頁會自己每 15 分鐘更新一次資料。

## 本機測試（不上傳 GitHub，先自己看看）

```bash
cd scraper
pip install -r requirements.txt
python fetch_media.py
```

執行完會在 `scraper/` 底下產生 `data.json`，複製到跟 `index.html` 同一層，
**用簡單的本機伺服器打開**（直接雙擊開檔案會因為瀏覽器安全限制讀不到 data.json）：

```bash
python -m http.server
```

再用瀏覽器打開 `http://localhost:8000`。

## 修正某家媒體抓不到資料的問題

**如果是 method: "youtube" 的媒體抓不到：**
去 Actions 執行紀錄看錯誤訊息；常見原因是頻道 ID 打錯或頻道被下架/改名，
重新搜尋「媒體名稱 YouTube」確認頻道 ID 是否還正確。

**如果是 method: "html" 的媒體：**
目前 14 家都不是用 html 爬蟲了（除非你之後自己加新的媒體來源選擇這個方式）。
1. 打開該媒體的娛樂/影音列表頁，按 F12 開開發人員工具
2. 找到每一則新聞外層的重複區塊（例如 `<article>`、`<li class="...">`），
   還有標題、連結、時間各自的標籤／class
3. 回到 `scraper/config.py`，把對應的 `selector` 改成正確的值
4. Commit 回 GitHub，等下一次 Actions 執行，或手動點 Run workflow

## 版權提醒

自由時報的 RSS 有明文允許非商業使用但須標明出處；其餘皆為公開的 YouTube 官方頻道
內建 RSS，屬於媒體自己公開發布的資訊。建議僅供公司內部監測比較使用，不要整篇重製
內容或做商業散布。

## 之後可以再擴充的方向

- 如果想加更多媒體，照 `scraper/config.py` 開頭的說明，找官方 RSS 或 YouTube 頻道 ID 即可。
- 把 `data.json` 存進資料庫，累積歷史資料，之後可以看「熱度變化趨勢」而不只是當下快照。
- 加上真正的觀看數／互動數比較（目前這些網站都不公開，如果之後想做，
  需要另外串接如 YouTube Data API 這類正式數據源）。
