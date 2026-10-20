"""一般防護（常駐，不在教學開關範圍）：限流。"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable

from .config import RATE_LIMIT_PER_HOUR


class RateLimiter:
    """每人每小時最多 N 張（滑動視窗，記在記憶體）。"""

    def __init__(
        self,
        max_per_hour: int = RATE_LIMIT_PER_HOUR,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max = max_per_hour
        self._clock = clock
        self._hits: dict[int, deque[float]] = defaultdict(deque)

    def allow(self, user_id: int) -> bool:
        """允許就記一次並回 True；超過上限回 False（不記）。"""
        now = self._clock()
        hits = self._hits[user_id]
        while hits and now - hits[0] >= 3600:
            hits.popleft()
        if len(hits) >= self._max:
            return False
        hits.append(now)
        return True
