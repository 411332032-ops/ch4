from foodbot.limits import RateLimiter
from foodbot.messages import MSG_FAILED, format_reply
from foodbot.models import Analysis, Ingredient


def test_rate_limit_per_user_with_sliding_window():
    now = [0.0]
    limiter = RateLimiter(max_per_hour=3, clock=lambda: now[0])
    assert [limiter.allow(1) for _ in range(4)] == [True, True, True, False]
    assert limiter.allow(2) is True  # 別人不受影響
    now[0] = 3601
    assert limiter.allow(1) is True  # 一小時後恢復


def test_failure_message_text():
    assert MSG_FAILED == "分析失敗，請再傳一次"


def test_food_reply_contains_everything_and_ends_with_daily_total():
    a = Analysis("food", "雞腿便當", "雞腿便當", [Ingredient("白飯", 200, 280), Ingredient("雞腿", 150, 320)])
    text = format_reply(a, 1540)
    for needle in ("雞腿便當", "白飯", "200 公克", "280 大卡", "雞腿", "350 公克", "600 大卡", "1,540 大卡", "僅供參考"):
        assert needle in text
    assert "你今天已攝取：1,540 大卡" in text


def test_not_food_reply_names_the_thing_and_still_shows_daily_total():
    text = format_reply(Analysis("not_food", "馬克杯", "馬克杯"), 800)
    assert "你傳的不是食物，是馬克杯" in text
    assert "800 大卡" in text
