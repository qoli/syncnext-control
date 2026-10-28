# Syncnext Control

讓本地 Agent 使用 Syncnext 的播放歷史、當前媒體的音樂識別結果、搜尋、打開播放列表、來源品質探測、選集、播放、關閉播放及播放狀態 API。

需要支援無令牌本地 HTTP API v1 的 Syncnext，以及 Python 3.10 以上版本；client 只使用 Python 標準庫。

## 安裝

將這個倉庫下載或 clone 到你所使用 Agent 的技能目錄，保留完整目錄結構，讓 Agent 能讀取根目錄的 `SKILL.md`。

以使用 `~/.agents/skills` 的 Agent 為例：

```bash
git clone https://github.com/qoli/syncnext-control.git ~/.agents/skills/syncnext-control
```

若目錄已存在且是這個倉庫的 clone，依下節更新即可。其他 Agent 請使用其支援的技能目錄或匯入方式。

## 更新

```bash
git -C ~/.agents/skills/syncnext-control pull --ff-only
```

以下載方式安裝時，下載最新版並替換這個 Skill 目錄。Skill 獨立於 App 更新；新的 API 能力仍需要相應的 Syncnext 版本。

## 連接 Syncnext

1. 讓 Syncnext 保持在前景，開啟「設定 → 網絡 → 本地 Agent API → 允許本地 Agent」。
2. 「安裝 Agent Skill」會顯示 QR Code；掃描後，可複製帶有這台裝置 HTTP 地址的安裝提示詞，交給 Agent。
3. 也可以手動設定環境變數後執行 client：

```bash
export SYNCNEXT_URL='http://192.168.1.20:11330'
python3 ~/.agents/skills/syncnext-control/scripts/syncnext.py status
```

不需要 API 令牌。Agent 必須能連接顯示的 HTTP 地址；`127.0.0.1` 指向 Agent 自己所在的主機。

任務開始及結束時預設會顯示 App 通知，讀取狀態與任務進度輪詢不會彈出通知；可在同一區塊關閉「顯示 Agent 操作通知」。

## 使用

安裝與設定完成後，可以直接對 Agent 說：

> 使用 Syncnext 搜尋「反黑先鋒」，比較可用來源的實際品質，播放第一集，並確認播放狀態。

Agent 應依 [SKILL.md](SKILL.md) 比對作品與集數，以實際探測結果選擇來源。需要換片時，先關閉目前播放器，再播放新的分集。探測資料不完整時，保留未知狀態。

完整路由、限制與 client 選項見 [HTTP API](references/http-api.md)。

在電視上打開搜尋結果的播放列表：

```bash
python3 scripts/syncnext.py open-playlist ITEM_ID
```

`ITEM_ID` 使用本次 App 搜尋結果的 ID；這會打開原有播放列表頁，讓你自行選集，不會開始播放。若正在播放，先執行 `stop`。需要 App 的 `status.capabilities` 包含 `openPlaylist`。

讀取播放歷史：

```bash
python3 scripts/syncnext.py history
python3 scripts/syncnext.py history --page 2
python3 scripts/syncnext.py activities
python3 scripts/syncnext.py activities --page 2
```

每頁固定最多 1000 筆，從第 1 頁開始；依回應的 `nextPage` 繼續讀取，直到 `null`。
紀錄保存的是續播位置，不能把播放位置當作實際觀看時長，或把紀錄筆數當作觀看次數。

讀取當前媒體保留的音樂識別結果：

```bash
python3 scripts/syncnext.py music
```

需要 `status.capabilities` 包含 `musicRecognition`。回傳 `songs`，最多 5 首、最新在前，
包含 `id`、`title`、`artist` 與可為 `null` 的 `artworkURL`。
第一首代表最近一次確認，不能當作此刻仍在播放的歌曲。沒有播放器或尚無結果時回傳空陣列。
暫停、seek、停用辨識保留結果；退出或換片清除。

## 維護

公開發佈位置為 [qoli/syncnext-control](https://github.com/qoli/syncnext-control)。Syncnext App 倉庫內的 `Skills/syncnext-control` 是發佈來源；修改 API 時，在同一變更中更新這份 Skill 與 client。

App 的 Fastlane `ios release` 與 `ios test` 會在 IPA 驗證完成、上傳前執行 `Scripts/publish_syncnext_skill.py`。腳本複製來源中 Git 追蹤的檔案，以候選副本執行 client HTTP 測試，通過後同步到相鄰的 `SyncnextSkill` checkout，使用固定訊息 `🔄 chore(skill): sync from Syncnext <App HEAD>` 建立 commit，再 push 到該 checkout 目前分支的 upstream。測試或 push 失敗會停止 lane。

也可在 **Syncnext App 倉庫根目錄**單獨執行發佈：

```bash
python3 Scripts/publish_syncnext_skill.py
# 目標 checkout 不在相鄰目錄時：
python3 Scripts/publish_syncnext_skill.py --repository /path/to/syncnext-control
```

目標必須是已設定 upstream 且工作樹乾淨的 Git checkout。內容相同時不建立新 commit；前次 push 失敗時，重跑會補推既有 commit。腳本不切換分支或拉取遠端變更；遇到分歧時，先處理 checkout 再重新發佈。
