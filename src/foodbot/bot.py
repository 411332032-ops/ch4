"""Discord 事件：上線公告、收訊息、一般檢查、加 ⏳ 反應、入列。

這裡只做「快的事」。真正慢的分析交給 worker.py 的佇列，一次處理一張。
一般防護（常駐）：只聽 CHANNEL_ID、忽略機器人、只收圖片、大小與格式檢查、限流、不 @ 任何人。
"""

from __future__ import annotations

import asyncio
import logging

import discord

from .config import MAX_IMAGE_BYTES, NOTE_MAX_CHARS, Settings
from .limits import RateLimiter
from .messages import MSG_BAD_IMAGE, MSG_BUSY, MSG_ONLINE, MSG_TOO_FAST, PROCESSING_EMOJI
from .records import RecordBook
from .worker import Job, Worker

log = logging.getLogger("foodbot.bot")

SUPPORTED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif", ".bmp", ".tif", ".tiff", ".svg")


def _looks_like_image(attachment: discord.Attachment) -> bool:
    content_type = (attachment.content_type or "").split(";")[0].strip().lower()
    if content_type:
        return content_type.startswith("image/")
    return attachment.filename.lower().endswith(IMAGE_SUFFIXES)


def _supported(attachment: discord.Attachment) -> bool:
    content_type = (attachment.content_type or "").split(";")[0].strip().lower()
    if content_type:
        return content_type in SUPPORTED_TYPES
    return attachment.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))


class FoodBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True  # 需要在 Developer Portal 也打開，否則讀不到附件
        super().__init__(intents=intents, allowed_mentions=discord.AllowedMentions.none())
        self.settings = settings
        self.book = RecordBook(settings.records_path)
        self.limiter = RateLimiter()
        self.worker = Worker(settings, self.book, bot_user=lambda: self.user)
        self._announced = False
        self._worker_task: asyncio.Task | None = None

    async def setup_hook(self) -> None:
        await asyncio.to_thread(self.book.load_totals)  # 從 Excel 重建每人當日熱量
        self._worker_task = asyncio.create_task(self.worker.run())

    async def on_ready(self) -> None:
        log.info("已登入：%s，只聽頻道 %s", self.user, self.settings.channel_id)
        if self._announced:  # on_ready 在重新連線時會再觸發，公告只發一次
            return
        self._announced = True
        channel = self.get_channel(self.settings.channel_id)
        if channel is None:
            log.error("找不到頻道 %s：請確認 CHANNEL_ID 正確，且 bot 已在該 Server 並看得到此頻道", self.settings.channel_id)
            return
        try:
            await channel.send(MSG_ONLINE)
        except discord.HTTPException as exc:
            log.warning("上線公告發送失敗：%s", exc)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.channel.id != self.settings.channel_id:
            return
        images = [a for a in message.attachments if _looks_like_image(a)]
        if not images:
            return  # 純文字、非圖片附件：完全不回應

        note = (message.content or "").strip()[:NOTE_MAX_CHARS]
        for attachment in images:
            await self._enqueue(message, attachment, note)

    async def _enqueue(self, message: discord.Message, attachment: discord.Attachment, note: str) -> None:
        if not _supported(attachment) or attachment.size > MAX_IMAGE_BYTES:
            await self._say(message, MSG_BAD_IMAGE)
            return
        if not self.limiter.allow(message.author.id):
            await self._say(message, MSG_TOO_FAST)
            return
        if self.worker.queue.full():
            await self._say(message, MSG_BUSY)
            return

        try:
            await message.add_reaction(PROCESSING_EMOJI)
        except discord.HTTPException as exc:  # 多半是 bot 缺少「新增反應」權限
            log.warning("加 %s 反應失敗（bot 是否有 Add Reactions 權限？）：%s", PROCESSING_EMOJI, exc)
        self.worker.queue.put_nowait(Job(message=message, attachment=attachment, note=note))

    @staticmethod
    async def _say(message: discord.Message, text: str) -> None:
        try:
            await message.reply(text, mention_author=False)
        except discord.HTTPException as exc:
            log.warning("回覆失敗：%s", exc)
