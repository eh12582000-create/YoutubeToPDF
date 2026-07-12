# 美食地圖工作流（給 Claude）

觸發：使用者貼 IG / YouTube / FB 美食影片連結並說「加進美食地圖」「更新美食地圖」，
或只貼連結且內容明顯是美食影片時主動詢問是否要加入地圖。

## 步驟

1. **取得內容**
   - YouTube/Bilibili：優先 `yt-dlp --skip-download --write-auto-subs`；無字幕走
     `~/.claude/skills/youtube-to-pdf/scripts/transcribe.py` 轉錄
   - IG / FB：先試 `yt-dlp`（公開貼文通常可以）；失敗就用 Claude in Chrome
     開連結讀貼文文字＋畫面（需使用者 Chrome 開著）
2. **抽出店家**：店名、類型、區域、一句話特色。日文店名保留原文
3. **查證正式店名**：WebSearch 對每家店確認日文正式店名（轉錄常是音譯，例如
   「安倍味」實為「めぐろの安兵衛」）；查不到就 `confirmed: false` 並在 note 註明待確認
4. **查重**：每家先跑 `python3 build_map.py --check 店名`（name 和 name_official 都查）；
   重複的跳過並告知使用者「已收錄過（哪支影片）」
5. **寫入**：新店 append 進 `places.json`（欄位照現有格式，added 用今天日期）
6. **重建**：`python3 build_map.py` → 檢查輸出無重複警告
7. **交付**：`git add foodmap && git commit && git push`（本 repo 慣例），
   Discord 通知新增了哪幾家（webhook 同 youtubetopdf pipeline），
   並把 map.html 用 SendUserFile 傳給使用者

## 注意

- 使用者要的是「已建過的不重複」——查重是硬規則，寧可多問不可重複
- 地區用「城市・區域」格式（例：東京・池袋），同區才會分在同一組
- map.html 是旅行時用手機開的，改版面要保持窄螢幕可用
