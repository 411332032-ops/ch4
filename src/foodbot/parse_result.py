"""讀取並檢查 claude -p 的輸出。

原則：claude -p 的任何回答都不可信。每一步都檢查，任何一步出問題，
都只丟出 AnalysisError，由呼叫端決定重試或回覆「分析失敗」，絕不讓程式當掉。
"""

from __future__ import annotations

import json
import math
import re

from .config import MAX_ITEMS, MAX_KCAL, MAX_NAME_CHARS, MAX_WEIGHT_G
from .models import (
    VERDICT_FOOD,
    VERDICT_NOT_FOOD,
    VERDICT_UNCLEAR,
    Analysis,
    Ingredient,
)

_VERDICTS = {VERDICT_FOOD, VERDICT_NOT_FOOD, VERDICT_UNCLEAR}
_NUMBER_TEXT = re.compile(r"^\s*\d+(\.\d+)?\s*$")
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_CODE_FENCE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")


class AnalysisError(Exception):
    """分析結果無法使用（逾時、格式錯、數字不合理…）。"""


def parse_claude_output(stdout: str) -> Analysis:
    """claude -p --output-format json 的整段輸出 → 檢查過的 Analysis。"""
    return validate_payload(extract_payload(stdout))


def extract_payload(stdout: str) -> dict:
    """從 claude 的外層 JSON 取出模型給的答案（一個 dict）。"""
    try:
        outer = json.loads(stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        raise AnalysisError("claude 的輸出不是合法 JSON") from exc
    if not isinstance(outer, dict):
        raise AnalysisError("claude 的輸出不是 JSON 物件")
    if outer.get("is_error"):
        raise AnalysisError("claude 回報執行錯誤")

    structured = outer.get("structured_output")
    if isinstance(structured, dict):
        return structured

    # 退一步：試著把 result 這段文字當 JSON 讀（可能被包在 ``` 裡）
    result = outer.get("result")
    if isinstance(result, str) and result.strip():
        text = _CODE_FENCE.sub("", result.strip())
        try:
            inner = json.loads(text)
        except json.JSONDecodeError as exc:
            raise AnalysisError("答案不是合法 JSON") from exc
        if isinstance(inner, dict):
            return inner
    raise AnalysisError("找不到可用的答案")


def validate_payload(payload: dict) -> Analysis:
    verdict = payload.get("verdict")
    if verdict not in _VERDICTS:
        raise AnalysisError(f"verdict 不合法：{verdict!r}")

    if verdict == VERDICT_UNCLEAR:
        return Analysis(verdict=verdict, name="", short_name="")

    name = _clean_text(payload.get("name"))
    if not name:
        raise AnalysisError("缺少 name")
    short_name = _clean_text(payload.get("short_name")) or name

    if verdict == VERDICT_NOT_FOOD:
        return Analysis(verdict=verdict, name=name, short_name=short_name)

    raw_items = payload.get("ingredients")
    if not isinstance(raw_items, list) or not raw_items:
        raise AnalysisError("食物沒有任何成份")
    if len(raw_items) > MAX_ITEMS:
        raise AnalysisError("成份項數過多")

    items = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise AnalysisError("成份格式錯誤")
        item_name = _clean_text(raw.get("name"))
        if not item_name:
            raise AnalysisError("成份缺少名稱")
        items.append(
            Ingredient(
                name=item_name,
                weight_g=_to_number(raw.get("weight_g"), "weight_g", MAX_WEIGHT_G),
                kcal=_to_number(raw.get("kcal"), "kcal", MAX_KCAL),
            )
        )
    return Analysis(verdict=verdict, name=name, short_name=short_name, ingredients=items)


def _clean_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return _CONTROL_CHARS.sub("", value).strip()[:MAX_NAME_CHARS]


def _to_number(value: object, field_name: str, upper: float) -> float:
    """必須是真的數字（或純數字的文字），且在 0～upper 之間。"""
    if isinstance(value, bool):
        raise AnalysisError(f"{field_name} 不是數字")
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str) and _NUMBER_TEXT.match(value):
        number = float(value)
    else:
        raise AnalysisError(f"{field_name} 不是數字：{value!r}")
    if math.isnan(number) or math.isinf(number) or not 0 <= number <= upper:
        raise AnalysisError(f"{field_name} 超出合理範圍：{number}")
    return number
