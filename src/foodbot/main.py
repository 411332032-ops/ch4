"""進入點：uv run foodbot"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import discord

from .config import ConfigError, load_settings
from .records import RecordError


def _setup_logging() -> None:
    # Windows 重新導向輸出時預設編碼可能不支援中文／emoji
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("logs/foodbot.log", encoding="utf-8")],
    )


def main() -> None:
    _setup_logging()
    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"設定有問題：{exc}")
        raise SystemExit(1)

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.photos_dir.mkdir(parents=True, exist_ok=True)

    from .bot import FoodBot  # 放在設定檢查之後，設定錯誤時能先看到清楚的訊息

    bot = FoodBot(settings)
    try:
        bot.run(settings.discord_token, log_handler=None)
    except discord.LoginFailure:
        print("登入失敗：DISCORD_TOKEN 不正確。請到 Developer Portal 的 Bot 頁面重新產生（Reset Token）並更新 .env。")
        raise SystemExit(1)
    except discord.PrivilegedIntentsRequired:
        print("請到 Developer Portal → Bot → 打開 Message Content Intent，存檔後再啟動。")
        raise SystemExit(1)
    except RecordError as exc:
        print(f"無法讀取紀錄檔：{exc}")
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("已停止。")


if __name__ == "__main__":
    main()
