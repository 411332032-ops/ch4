"""資料結構。"""

from __future__ import annotations

from dataclasses import dataclass, field

VERDICT_FOOD = "food"
VERDICT_NOT_FOOD = "not_food"
VERDICT_UNCLEAR = "unclear"


@dataclass(frozen=True)
class Ingredient:
    name: str
    weight_g: float
    kcal: float


@dataclass(frozen=True)
class Analysis:
    verdict: str
    name: str
    short_name: str
    ingredients: list[Ingredient] = field(default_factory=list)

    @property
    def is_food(self) -> bool:
        return self.verdict == VERDICT_FOOD

    # 整餐的重量與熱量由程式加總，不讓模型自己算（避免各項與合計對不上）
    @property
    def total_weight_g(self) -> float:
        return sum(i.weight_g for i in self.ingredients)

    @property
    def total_kcal(self) -> float:
        return sum(i.kcal for i in self.ingredients)
