# ch4 — 食物照片記錄 Agent

一個在自己電腦上執行的 Discord bot：指定頻道有人傳食物照片，就用 `claude -p` 估熱量、記進 Excel、存照片，並回覆上傳者與其「當日已攝取熱量」。

- 需求：[docs/requirements.md](docs/requirements.md)
- 設計：[docs/architecture.md](docs/architecture.md)
- Discord 設定：[docs/discord-server-setup.md](docs/discord-server-setup.md)、[docs/discord-bot-setup.md](docs/discord-bot-setup.md)

## 啟動

```
uv run foodbot
```

（等同 `uv run python -m foodbot`。按 `Ctrl+C` 停止。agent 關掉期間傳的照片不會被處理。）

第一次使用前：

1. 照 `docs/discord-bot-setup.md` 建立 bot、打開 **Message Content Intent**、邀進 Server（權限要有 View Channels、Send Messages、Read Message History、**Add Reactions**）。
2. 複製 `.env.example` 成 `.env`，填入四項：`DISCORD_TOKEN`、`CHANNEL_ID`、`CLAUDE_MODEL`、`DATA_DIR`。
3. 確認 `claude` 指令可用（已登入 Claude Code）。

`.env` 與 `DATA_DIR`（照片、`records.xlsx`）、`logs/` 都已列在 `.gitignore`，**不可 commit**。`DISCORD_TOKEN` 絕不能貼給任何人。

## 測試

```
uv run pytest
```

## 四段防護在哪裡

每段都用 `# ==== 防護 N：… 開始 ====` 到 `# ==== 防護 N 結束 ====` 框起來。行號會隨修改偏移，**用搜尋 `==== 防護` 一定找得到**。

| 防護 | 檔案 | 約在第幾行 | 擋什麼 |
|---|---|---|---|
| 1 | `src/foodbot/analyzer.py` | 80–90 | `claude -p` 的檔案範圍隔離：只能碰到「只有這一張待分析照片」的暫存資料夾 |
| 2 | `src/foodbot/analyzer.py` | 103–123 | 上傳者打的字只當資料（存成 `note.txt`），不接進給 `claude -p` 的指令 |
| 3 | `src/foodbot/photo_store.py` | 30–55 | 食物名稱當檔名前，清掉 `/ \ .. :` 等會讓路徑亂跑的字 |
| 4 | `src/foodbot/records.py` | 50–59 | 寫進 Excel 的文字若以 `= + - @` 開頭，處理成純文字 |

**一開始四段全部開啟。** 每段的做法是：沒有防護時的預設行為寫在段落外面，段落裡用同名函式覆蓋成有防護的版本。所以把整段註解掉，程式照常運作，只是少了那層保護（也就是上課要對照的「防護關閉」版本）。

## 資料夾

```
src/foodbot/
  main.py          進入點
  config.py        .env 與各種上限
  bot.py           Discord 事件：上線公告、收訊息、⏳ 反應、入列、一般檢查
  worker.py        排隊區的處理員（一次一張）、回覆
  pipeline.py      圖片檢查、分析重試、存檔
  analyzer.py      呼叫 claude -p（防護 1、2）
  parse_result.py  檢查 claude -p 的 JSON
  photo_store.py   存照片、檔名（防護 3）
  records.py       Excel 紀錄、當日熱量（防護 4）
  limits.py        限流
  messages.py      所有回給使用者的文字
tests/             自動測試
```
