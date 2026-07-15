# 2027透明

SAKANAQUARIUM 2026-2027「透明」巡演相關場館資料整理：查證分級、座席示意標註，以及場內視角 YouTube 搜尋閱讀頁。

## GitHub Pages 閱讀頁

場內視角（POV）搜尋入口：

**https://\<username\>.github.io/\<repo\>/**

將 `<username>`、`<repo>` 換成你的 GitHub 帳號與 repository 名稱。啟用 Pages 後即可使用。

本地也可直接開啟產生後的 [`docs/index.md`](docs/index.md)。

## 啟用 GitHub Pages

推送本 repo 後：

1. 開啟 repository → **Settings** → **Pages**
2. **Source** 選 **Deploy from a branch**
3. Branch 選 `main`（或你的預設分支），資料夾選 **`/docs`**
4. 儲存後稍待建置完成，開啟上方的 Pages 網址

## 重新產生閱讀頁

場館資料改動後，執行：

```bash
python3 build_venue_youtube_search.py
```

會覆寫 [`docs/index.md`](docs/index.md)。場館來源為 [`annotate_seatmaps.py`](annotate_seatmaps.py) 的 `VENUES`。

## 主要文件

| 文件 | 說明 |
|------|------|
| [docs/index.md](docs/index.md) | 場內視角 YouTube 搜尋閱讀頁（Pages 首頁） |
| [venues_Dataset.md](venues_Dataset.md) | 場館資料可信度分級 |
| [sakanaction_2027_venue_factcheck.md](sakanaction_2027_venue_factcheck.md) | 查證報告 |
| [venue_research_backlog.md](venue_research_backlog.md) | 補查清單 |
| [annotated/README.md](annotated/README.md) | 標註圖使用限制 |

## 說明

- YouTube 粉絲／觀眾影片僅作**概略視野參考**，不可當作官方座席或容量規格。
- 標註圖中的 SS／S／A／B 人數屬歷史推估，詳見 [`annotated/README.md`](annotated/README.md)。
