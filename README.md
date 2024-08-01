# DiscordBotTemplate

below is the english translation for the instructions

A cutting-edge Discord bot that's packed with features and commands to elevate your server experience. With this template, you can create a bot that's tailored to your community's unique needs.
## Installation

- Clone the repository:


```bash
git clone https://github.com/xireno/discord-bot-template.git

cd discordbot

npm install
```
### Prerequisites

- `Python 3.8` or higher, python 12+ is recommended
- `[En-us]ffmpeg` installed and added to your system's PATH                 https://ffmpeg.org/download.html

### settings

Create a file named .env to store your Discord bot token.

content should be `DISCORD_BOT_TOKEN=your_token_here`


## Usage

### Music Commands

- `!play [URL]`  - Plays a song from a YouTube or Spotify URL, or shows the current queue if no URL is provided.

- `!pause`  - Pauses the current song.

- `!resume`  - Resumes the paused song.

- `!skip`  - Skips the current song.

- `!stop`  - Stops the current song and clears the queue.

- `!leave`  - Leaves the voice channel and clears the queue.

- `!addlist [URL1, URL2, ...]`  - Adds multiple songs to the queue from a list of YouTube URLs.

### Moderation Commands
- `!mute [user]`  - Mutes a specific user.

- `!unmute [user]`  - Unmutes a specific user.

- `!unban [user]`  - Unbans a specific user from the server.

### Utility Commands
- `!help`  - Displays a list of all commands and their descriptions.

- `!ping`  - Checks the bot's response time to the Discord server.

- `!rs [file]`  - Restarts the bot's internal program. For example, !rs all restarts all files, or !rs music.py restarts the `music.py` file.

- `!roll [sides]`  - Rolls a dice with a specified number of sides.

- `!serverinfo`  - Provides information about the server.

- `!trsetting`  - Opens the translation select menu.

- `!trans [message]`  - Translates the message to the desired language.

- `!userinfo [user]`  - Provides information about a specific user.
# Discord 機器人 功能模板

以下是中文版翻譯

一款尖端的 Discord 機器人，包含豐富的功能和指令，可提升您的伺服器體驗。使用此模板，您可以創建適合您伺服器獨特需求的機器人。

## 安裝

- 複製存儲庫：

```bash
git clone https://github.com/xireno/discord-bot-template.git
cd discordbot
npm install
```

### 前置條件

* `Python 3.8` 或更高版本，Python 12+ 是建議使用的版本
* `[En-us]ffmpeg` 已經安裝到您的系統中，並添加到 PATH 中 https://ffmpeg.org/download.html

### 設定

創建一個名為 `.env` 的檔案，用於存儲 Discord 機器人的 Token。

內容如下： `DISCORD_BOT_TOKEN=your_token_here`

## 使用

### 音樂命令

- `!play [URL]`   - 從 YouTube 或 Spotify URL 播放歌曲，或者顯示當前等候列
如果沒有提供 URL。

- `!pause`   - 停止當前歌曲。

- `!resume`   - 繼續播放被停止的歌曲。

- `!skip`   - 跳過當前歌曲。

- `!stop`   - 停止當前歌曲並清除等候列。

- `!leave`   - 離開語頻頻頻 etc... 並清除等候列。

- `!addlist [URL1, URL2, ...]`   - 從多個 YouTube URL 列表中將多個歌曲添加到等候列。

### Management Commands
- `!mute [用戶]`    - 禁言指定用戶。 

- `!unmute [用戶]`    - 解除指定用戶的禁言狀態。

- `!unban [用戶]`    - 將指定用戶從伺服器中解除封禁。

### Utility Commands
- `!help`    - 顯示所有命令和描述。 

- `!ping`    - 檢查機器人的回應時間到 Discord 伺服器。 

- `!rs [檔案]`    - 重啟機器人的內部程式 例如 !rs all 重啟全部檔案 !rs `music.py` 等...方便更改程式

- `!roll [面]`    - 隨機滾動一個骰子具有指定的面數。 

- `!serverinfo`    - 顯示伺服器的信息。 

- `!trsetting`    - 開啟翻譯選擇選單。

- `!trans [訊息]`    - 對要翻譯的訊息進行翻譯。

- `!userinfo [用戶]`    - 顯示指定用戶的信息。





