"""測試用的假 claude：把收到的東西記下來，再依 FAKE_CLAUDE_MODE 回傳不同結果。"""

import json
import os
import sys
import time
from pathlib import Path

# 真正的 claude 輸出 UTF-8；Windows 上 Python 接管線時預設是 cp950，要明確指定
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

stdin_text = sys.stdin.buffer.read().decode("utf-8")
note_file = Path(os.getcwd()) / "note.txt"
log = {
    "argv": sys.argv[1:],
    "cwd": os.getcwd(),
    "stdin": stdin_text,
    "cwd_files": sorted(p.name for p in Path(os.getcwd()).iterdir()),
    "note_txt": note_file.read_text(encoding="utf-8") if note_file.exists() else None,
}
Path(os.environ["FAKE_CLAUDE_LOG"]).write_text(json.dumps(log, ensure_ascii=False), encoding="utf-8")

mode = os.environ.get("FAKE_CLAUDE_MODE", "ok")
GOOD = {
    "verdict": "food",
    "name": "雞腿便當",
    "short_name": "雞腿便當",
    "ingredients": [{"name": "白飯", "weight_g": 200, "kcal": 280}, {"name": "雞腿", "weight_g": 150, "kcal": 320}],
}
if mode == "ok":
    print(json.dumps({"is_error": False, "structured_output": GOOD}, ensure_ascii=False))
elif mode == "garbage":
    print("this is not json")
elif mode == "bad_number":
    bad = {**GOOD, "ingredients": [{"name": "飯", "weight_g": "很多", "kcal": 1}]}
    print(json.dumps({"is_error": False, "structured_output": bad}, ensure_ascii=False))
elif mode == "fail":
    print("boom", file=sys.stderr)
    sys.exit(3)
elif mode == "sleep":
    time.sleep(30)
