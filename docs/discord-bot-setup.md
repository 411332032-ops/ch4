# Discord Bot 設定步驟

> 目標：在 Discord Developer Portal 建立 bot、打開 Message Content Intent、拿到 bot token、用最小權限把 bot 邀進你自己的 Server。
> 適用：**Windows**。全程在瀏覽器操作。
> 前置：先完成 [discord-server-setup.md](discord-server-setup.md)（你要先有 Server 和 `food-log` 頻道）。
> 提醒：Discord 偶爾會調整畫面，如果看到的名稱和這裡稍有不同，找意思最接近的。每個名稱都附了中文與英文。

名詞先說明：

- **Developer Portal（開發者後台）**：Discord 提供給開發者建立 bot 的網站。
- **Application（應用程式）**：你在後台建立的「專案」。bot 是這個專案裡的一個功能。
- **Bot token（機器人密鑰）**：bot 的密碼。程式拿著它才能以 bot 的身分登入 Discord。

---

## 🚨 先看這個：bot token 的規則

> **bot token 等於 bot 的密碼。誰拿到它，誰就能完全控制你的 bot（以它的名義發訊息、讀它看得到的所有訊息）。**
>
> ❌ **不能貼給任何人**（包含同學、朋友、老師、客服）
> ❌ **不能貼進這個對話**（包含貼給 Claude，對話內容可能被保存）
> ❌ **不能 commit 進 git**，也不能放到 GitHub
> ❌ **不能截圖**，也不能放進文件、聊天、貼文
> ✅ **只能存在你電腦上的 `.env` 檔裡**（這個檔已經被 `.gitignore` 擋住，git 不會追蹤它）
>
> **萬一外洩了怎麼辦**：立刻回到 Developer Portal → Bot → **Reset Token**（見第三節），舊的 token 馬上作廢。動作要快，不要等。

---

## 一、建立 Application 和 Bot

1. 用瀏覽器打開：`https://discord.com/developers/applications`
2. 如果要求登入，用你平常的 Discord 帳號登入。
3. 點右上角的藍色按鈕 **「New Application」**（新增應用程式）。
4. 在「Name」欄位輸入名稱，例如 `食物記錄 bot`。
5. 勾選同意條款（Developer Terms of Service 與 Developer Policy）。
6. 點 **「Create」**（建立）。

✅ **你應該看到**：進到這個 Application 的設定頁，左邊有選單（General Information、Installation、OAuth2、Bot…）。

> 每個 Application 建立時就自動有一個 bot，不用另外「新增 bot」。

---

## 二、打開 Message Content Intent（一定要做）

### 為什麼一定要打開

- Discord 把「**訊息內容**和**附件**」列為敏感資料，叫做 **Privileged Intent（特權權限）**，bot 要主動申請才拿得到。
- 這個 agent 的工作就是「**收到照片**」。如果沒打開，bot 看到的訊息會是空的、附件清單也是空的，它**根本不知道有人傳了照片**，也就不會有任何反應。
- 你的 Server 很小（遠少於 100 個 Server），打開這個開關不需要通過 Discord 的審核。

### 步驟

1. 在左邊選單點 **「Bot」**。
2. 往下捲到 **「Privileged Gateway Intents」** 區塊。
3. 找到 **「Message Content Intent」**，把右邊的開關**打開**（變成藍色）。
4. 其他兩個（Presence Intent、Server Members Intent）**維持關閉**，這個專案用不到。
5. 畫面下方會跳出一條提示「Careful — you have unsaved changes!」，點 **「Save Changes」**（儲存變更）。

✅ **你應該看到**：開關是藍色的，重新整理頁面後仍然是藍色（代表真的存好了）。

---

## 三、拿到 Bot Token

1. 仍在左邊選單的 **「Bot」** 頁面，往上看到 **「Token」** 區塊。
2. 點 **「Reset Token」**（重設密鑰）。
3. 跳出確認視窗，點 **「Yes, do it!」**。如果要求輸入密碼或兩步驟驗證碼，照做。
4. 畫面會顯示一串很長的字，旁邊有 **「Copy」**（複製）按鈕。**點 Copy。**

⚠️ **這串 token 只會顯示這一次。** 離開頁面就看不到了，只能再按一次 Reset Token 產生新的（舊的就作廢）。

5. **馬上**照下面「第六節」把它放進 `.env`。**不要貼到記事本以外的任何地方，也不要貼進對話。**

---

## 四、建議：關掉「Public Bot」

這樣別人就沒辦法把你的 bot 加進他們的 Server。

1. 在 **「Bot」** 頁面往下找到 **「Public Bot」**。
2. 把開關**關閉**（變成灰色）。
3. 點 **「Save Changes」**。

---

## 五、產生邀請連結，把 bot 邀進你的 Server

### 5-1. 選權限

1. 在左邊選單點 **「OAuth2」**。
2. 往下找到 **「OAuth2 URL Generator」** 區塊。
3. 在 **「Scopes」**（範圍）清單，只勾選 **`bot`**。其他（尤其 `applications.commands`）都不要勾。
4. 勾了 `bot` 之後，下面會出現 **「Bot Permissions」**（機器人權限）清單。**只勾這四個：**

| 要勾的權限 | 英文名稱 | 為什麼需要 |
|---|---|---|
| 檢視頻道 | View Channels | 才看得到 `food-log` 頻道和裡面的照片 |
| 傳送訊息 | Send Messages | 才能回「處理中」和結果 |
| 讀取訊息歷史 | Read Message History | 才能「回覆」某一則訊息 |
| 新增反應 | Add Reactions | 收到照片時，在那則訊息上加 ⏳ 表示排隊中 |

5. ❌ **絕對不要勾 `Administrator`（管理員）**，也不要多勾其他權限。權限給越少，萬一 bot 被騙或 token 外洩，能造成的傷害越小。
6. 如果頁面有 **「Integration Type」**（整合類型），選 **「Guild Install」**（安裝到伺服器）。

### 5-2. 邀進 Server

1. 捲到頁面最下方，**「Generated URL」** 欄位會出現一條網址。點旁邊的 **「Copy」** 複製。
2. 把網址貼到瀏覽器網址列，按 Enter。
3. 「新增至伺服器」／**Add to server** 下拉選單，選你剛建立的那個 Server。（如果下拉選單裡沒有你的 Server，代表你登入的帳號不是 Server 的擁有者。）
4. 點 **「繼續」／Continue**。
5. 確認畫面列出的權限就是上面那四個，沒有別的。點 **「授權」／Authorize**。
6. 若出現「我不是機器人」驗證，照做。

✅ **你應該看到**：「已授權」的畫面。回到 Discord，Server 右邊的成員清單多了你的 bot，標有 **「BOT」** 標籤，狀態是**離線**（灰色）。

> bot 離線是正常的。等你之後把程式跑起來，它才會變成綠色上線。

---

> 💡 如果你的 bot 已經邀進 Server 了，才發現漏勾 **新增反應**：重新做一次 5-1、5-2，勾好四個權限後再授權一次，權限就會更新，不用把 bot 踢掉。

---

## 六、把 token 和頻道編號放進 `.env`（只在你自己的電腦上）

### 6-1. 建立 `.env` 檔

1. 打開**記事本**（`Win` 鍵 → 輸入「記事本」→ Enter）。
2. 輸入下面四行，把括號裡的說明**換成你自己的值**（不要留括號）：

```
DISCORD_TOKEN=（貼上剛剛複製的 token）
CHANNEL_ID=（貼上 food-log 的頻道編號）
CLAUDE_MODEL=sonnet
DATA_DIR=C:\Users\user\food-data
```

   注意：
   - `=` 前後**不要有空格**。
   - 值**不用加引號**。
   - `DATA_DIR` 是存 Excel 和照片的資料夾，**放在專案資料夾之外**，這個資料夾可以先不存在，程式之後會建立。

3. 點左上角 **「檔案」→「另存新檔」**。
4. 儲存位置選你的專案資料夾：`C:\Users\user\ch4`。
5. **「存檔類型」**一定要改成 **「所有檔案 (*.*)」**。（沒改的話會存成 `.env.txt`，程式讀不到。）
6. **「檔案名稱」**輸入 `.env`（前面有一個點）。
7. 點 **「存檔」**。
8. 關掉記事本。**不要把內容留在其他地方。**

### 6-2. 確認 `.env` 沒有被 git 追蹤

1. 在專案資料夾空白處，按住 `Shift` 再按滑鼠右鍵，選 **「在此處開啟 PowerShell 視窗」**（或「在終端機中開啟」）。
2. 輸入下面這行，按 Enter：

```
git status
```

✅ **你應該看到**：畫面裡**沒有出現 `.env`** 這個檔名。（`.gitignore` 已經包含 `.env`，所以它被擋掉了。）

❌ **如果看到 `.env` 出現在清單裡**：**不要 commit**，先停下來，把畫面內容（不含 token）告訴我。

---

## 完成確認

- [ ] 我在 Developer Portal 建立了 Application
- [ ] **Message Content Intent 是打開的**，重新整理後仍是藍色
- [ ] 我複製了 token，並**只**放進本機的 `.env`
- [ ] 我關掉了 Public Bot
- [ ] 邀請連結只勾了 `bot` scope 和四個權限（View Channels、Send Messages、Read Message History、Add Reactions），**沒有勾 Administrator**
- [ ] bot 出現在我的 Server 成員清單，狀態是離線
- [ ] `.env` 裡有 `DISCORD_TOKEN`、`CHANNEL_ID`、`CLAUDE_MODEL`、`DATA_DIR` 四項
- [ ] `git status` 沒有顯示 `.env`
- [ ] 我**沒有**把 token 貼給任何人，也沒有貼進任何對話

## 如果 token 外洩了

不管是貼錯地方、截圖被看到、還是不小心 commit 了：

1. 立刻打開 `https://discord.com/developers/applications`，進入你的 Application → **Bot** → **Reset Token**。舊 token 馬上作廢。
2. 把新 token 更新到 `.env`。
3. 如果是 commit 進 git 的，光是刪檔不夠（歷史紀錄裡還在），**一律當作已經外洩**，以 Reset Token 為準。
