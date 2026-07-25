"""
SeedPackagePackager —— 將 Seed Package 目錄 序列化 / 反序列化。

負責 walk 一個 Seed Package 目錄（P0 輸出格式：
manifest.json + entries/*.md + README.md）成 ordered (path, bytes) 列表，
同埋由列表重建目錄。
"""

from pathlib import Path
from typing import List, Tuple


class SeedPackagePackager:
    """Seed Package 目錄 ↔ (rel_path, bytes) 列表。"""

    # 唔打包呢啲（VCS / OS 雜物）
    IGNORE = {".DS_Store", "Thumbs.db", ".gitkeep", "__pycache__"}

    @staticmethod
    def serialize(package_dir: Path) -> List[Tuple[str, bytes]]:
        """
        Walk package_dir，回傳 [(相對路徑, 內容), ...]，
        按 rel_path 排序（令輸出 deterministic）。
        """
        package_dir = Path(package_dir)
        if not package_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {package_dir}")

        result: List[Tuple[str, bytes]] = []
        for path in sorted(package_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.name in SeedPackagePackager.IGNORE:
                continue
            rel = path.relative_to(package_dir).as_posix()  # 跨平台用 /
            result.append((rel, path.read_bytes()))
        return result

    @staticmethod
    def deserialize(files: List[Tuple[str, bytes]], out_dir: Path) -> Path:
        """
        由 (rel_path, bytes) 列表重建目錄結構到 out_dir。

        防 path traversal：只允許相對路徑，拒絕 .. 同絕對路徑。
        """
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for rel, content in files:
            # 安全：唔允許逃出 out_dir
            rel_path = Path(rel)
            if rel_path.is_absolute() or ".." in rel_path.parts:
                raise ValueError(f"Unsafe path in package: {rel}")
            target = out_dir / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        return out_dir
