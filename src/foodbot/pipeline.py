"""一張照片的處理步驟（不碰 Discord，方便單獨測試）。

流程：prepare_image（確認真的是圖片、轉成 JPEG）→ analyze_with_retry（claude -p，失敗重試一次）
      → record_result（存照片＋寫 Excel）
"""

from __future__ import annotations

import io
import logging
import os
from datetime import datetime

from PIL import Image, ImageOps

from .analyzer import run_claude
from .config import MAX_IMAGE_SIDE, Settings
from .models import Analysis
from .parse_result import AnalysisError, parse_claude_output
from .photo_store import save_photo
from .records import RecordBook, Row

log = logging.getLogger("foodbot.pipeline")

NOT_FOOD_LABEL = "不是食物"


class ImageError(Exception):
    """照片打不開、損毀，或不是支援的圖片。"""


def prepare_image(data: bytes) -> bytes:
    """用 Pillow 實際解碼（不信副檔名），轉成 JPEG，最長邊縮到上限內。

    重新編碼還有一個好處：EXIF（GPS 位置等）會被去掉。
    """
    try:
        with Image.open(io.BytesIO(data)) as opened:
            opened.load()
            image = ImageOps.exif_transpose(opened)
            if image.mode in ("RGBA", "LA", "P"):
                rgba = image.convert("RGBA")
                flat = Image.new("RGB", rgba.size, "white")
                flat.paste(rgba, mask=rgba.split()[3])
                image = flat
            else:
                image = image.convert("RGB")
            image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
            out = io.BytesIO()
            image.save(out, "JPEG", quality=90)
            return out.getvalue()
    except Exception as exc:  # Pillow 對壞檔可能丟各種例外
        raise ImageError(f"無法解碼圖片：{exc}") from exc


async def analyze_with_retry(jpeg: bytes, note: str, settings: Settings, attempts: int = 2) -> Analysis:
    """呼叫 claude -p 並檢查結果；失敗時重試（共 attempts 次）。看不清楚（unclear）不重試。"""
    last: AnalysisError | None = None
    for n in range(1, attempts + 1):
        raw = ""
        try:
            raw = await run_claude(jpeg, note, settings)
            return parse_claude_output(raw)
        except AnalysisError as exc:
            last = exc
            log.warning("分析失敗（第 %d/%d 次）：%s | 原始輸出前 300 字：%r", n, attempts, exc, raw[:300])
    assert last is not None
    raise last


def record_result(
    settings: Settings,
    book: RecordBook,
    now: datetime,
    uploader_name: str,
    uploader_id: int,
    analysis: Analysis,
    jpeg: bytes,
) -> float:
    """存照片＋在 Excel 加一列，回傳該使用者當日（含這一餐）熱量總數。

    Excel 寫入失敗時，把剛存的照片刪掉，保持「失敗就不留任何痕跡」。
    """
    photo_path = save_photo(settings.photos_dir, now, analysis.short_name, jpeg)
    try:
        rel = os.path.relpath(photo_path, settings.data_dir).replace(os.sep, "/")
    except ValueError:
        rel = str(photo_path)

    if analysis.is_food:
        row = Row(
            when=now,
            uploader_name=uploader_name,
            uploader_id=uploader_id,
            description=analysis.name,
            ingredients="；".join(
                f"{i.name} {round(i.weight_g)}公克/{round(i.kcal)}大卡" for i in analysis.ingredients
            ),
            weight_g=analysis.total_weight_g,
            kcal=analysis.total_kcal,
            photo_rel_path=rel,
        )
    else:
        row = Row(
            when=now,
            uploader_name=uploader_name,
            uploader_id=uploader_id,
            description=NOT_FOOD_LABEL,
            ingredients=analysis.name,
            weight_g=None,
            kcal=None,
            photo_rel_path=rel,
        )

    try:
        return book.append(row)
    except Exception:
        photo_path.unlink(missing_ok=True)
        raise
