# Hardware Specification — HiveAGI Edge Node

> Device-agnostic requirements. Any phone or glasses that meet these specs
> can serve as a HiveAGI edge node. No brand recommendations — just the
> minimum capabilities the architecture demands.

---

## AI Glasses (Layer 0: Capture)

The glasses are the eyes. Their only job: capture and stream to the phone.

### Minimum requirements

| Requirement | Spec | Why |
|:---|:---|:---|
| Camera | ≥ 12MP still, 1080p video | Clear enough frames for LLM visual analysis |
| Connectivity | Bluetooth Low Energy (BLE) | Low-power stream to paired phone |
| Open SDK | Python + mobile SDK, open source | HiveAGI writes its own capture app — no vendor lock-in |
| On-device scripting | Lua or equivalent (optional) | Pre-filter on glasses before sending to phone (saves battery) |
| Microphone | Yes (optional) | Audio capture for future voice-tagging |
| Battery | ≥ 4 hours continuous capture | Half-day use with charging |
| Weight | ≤ 50g | Wearable all day without fatigue |

### Reference: Brilliant Labs Frame

- Open source SDK (Python `frame-sdk`, Flutter, Lua on-device)
- BLE connectivity, camera + microphone
- Community projects already demonstrate capture → local LLM pipelines
- ~$349 USD
- This is an example of a device that meets the spec, not a recommendation.

---

## Mobile Phone (Layer 1-2: Filter + Understand)

The phone is the local brain. It runs the tiny LLM, filters input, produces
tags, and escalates uncertain cases to the cloud.

### Minimum requirements

| Requirement | Spec | Why |
|:---|:---|:---|
| RAM | ≥ 12GB (16GB+ preferred) | Holds the local LLM (7B ≈ 6-8GB) + OS + app + vault |
| NPU / AI accelerator | Any modern mobile NPU | Runs LLM inference on-device (not CPU) |
| On-device LLM support | ONNX Runtime, MLX, CoreML, or Qualcomm AI Direct | The framework that executes the model |
| BLE | Bluetooth 5.0+ LE | Pairs with glasses |
| Storage | ≥ 256GB | Local clip retention + Obsidian vault + model weights |
| OS | Android or iOS (both supported) | HiveAGI app is cross-platform (Flutter) |
| Network | 5G or WiFi | Cloud escalation + IPFS sharing |

### Preferred capabilities (not required)

| Capability | Why it helps |
|:---|:---|
| Large screen (≥ 7" or foldable) | Side-by-side clip comparison, vault reading — the human review workspace |
| 16GB+ RAM | 7-13B models (smarter filtering, fewer cloud escalations) |
| 24GB+ RAM | 30B MoE models (GLM-4.7-Flash, deep local reasoning) |
| Built-in LLM (manufacturer) | Reduces setup — model already optimized for the hardware |
| Native DeepSeek integration | HiveAGI's auditor already speaks this language |

### How RAM maps to model choice

| Phone RAM | Max practical model | HiveAGI role |
|:---|:---|:---|
| 8GB | 1-3B (Qwen2.5-1.5B, Llama-3.2-1B) | Basic filter only — frequent cloud escalation |
| 12-16GB | 7B (Qwen2.5-7B, MagicLM) | Filter + understand — 90%+ handled locally |
| 16-24GB | 7-13B or 30B MoE (GLM-4.7-Flash) | Filter + understand + light reasoning — 95%+ local |

---

## Cloud (Layer 3: Reason)

No hardware spec — cloud APIs accessed via network.

| Component | Purpose | Access |
|:---|:---|:---|
| MiniMax M3 | Deep visual analysis, script writing, complex judgment | REST API (`api.minimax.io`) |
| DeepSeek V4 Flash | Audit, verification, correction | REST API (`api.deepseek.com`) |
| Pexels | Stock footage sourcing (Forge only) | REST API + keychain |

---

## Network (Layer 4: Share)

| Component | Purpose | Requirement |
|:---|:---|:---|
| IPFS / kubo | Content-addressed Seed Package exchange | `p2p_exchange/` module (already built) |
| Obsidian sync | Vault synchronization across devices | File-based (Syncthing, iCloud, or manual) |

---

## The edge node as a system

```
┌──────────────────────────────────────────────────┐
│                  EDGE NODE                        │
│                                                  │
│  Glasses ──BLE──→ Phone                          │
│  (capture)        ├── Tiny LLM (NPU, local)      │
│                   ├── HiveAGI app (Flutter)       │
│                   ├── Obsidian vault (memory)     │
│                   └── Escalation client → Cloud   │
│                                                  │
│  Any phone meeting the RAM + NPU spec works.     │
│  Any glasses with open SDK + BLE works.          │
│  No brand lock-in.                               │
└──────────────────────────────────────────────────┘
```
