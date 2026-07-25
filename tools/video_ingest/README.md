# Video Ingest

Converts street video into Hive.AGI RawData. **Two paths**, for different needs.

---

## Path 1: Manual Curation (recommended, zero PII risk)

A **human** decides which moments are worth recording — this itself is the core of the "human perspective".

### Workflow

```bash
# 1. (Optional) Extract frames at specific timestamps as references
python tools/video_ingest/extract_frames.py video.mp4 \
    --at 00:01:23,00:03:45,00:07:12 \
    --out frames/

# 2. Play the video in any player, pause when you see a moment
# 3. Run the helper, filling in each trigger
python tools/video_ingest/capture_helper.py \
    --video street_walk_001.mp4 \
    --inbox ./00_Inbox
# (the helper will ask you for each entry's timestamp / location / trigger_type / description)

# 4. After collection, run the P1 engine (text only, no vision API)
python -m llm_wiki_engine process \
    --inbox ./00_Inbox --entries ./01_Entries
```

**Why it is recommended**:
- Zero PII risk (no images are uploaded)
- Each trigger carries your human judgment (the AI does not guess automatically)
- One long video can be curated into 5–20 high-quality triggers

---

## Path 2: Auto-Vision (experimental, requires PII blur)

The AI automatically looks at frames to generate descriptions. **Must pass PII blur first** (faces + license plates).

### Workflow

```bash
# 1. Extract frames (one frame every 30 seconds)
python tools/video_ingest/extract_frames.py video.mp4 --every 30 --out frames/

# 2. Auto-vision: blur + MiniMax M3 + write to inbox
python -m llm_wiki_engine process-video \
    --frames frames/ \
    --inbox ./00_Inbox \
    --location Sydney \
    --every 30
# (for each frame: blur faces/license plates first → send to MiniMax M3 → write RawData JSON)

# 3. Run the P1 engine for audit (DeepSeek V4 Flash)
python -m llm_wiki_engine process \
    --inbox ./00_Inbox --entries ./01_Entries
```

### ⚠️ Safety Design

- **There is no `--skip-blur` flag.** This is intentional.
- Each frame must pass `anonymize_image()` (MediaPipe face + OpenCV plate) before being sent to the LLM
- If blur fails → refuse to send to the LLM (`SafetyError`)
- See `tools/pii_anonymizer/`

### Accuracy Limitations

- **License plate detection**: an edge-based generic detector with moderate recall for AU plates. Manually review low-confidence frames.
- **Vision token cost**: each frame is roughly ~500–1000 tokens. The frame extraction interval is the cost knob.

---

## Dependencies

| Path | What to Install |
|---|---|
| **Path 1 (manual)** | ffmpeg (`brew install ffmpeg`)|
| **Path 2 (auto-vision)** | ffmpeg + `pip install -r tools/pii_anonymizer/requirements.txt` + MiniMax API key |

## Files

```
tools/video_ingest/
├── extract_frames.py        # ffmpeg wrapper (shared by both paths)
├── capture_helper.py        # Path 1 interactive helper (pure stdlib)
├── templates/
│   └── manual_capture.json  # manual fill-in template
└── README.md                # this file
```

## License

AGPL-3.0 (consistent with the main repo).
