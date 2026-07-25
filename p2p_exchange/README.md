# P2P Exchange — Project Hive.AGI P2

Content-addressed publishing, verification, and resolution of Seed Packages.

> **Canonical real impl = kubo (local IPFS daemon)** — truly decentralized, no vendor lock-in.
> Mock lets you run the whole pipeline without installing IPFS.

---

## Architecture

```
Seed Package directory (P0 output)
        │
        ▼
┌──────────────────────┐
│ SeedPackagePackager  │  walk directory → [(rel_path, bytes), ...]
└─────────┬────────────┘
          ▼
┌──────────────────────┐      ┌─────────────────────────┐
│   compute_mock_cid   │  OR  │  KuboP2PClient.publish  │
│   (content → CID)    │      │  (kubo daemon computes  │
│                      │      │   the real CID)         │
└─────────┬────────────┘      └────────────┬────────────┘
          │                                │
          ▼                                ▼
    mockbafy...                      bafy... (real IPFS CID)
          │                                │
          └─────────────┬──────────────────┘
                        ▼
              p2p_registry.json  (local record)
                        │
                        ▼
      Share the CID with other contributors / nodes
                        │
                        ▼
┌──────────────────────────────────────────────────────┐
│ resolve --cid <CID> --out /tmp/fetched               │
│   → rebuild the package directory                     │
│ verify --package <dir> --cid <CID>                   │
│   → recompute hash, compare against CID (detect       │
│      tampering)                                       │
└──────────────────────────────────────────────────────┘
```

---

## Usage

### Mock Mode (zero install, for testing)

```bash
# 1. First generate a Seed Package with P0
python tools/seed_generator/generate_seed.py

# 2. Publish (compute CID + record in registry)
python -m p2p_exchange publish \
    --package seed_output/seed_goldman_20260725 \
    --mock

# 3. Verify (recompute hash and compare against CID)
python -m p2p_exchange verify \
    --package seed_output/seed_goldman_20260725 \
    --cid <the CID from above> \
    --mock

# 4. Resolve (use the CID to fetch + rebuild the directory)
python -m p2p_exchange resolve \
    --cid <CID> \
    --out /tmp/fetched_package \
    --mock

# 5. List (view the local registry)
python -m p2p_exchange list
```

### Real Mode (Kubo / IPFS daemon)

1. **Install kubo**: https://docs.ipfs.tech/install/
2. Start the daemon:
   ```bash
   ipfs daemon &
   ```
3. (Optional) Configure the endpoint (default `http://127.0.0.1:5001`):
   ```bash
   # .env
   IPFS_API_URL=http://127.0.0.1:5001
   ```
4. Run (without `--mock`):
   ```bash
   python -m p2p_exchange publish --package seed_output/seed_goldman_20260725
   ```

---

## 🔒 Trust Model (Honest Note)

### What P2 Delivers
- ✅ **Content addressing** — the same package content always maps to the same CID
- ✅ **Integrity verification** — the recipient can recompute the hash to detect tampering
- ✅ **Publish / resolve** — via the kubo daemon or the mock store
- ✅ **Local registry** — records packages published locally

### What P2 Does Not Deliver (deferred to P2.5)
- ❌ **Peer discovery** — automatically finding other contributor nodes
- ❌ **Background sync** — automatically fetching new packages from other peers
- ❌ **libp2p pubsub** — broadcasting CID announcements

The seam for P2.5 is `p2p_registry.json` — in the future pubsub will broadcast the entries inside the registry.

### CID Compatibility
- **Mock CID** (`mockbafy...`) and **real kubo CID** (`bafy...`) **will not be byte-for-byte identical**.
  Kubo uses DAG-PB / UnixFS multi-layer wrapping; Mock is only a content hash.
- Both are content-derived — the same content → the same CID, consistent across recomputes.
- The `verify` command recomputes locally for mock CIDs; for real kubo CIDs it suggests using `ipfs cat | sha256sum` to verify manually.

---

## Design Principles

1. **No new dependencies** — pure stdlib (`urllib`, `json`, `hashlib`, `base64`).
   In keeping with the project's "minimal, auditable" ethos.
2. **Decentralization first** — kubo is canonical, not a pinning service.
   Pinning (Pinata, etc.) may be added as an optional impl in the future.
3. **Mock/Real abstraction** — the same pattern as P1's `LLMClient`,
   the pipeline is testable with zero install, and connecting to the daemon requires zero orchestration changes.

---

## File Structure

```
p2p_exchange/
├── __init__.py
├── __main__.py
├── cli.py            # publish / verify / resolve / list / --mock
├── client.py         # P2PClient ABC + MockP2PClient + KuboP2PClient
├── cid.py            # deterministic content addressing (sha256 + base32)
├── package.py        # dir ↔ (rel_path, bytes) serialization
├── registry.py       # p2p_registry.json local record
├── verify.py         # integrity check (tamper detection)
├── requirements.txt  # stdlib only
└── README.md
```

## License

AGPL-3.0 (consistent with the main Project Hive.AGI project).
