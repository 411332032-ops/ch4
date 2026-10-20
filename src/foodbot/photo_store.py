"""存照片、決定檔名。

包含：
  防護 3：食物名稱當檔名前，先清掉會讓路徑亂跑的字

檔名格式：YYYY-MM-DD hh-mm-ss 食物名稱簡稱.jpg（用 - 不用冒號，Windows 才存得了）
同一秒撞名時，在簡稱後面加 -2、-3…，絕不覆蓋既有檔案。
"""

from __future__ import annotations

import itertools
import re
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path


# ----------------------------------------------------------------------------
# 沒有防護 3 時的預設：名稱原樣拿去當檔名，路徑也不檢查
# ----------------------------------------------------------------------------
def clean_name(raw: str) -> str:
    return raw


def ensure_inside(path: Path, root: Path) -> Path:
    return path


# ==== 防護 3：食物名稱清洗（路徑安全）　開始 ====
# 威脅：claude -p 回來的名稱（可能被騙，也可能亂寫）含有 / \ .. 冒號等字，
#       直接拿去當檔名，檔案可能被存到別的資料夾，或蓋掉別的檔案。
# 做法：移除不安全字元、擋掉 Windows 保留名稱、限制長度；
#       最後再確認完整路徑真的還在照片資料夾裡面。
_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
_UNSAFE_CHARS = re.compile(r'[\x00-\x1f\x7f\\/:*?"<>|]')
NAME_MAX_CHARS = 30


def clean_name(raw: str) -> str:  # noqa: F811
    name = _UNSAFE_CHARS.sub("", raw)
    while ".." in name:
        name = name.replace("..", "")
    name = name.strip(" .")  # Windows 會悄悄吃掉結尾的句點與空白
    if name.split(".")[0].upper() in _RESERVED_NAMES:
        name = f"_{name}"
    return name[:NAME_MAX_CHARS].strip(" .") or "未命名"


def ensure_inside(path: Path, root: Path) -> Path:  # noqa: F811
    resolved_root = root.resolve()
    if path.resolve().parent != resolved_root:
        raise ValueError(f"檔案路徑跑到照片資料夾外面了：{path}")
    return path
# ==== 防護 3 結束 ====


def _candidate_paths(photos_dir: Path, when: datetime, short_name: str) -> Iterator[Path]:
    stem = f"{when:%Y-%m-%d %H-%M-%S} {clean_name(short_name)}"
    yield ensure_inside(photos_dir / f"{stem}.jpg", photos_dir)
    for n in itertools.count(2):
        yield ensure_inside(photos_dir / f"{stem}-{n}.jpg", photos_dir)


def save_photo(photos_dir: Path, when: datetime, short_name: str, jpeg_bytes: bytes) -> Path:
    """存照片並回傳實際路徑。用「獨占建立」確保絕不覆蓋既有檔案。"""
    photos_dir.mkdir(parents=True, exist_ok=True)
    for path in _candidate_paths(photos_dir, when, short_name):
        try:
            with open(path, "xb") as f:
                f.write(jpeg_bytes)
        except FileExistsError:
            continue
        return path
    raise RuntimeError("unreachable")  # pragma: no cover
