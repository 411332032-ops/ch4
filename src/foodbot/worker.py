"""排隊區的處理員：一次只處理一張，串起 分析 → 檢查 → 建檔 → 回覆。

整張照片的處理都包在「出任何錯都接住」的保護裡：一張壞照片只會得到失敗訊息，
絕不會讓處理員（或整支 agent）停掉。
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

import discord

from .config import MAX_IMAGE_BYTES, QUEUE_MAX, Settings
from .messages import (
    MSG_BAD_IMAGE,
    MSG_FAILED,
    MSG_UNCLEAR,
    PROCESSING_EMOJI,
    format_reply,
)
from .models import VERDICT_UNCLEAR
from .parse_result import AnalysisError
from .pipeline import ImageError, analyze_with_retry, prepare_image, record_result
from .records import RecordBook, RecordError

log = logging.getLogger("foodbot.worker")


@dataclass(frozen=True)
class Job:
    message: discord.Message
    attachment: discord.Attachment
    note: str  # 上傳者附帶的文字（已截斷）。只當資料，見 analyzer.py 的防護 2


class Worker:
    def __init__(self, settings: Settings, book: RecordBook, bot_user: Callable[[], discord.abc.User | None]) -> None:
        self.settings = settings
        self.book = book
        self._bot_user = bot_user  # 呼叫後取得 bot 自己的 User（用來移除自己加的反應）
        self.queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=QUEUE_MAX)

    async def run(self) -> None:
        """永遠執行：從佇列取一張、處理一張。"""
        while True:
            job = await self.queue.get()
            try:
                await self.process(job)
            except Exception:  # 最外層保險
                log.exception("處理照片時發生未預期的錯誤")
            finally:
                self.queue.task_done()

    async def process(self, job: Job) -> None:
        message = job.message
        try:
            reply = await self._analyze_and_record(job)
        except ImageError as exc:
            log.warning("照片無法使用：%s", exc)
            reply = MSG_BAD_IMAGE
        except (AnalysisError, RecordError) as exc:
            log.warning("處理失敗：%s", exc)
            reply = MSG_FAILED
        except Exception:
            log.exception("處理失敗（未預期的錯誤）")
            reply = MSG_FAILED

        await self._reply(message, reply)
        await self._clear_reaction(message)

    async def _analyze_and_record(self, job: Job) -> str:
        data = await job.attachment.read()
        if len(data) > MAX_IMAGE_BYTES:
            raise ImageError("檔案超過大小上限")

        jpeg = await asyncio.to_thread(prepare_image, data)
        analysis = await analyze_with_retry(jpeg, job.note, self.settings)
        if analysis.verdict == VERDICT_UNCLEAR:
            return MSG_UNCLEAR

        author = job.message.author
        total = await asyncio.to_thread(
            record_result,
            self.settings,
            self.book,
            datetime.now(),  # 以這台電腦的本地時間為準
            author.display_name,
            author.id,
            analysis,
            jpeg,
        )
        return format_reply(analysis, total)

    @staticmethod
    async def _reply(message: discord.Message, text: str) -> None:
        try:
            await message.reply(text, mention_author=False, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException as exc:
            log.warning("回覆失敗：%s", exc)

    async def _clear_reaction(self, message: discord.Message) -> None:
        try:
            await message.remove_reaction(PROCESSING_EMOJI, self._bot_user())
        except discord.HTTPException as exc:
            log.warning("移除 %s 失敗：%s", PROCESSING_EMOJI, exc)
