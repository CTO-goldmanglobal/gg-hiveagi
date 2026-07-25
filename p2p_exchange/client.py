"""
P2PClient —— 抽象 + Mock + Kubo 實作。

Replicates P1 嘅 LLMClient 模式：
    ABC 介面統一，Mock 令 pipeline 喺零安裝下可測，
    Kubo 係 canonical real impl（真正去中心化，唔靠第三方）。

Canonical real = kubo (local IPFS daemon) —— 符合 project 嘅
「decentralized knowledge symbiosis」願景，無 vendor lock-in。
Pinning service（Pinata 等）係可選嘅未來 impl，畀跑唔到 daemon 嘅貢獻者用。
"""

import json
import os
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple

from .cid import compute_mock_cid, looks_like_mock_cid
from .package import SeedPackagePackager


class P2PClient(ABC):
    """抽象 P2P / content-addressing client。"""

    @abstractmethod
    def publish(self, files: List[Tuple[str, bytes]]) -> str:
        """發佈 package，回傳 CID。"""
        raise NotImplementedError

    @abstractmethod
    def resolve(self, cid: str) -> List[Tuple[str, bytes]]:
        """用 CID 拉 package，回傳 [(rel_path, content), ...]。"""
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """呢個 backend 而家係咪可用（例如 kubo daemon 有冇行緊）。"""
        raise NotImplementedError


# ===== Mock: 本地檔案系統模擬 CID =====
class MockP2PClient(P2PClient):
    """
    Mock —— 用本地檔案系統模擬 content addressing。

    Publish：計 mock CID，將 serialized files 存去 ~/.hiveagi_mock_store/<cid>.json
    Resolve：用 CID 讀返
    CID 係 content-derived（sha256），所以同一內容永遠同一 CID。

    零安裝，全 pipeline 可測。
    """

    def __init__(self, store_dir: Path = None):
        self.store_dir = Path(store_dir or os.path.expanduser("~/.hiveagi_mock_store"))
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def publish(self, files: List[Tuple[str, bytes]]) -> str:
        cid = compute_mock_cid(files)
        store_path = self.store_dir / f"{cid}.json"
        # 存做 [{path, content_b64}, ...]
        import base64
        payload = [
            {"path": p, "content_b64": base64.b64encode(c).decode("ascii")}
            for p, c in files
        ]
        store_path.write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
        return cid

    def resolve(self, cid: str) -> List[Tuple[str, bytes]]:
        if not looks_like_mock_cid(cid):
            raise ValueError(
                f"MockP2PClient can only resolve mock CIDs (mockbafy...), got: {cid}"
            )
        store_path = self.store_dir / f"{cid}.json"
        if not store_path.exists():
            raise FileNotFoundError(
                f"Mock store has no such CID: {cid} (maybe not published yet, or on a different node)"
            )
        import base64
        payload = json.loads(store_path.read_text(encoding="utf-8"))
        return [
            (item["path"], base64.b64decode(item["content_b64"]))
            for item in payload
        ]

    def is_available(self) -> bool:
        return True  # 本地 FS 永遠 available


# ===== Kubo: 真 IPFS daemon（canonical real impl）=====
class KuboP2PClient(P2PClient):
    """
    Kubo（go-ipfs） daemon client，經 HTTP API。

    預設 endpoint: http://127.0.0.1:5001/api/v0
    用 stdlib urllib —— 唔引入 requests 依賴。

    用法前提：用戶已安裝並啟動 kubo daemon（`ipfs daemon`）。
    安裝見 README。
    """

    def __init__(self, api_url: str = None):
        self.api_url = (api_url or os.getenv("IPFS_API_URL", "http://127.0.0.1:5001")).rstrip("/")
        self.api_base = f"{self.api_url}/api/v0"

    def is_available(self) -> bool:
        """檢查 kubo daemon 有冇行緊。"""
        try:
            req = urllib.request.Request(f"{self.api_base}/version", method="POST")
            with urllib.request.urlopen(req, timeout=3):
                return True
        except (urllib.error.URLError, OSError):
            return False

    def publish(self, files: List[Tuple[str, bytes]]) -> str:
        """
        Publish 成 directory（保留結構），用 multipart/form-data。
        kubo 會自己計真 CID（dag-pb / UnixFS）。

        用 wrap-with-directory=true：kubo 會自動將所有上傳嘅 file 包成
        一個 root directory，root 嘅 Name 係 ""。每個 file 嘅 filename
        用相對路徑（例如 entries/entry_001.md）以保留子目錄結構。
        """
        boundary = "hiveagi-boundary-" + os.urandom(8).hex()
        body = self._build_multipart(files, boundary)

        req = urllib.request.Request(
            f"{self.api_base}/add?pin=true&recursive=true&wrap-with-directory=true",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

        # kubo /add 對每個 file 回一行 JSON；最後一行係 root dir
        with urllib.request.urlopen(req, timeout=60) as resp:
            lines = resp.read().decode("utf-8").strip().split("\n")

        root = None
        for line in lines:
            obj = json.loads(line)
            if obj.get("Name") == "":
                root = obj["Hash"]
        if root is None:
            # fallback：取最後一個有 Hash 嘅
            for line in reversed(lines):
                obj = json.loads(line)
                if "Hash" in obj:
                    root = obj["Hash"]
                    break
        if root is None:
            raise RuntimeError(f"kubo /add returned no root CID: {lines[-3:]}")
        return root

    def resolve(self, cid: str) -> List[Tuple[str, bytes]]:
        """用 `ipfs ls` 列出 dir 內容（遞迴處理子目錄），再逐個 `cat`。"""
        return self._ls_recursive(cid, prefix="")

    def _ls_recursive(self, cid: str, prefix: str) -> List[Tuple[str, bytes]]:
        """遞迴 walk 一個 IPFS directory，返回所有 file。"""
        req = urllib.request.Request(
            f"{self.api_base}/ls?arg={cid}", method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            ls_data = json.loads(resp.read().decode("utf-8"))

        objects = ls_data.get("Objects", [])
        if not objects:
            raise RuntimeError(f"kubo /ls returned empty: {ls_data}")

        files: List[Tuple[str, bytes]] = []
        for link in objects[0].get("Links", []):
            name = link.get("Name", "")
            if not name:
                continue
            sub_cid = link["Hash"]
            rel_path = f"{prefix}/{name}" if prefix else name
            # Type: 1 = directory, 2 = file（kubo UnixFS）
            if link.get("Type") == 1:
                # 遞迴入子目錄
                files.extend(self._ls_recursive(sub_cid, rel_path))
            else:
                content = self._cat(sub_cid)
                files.append((rel_path, content))
        return files

    def _cat(self, cid: str) -> bytes:
        req = urllib.request.Request(
            f"{self.api_base}/cat?arg={cid}", method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()

    @staticmethod
    def _build_multipart(files: List[Tuple[str, bytes]], boundary: str) -> bytes:
        """
        手工 multipart/form-data（stdlib 冇簡單 API）。

        filename 用相對路徑（例如 entries/entry_001.md）—— 配合
        wrap-with-directory=true，kubo 會保留子目錄結構。
        """
        parts = []
        for rel_path, content in files:
            parts.append(f"--{boundary}\r\n".encode("utf-8"))
            # filename 用相對路徑（無 leading /），令 wrap 出嚟嘅 dir 結構正確
            parts.append(
                f'Content-Disposition: form-data; name="file"; filename="{rel_path}"\r\n'
                .encode("utf-8")
            )
            parts.append(b"Content-Type: application/octet-stream\r\n\r\n")
            parts.append(content)
            parts.append(b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode("utf-8"))
        return b"".join(parts)


def make_client(mock: bool = False, api_url: str = None) -> P2PClient:
    """工廠：揀 Mock 定 Kubo。"""
    if mock:
        return MockP2PClient()
    return KuboP2PClient(api_url=api_url)
