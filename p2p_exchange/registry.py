"""
本地 Seed Package 註冊表 —— p2p_registry.json。

記錄「呢個節點曾經 publish / pin 過邊啲 package」。
Append-only log 風格。

呢個 registry 係 P2.5（peer discovery）嘅 seam：
未來 libp2p pubsub 會 broadcast registry 嘅 entry 俾其他 peer 知。
而家 P2 淨係 local，但結構已經為去中心化準備好。
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


DEFAULT_REGISTRY_PATH = Path("p2p_registry.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_registry(path: Path = DEFAULT_REGISTRY_PATH) -> List[dict]:
    """載入 registry（唔存在就返空 list）。"""
    path = Path(path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_registry(entries: List[dict], path: Path = DEFAULT_REGISTRY_PATH) -> None:
    """覆寫整個 registry。"""
    path = Path(path)
    path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def add_entry(
    cid: str,
    package_name: str,
    contributor: str,
    source_path: str,
    path: Path = DEFAULT_REGISTRY_PATH,
) -> dict:
    """新增一筆 publish 記錄（CID 已存在就更新，唔重複）。"""
    entries = load_registry(path)
    # 移除同 CID 嘅舊記錄（re-publish 覆蓋）
    entries = [e for e in entries if e.get("cid") != cid]
    entry = {
        "cid": cid,
        "package_name": package_name,
        "contributor": contributor,
        "source_path": source_path,
        "published_at": _now_iso(),
    }
    entries.append(entry)
    save_registry(entries, path)
    return entry


def find_by_cid(cid: str, path: Path = DEFAULT_REGISTRY_PATH) -> Optional[dict]:
    """用 CID 搵 entry。"""
    for entry in load_registry(path):
        if entry.get("cid") == cid:
            return entry
    return None
