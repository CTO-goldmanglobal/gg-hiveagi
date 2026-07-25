# P2P Exchange — Project Hive.AGI P2

Seed Package 嘅 content-addressed 發佈、驗證、解析。

> **Canonical real impl = kubo（local IPFS daemon）** —— 真正去中心化，無 vendor lock-in。
> Mock 令你唔使裝 IPFS 都可以行通成個 pipeline。

---

## 架構

```
Seed Package 目錄 (P0 輸出)
        │
        ▼
┌──────────────────────┐
│ SeedPackagePackager  │  walk 目錄 → [(rel_path, bytes), ...]
└─────────┬────────────┘
          ▼
┌──────────────────────┐      ┌─────────────────────────┐
│   compute_mock_cid   │  OR  │  KuboP2PClient.publish  │
│   (content → CID)    │      │  (kubo daemon 計真 CID) │
└─────────┬────────────┘      └────────────┬────────────┘
          │                                │
          ▼                                ▼
    mockbafy...                      bafy... (真 IPFS CID)
          │                                │
          └─────────────┬──────────────────┘
                        ▼
              p2p_registry.json  (本地記錄)
                        │
                        ▼
      分享 CID 俾其他貢獻者 / 節點
                        │
                        ▼
┌──────────────────────────────────────────────────────┐
│ resolve --cid <CID> --out /tmp/fetched               │
│   → 重建 package 目錄                                 │
│ verify --package <dir> --cid <CID>                   │
│   → recompute hash，對比 CID（偵測篡改）              │
└──────────────────────────────────────────────────────┘
```

---

## 用法

### Mock 模式（零安裝，測試用）

```bash
# 1. 先用 P0 生成一個 Seed Package
python tools/seed_generator/generate_seed.py

# 2. Publish（計 CID + 記入 registry）
python -m p2p_exchange publish \
    --package seed_output/seed_goldman_20260725 \
    --mock

# 3. Verify（recompute hash 對比 CID）
python -m p2p_exchange verify \
    --package seed_output/seed_goldman_20260725 \
    --cid <上面嗰個 CID> \
    --mock

# 4. Resolve（用 CID 拎返 + 重建目錄）
python -m p2p_exchange resolve \
    --cid <CID> \
    --out /tmp/fetched_package \
    --mock

# 5. List（睇本地 registry）
python -m p2p_exchange list
```

### 真實模式（Kubo / IPFS daemon）

1. **安裝 kubo**：https://docs.ipfs.tech/install/
2. 啟動 daemon：
   ```bash
   ipfs daemon &
   ```
3. （可選）設定 endpoint（預設 `http://127.0.0.1:5001`）：
   ```bash
   # .env
   IPFS_API_URL=http://127.0.0.1:5001
   ```
4. 跑（唔加 `--mock`）：
   ```bash
   python -m p2p_exchange publish --package seed_output/seed_goldman_20260725
   ```

---

## 🔒 Trust Model（誠實說明）

### P2 已交付
- ✅ **Content addressing** —— 同一 package 內容永遠映射到同一 CID
- ✅ **Integrity verification** —— 收件者可 recompute hash 偵測篡改
- ✅ **Publish / resolve** —— 經 kubo daemon 或 mock store
- ✅ **Local registry** —— 記錄本地 publish 過嘅 package

### P2 未交付（留畀 P2.5）
- ❌ **Peer discovery** —— 自動搵到其他貢獻者節點
- ❌ **Background sync** —— 自動由其他 peer 拎新 package
- ❌ **libp2p pubsub** —— broadcast CID announcement

P2.5 嘅 seam 就係 `p2p_registry.json` —— 未來 pubsub 會 broadcast registry 入面嘅 entry。

### CID 相容性
- **Mock CID**（`mockbafy...`）同 **kubo 真 CID**（`bafy...`）**唔會 byte-for-byte 一樣**。
  Kubo 用 DAG-PB / UnixFS 多層 wrapping；Mock 淨係 content hash。
- 兩者都係 content-derived —— 同一內容 → 同一 CID，重複計都一樣。
- `verify` command 對 mock CID 會本地 recompute；對真 kubo CID 會提示用 `ipfs cat | sha256sum` 自行核對。

---

## 設計原則

1. **無新依賴** —— 純 stdlib（`urllib`, `json`, `hashlib`, `base64`）。
   呼應 project「minimal, auditable」嘅精神。
2. **去中心化優先** —— kubo 係 canonical，唔係 pinning service。
   Pinning（Pinata 等）未來可做可選 impl。
3. **Mock/Real 抽象** —— 同 P1 `LLMClient` 一致嘅模式，
   pipeline 喺零安裝下可測，接 daemon 後零 orchestration 改動。

---

## 檔案結構

```
p2p_exchange/
├── __init__.py
├── __main__.py
├── cli.py            # publish / verify / resolve / list / --mock
├── client.py         # P2PClient ABC + MockP2PClient + KuboP2PClient
├── cid.py            # deterministic content addressing (sha256 + base32)
├── package.py        # dir ↔ (rel_path, bytes) 序列化
├── registry.py       # p2p_registry.json 本地記錄
├── verify.py         # integrity check（篡改偵測）
├── requirements.txt  # stdlib only
└── README.md
```

## License

AGPL-3.0（同 Project Hive.AGI 主項目一致）。
