# Syncnext Control

讓本地 Agent 使用 Syncnext 的搜尋、來源品質探測、選集、播放、關閉播放及播放狀態 API。

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

API 操作預設會顯示 App 通知，可在同一區塊關閉「顯示 Agent 操作通知」。

## 使用

安裝與設定完成後，可以直接對 Agent 說：

> 使用 Syncnext 搜尋「反黑先鋒」，比較可用來源的實際品質，播放第一集，並確認播放狀態。

Agent 應依 [SKILL.md](SKILL.md) 比對作品與集數，以實際探測結果選擇來源。需要換片時，先關閉目前播放器，再播放新的分集。探測資料不完整時，保留未知狀態。

完整路由、限制與 client 選項見 [HTTP API](references/http-api.md)。

## 維護

公開發佈位置為 [qoli/syncnext-control](https://github.com/qoli/syncnext-control)。Syncnext App 倉庫內的 `Skills/syncnext-control` 保留同一套檔案供整合驗收；修改 API 或 Skill 時，應同步這份快照。
