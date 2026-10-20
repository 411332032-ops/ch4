"""claude -p 的輸出不可信：每一種壞資料都只能得到 AnalysisError，不能當掉。"""

import json

import pytest

from foodbot.parse_result import AnalysisError, parse_claude_output


def outer(**fields) -> str:
    return json.dumps({"is_error": False, **fields}, ensure_ascii=False)


GOOD = {
    "verdict": "food",
    "name": "雞腿便當",
    "short_name": "雞腿便當",
    "ingredients": [
        {"name": "白飯", "weight_g": 200, "kcal": 280},
        {"name": "雞腿", "weight_g": 150, "kcal": 320},
    ],
}


def test_good_structured_output():
    a = parse_claude_output(outer(structured_output=GOOD))
    assert a.is_food
    assert a.total_kcal == 600  # 合計由程式加總
    assert a.total_weight_g == 350


def test_result_text_with_code_fence_is_accepted():
    text = "```json\n" + json.dumps(GOOD, ensure_ascii=False) + "\n```"
    assert parse_claude_output(outer(result=text)).name == "雞腿便當"


def test_numbers_as_plain_numeric_text_are_accepted():
    bad = {**GOOD, "ingredients": [{"name": "飯", "weight_g": "200", "kcal": "280.5"}]}
    assert parse_claude_output(outer(structured_output=bad)).total_kcal == 280.5


def test_not_food_needs_only_a_name():
    a = parse_claude_output(outer(structured_output={"verdict": "not_food", "name": "馬克杯", "short_name": "馬克杯", "ingredients": []}))
    assert not a.is_food and a.name == "馬克杯"


def test_unclear():
    a = parse_claude_output(outer(structured_output={"verdict": "unclear", "name": "", "short_name": "", "ingredients": []}))
    assert a.verdict == "unclear"


@pytest.mark.parametrize(
    "stdout",
    [
        "",  # 空
        "not json at all",
        "[1, 2, 3]",  # 合法 JSON 但不是物件
        json.dumps({"is_error": True, "result": "boom"}),
        outer(result="這不是 JSON"),
        outer(result="```json\n{壞掉\n```"),
        outer(),  # 什麼答案都沒有
        outer(structured_output={"verdict": "maybe", "name": "x", "short_name": "x", "ingredients": []}),
        outer(structured_output={"verdict": "food", "name": "", "short_name": "x", "ingredients": [{"name": "a", "weight_g": 1, "kcal": 1}]}),
        outer(structured_output={"verdict": "food", "name": "x", "short_name": "x", "ingredients": []}),  # 食物沒成份
        outer(structured_output={"verdict": "food", "name": "x", "short_name": "x"}),  # 缺 ingredients
    ],
)
def test_bad_outputs_raise_analysis_error(stdout):
    with pytest.raises(AnalysisError):
        parse_claude_output(stdout)


@pytest.mark.parametrize(
    "bad_item",
    [
        {"name": "飯", "weight_g": "約200克", "kcal": 280},  # 重量不是數字
        {"name": "飯", "weight_g": 200, "kcal": None},
        {"name": "飯", "weight_g": 200, "kcal": ""},
        {"name": "飯", "weight_g": True, "kcal": 1},
        {"name": "飯", "weight_g": [200], "kcal": 1},
        {"name": "飯", "weight_g": 200, "kcal": -50},
        {"name": "飯", "weight_g": 200, "kcal": 99999},
        {"name": "飯", "weight_g": float("nan"), "kcal": 1},
        {"name": "飯", "weight_g": float("inf"), "kcal": 1},
        {"name": "", "weight_g": 1, "kcal": 1},
        {"weight_g": 1, "kcal": 1},
        "不是物件",
    ],
)
def test_bad_numbers_and_items_raise(bad_item):
    payload = {**GOOD, "ingredients": [bad_item]}
    stdout = '{"structured_output": ' + json.dumps(payload, ensure_ascii=False) + "}"  # allow_nan 會輸出 NaN
    with pytest.raises(AnalysisError):
        parse_claude_output(stdout)


def test_too_many_items():
    many = [{"name": f"x{i}", "weight_g": 1, "kcal": 1} for i in range(21)]
    with pytest.raises(AnalysisError):
        parse_claude_output(outer(structured_output={**GOOD, "ingredients": many}))


def test_control_characters_are_stripped_from_names():
    payload = {**GOOD, "name": "雞腿\n便當\x00"}
    assert parse_claude_output(outer(structured_output=payload)).name == "雞腿便當"
