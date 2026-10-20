"""所有要回給使用者的文字，集中在這裡。"""

from __future__ import annotations

from .models import Analysis

PROCESSING_EMOJI = "⏳"

MSG_FAILED = "分析失敗，請再傳一次"
MSG_UNCLEAR = "照片看不清楚，請重傳。"
MSG_BAD_IMAGE = "照片太大或格式不支援。"
MSG_TOO_FAST = "你傳太快了，請稍後再試。"
MSG_BUSY = "目前太忙，請稍後再試。"

MSG_ONLINE = (
    "食物記錄 bot 上線了 🍽️ 傳食物照片到這裡，我會估算熱量並記錄。\n"
    "**傳到這個頻道的照片都會被存下來**，請不要傳食物以外的私人照片。"
)


def _num(value: float) -> str:
    return f"{round(value):,}"


def format_reply(analysis: Analysis, today_total_kcal: float) -> str:
    today = f"你今天已攝取：{_num(today_total_kcal)} 大卡"
    if not analysis.is_food:
        return f"你傳的不是食物，是{analysis.name}。\n{today}"

    lines = [f"✅ 這是食物：{analysis.name}"]
    for item in analysis.ingredients:
        lines.append(f"• {item.name}　約 {_num(item.weight_g)} 公克　約 {_num(item.kcal)} 大卡")
    lines.append(f"這餐合計：約 {_num(analysis.total_weight_g)} 公克，約 {_num(analysis.total_kcal)} 大卡")
    lines.append(today)
    lines.append("（以上為 AI 依照片估算，僅供參考）")
    return "\n".join(lines)
