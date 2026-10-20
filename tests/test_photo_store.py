"""防護 3：食物名稱當檔名前先清洗；以及撞名處理。"""

from datetime import datetime
from pathlib import Path

import pytest

from foodbot import photo_store
from foodbot.photo_store import clean_name, save_photo

WHEN = datetime(2026, 10, 20, 12, 34, 56)


@pytest.mark.parametrize(
    "raw",
    ["../../evil", "..\\..\\evil", "a/b", "a\\b", "a:b", "C:\\Windows", "....", "...", "name.", " name ", "a*b?c", 'a"b<c>d|e', "line1\nline2"],
)
def test_clean_name_never_produces_path_tricks(raw):
    cleaned = clean_name(raw)
    assert cleaned
    assert not set(cleaned) & set('\\/:*?"<>|\n')
    assert ".." not in cleaned
    assert cleaned == cleaned.strip(" .")


@pytest.mark.parametrize("raw", ["CON", "nul", "com1", "LPT9", "con.txt"])
def test_reserved_names_are_neutralized(raw):
    assert clean_name(raw).split(".")[0].upper() not in {"CON", "NUL", "COM1", "LPT9"}


def test_empty_or_too_long_names():
    assert clean_name("") == "未命名"
    assert clean_name("///") == "未命名"
    assert len(clean_name("字" * 100)) <= 30


def test_saved_file_name_format(tmp_path):
    path = save_photo(tmp_path, WHEN, "雞腿便當", b"jpg")
    assert path.name == "2026-10-20 12-34-56 雞腿便當.jpg"
    assert path.read_bytes() == b"jpg"


def test_same_second_collisions_get_suffix_and_never_overwrite(tmp_path):
    p1 = save_photo(tmp_path, WHEN, "便當", b"1")
    p2 = save_photo(tmp_path, WHEN, "便當", b"2")
    p3 = save_photo(tmp_path, WHEN, "便當", b"3")
    assert [p.name for p in (p1, p2, p3)] == [
        "2026-10-20 12-34-56 便當.jpg",
        "2026-10-20 12-34-56 便當-2.jpg",
        "2026-10-20 12-34-56 便當-3.jpg",
    ]
    assert [p.read_bytes() for p in (p1, p2, p3)] == [b"1", b"2", b"3"]


def test_malicious_name_cannot_escape_photos_dir(tmp_path):
    photos = tmp_path / "photos"
    secret = tmp_path / "secret.txt"
    secret.write_text("keep me")
    path = save_photo(photos, WHEN, "../secret.txt", b"x")
    assert path.parent == photos
    assert secret.read_text() == "keep me"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["photos", "secret.txt"]


def test_ensure_inside_rejects_outside_path(tmp_path):
    with pytest.raises(ValueError):
        photo_store.ensure_inside(tmp_path.parent / "x.jpg", tmp_path)
