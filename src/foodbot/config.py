"""設定：.env 裡的四項，加上寫死在這裡的各種上限。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# ---- 各種上限（不放進 .env，.env 只保留四項）----
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 單張照片上限 10 MB
MAX_IMAGE_SIDE = 2048  # 存檔與分析前，最長邊縮到這個像素以內
RATE_LIMIT_PER_HOUR = 20  # 每人每小時最多幾張
QUEUE_MAX = 50  # 排隊區上限
NOTE_MAX_CHARS = 200  # 上傳者附帶文字的長度上限
CLAUDE_TIMEOUT_SEC = 120  # 單次 claude -p 的時間上限
CLAUDE_MAX_BUDGET_USD = "0.50"  # 單次 claude -p 的花費上限
EXCEL_RETRIES = 5  # Excel 被鎖住時最多重試幾次
EXCEL_RETRY_DELAY_SEC = 3.0
CELL_MAX_CHARS = 2000  # Excel 單格長度上限

# ---- 分析結果的合理範圍 ----
MAX_WEIGHT_G = 5000
MAX_KCAL = 5000
MAX_ITEMS = 20
MAX_NAME_CHARS = 60

PHOTOS_DIRNAME = "photos"
RECORDS_FILENAME = "records.xlsx"


class ConfigError(Exception):
    """.env 缺項或格式不對。訊息會直接顯示給使用者，絕不可包含 token。"""


@dataclass(frozen=True)
class Settings:
    discord_token: str
    channel_id: int
    claude_model: str
    data_dir: Path

    @property
    def photos_dir(self) -> Path:
        return self.data_dir / PHOTOS_DIRNAME

    @property
    def records_path(self) -> Path:
        return self.data_dir / RECORDS_FILENAME

    def __repr__(self) -> str:  # 避免 token 被意外印出
        return (
            f"Settings(channel_id={self.channel_id}, claude_model={self.claude_model!r}, "
            f"data_dir={str(self.data_dir)!r}, discord_token=<hidden>)"
        )


def load_settings() -> Settings:
    load_dotenv(find_dotenv(usecwd=True) or find_dotenv())

    missing = [k for k in ("DISCORD_TOKEN", "CHANNEL_ID", "CLAUDE_MODEL", "DATA_DIR") if not os.getenv(k, "").strip()]
    if missing:
        raise ConfigError(f".env 缺少這些項目（或是空的）：{', '.join(missing)}")

    raw_channel = os.environ["CHANNEL_ID"].strip()
    if not raw_channel.isdigit():
        raise ConfigError("CHANNEL_ID 必須是純數字（頻道編號）")

    return Settings(
        discord_token=os.environ["DISCORD_TOKEN"].strip(),
        channel_id=int(raw_channel),
        claude_model=os.environ["CLAUDE_MODEL"].strip(),
        data_dir=Path(os.environ["DATA_DIR"].strip()).expanduser().resolve(),  # 一律轉成絕對路徑
    )
