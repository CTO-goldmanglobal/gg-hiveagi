# PII Anonymizer

Removes PII such as faces and license plates from Raw Data (images / video) before it is sent to the LLM Wiki Engine.
**Ensures that only the "scene knowledge" of the human perspective enters the wiki, not personally identifiable data.**

## Status

🚧 **P0: STUB.** The interface is defined; the implementation is deferred to P1.

| Module | Status | Planned Technology |
| :--- | :--- | :--- |
| `blur_faces.py` | STUB | MediaPipe Face Detection + OpenCV Gaussian blur |
| `blur_plates.py` | STUB | HyperLPR / YOLOv8 plate detector + OpenCV blur |

## Design Principles

1. **Mandatory before sending to the LLM** — `strip_pii()` runs before the API call (see `specs/api-protocol-v1.md` §8)
2. **Irreversible** — blurring is a destructive operation; the original image is not retained
3. **Verifiable** — after processing, the detected count is reported for the contributor to confirm

## What Will Be Added After P1

- Video support (frame-by-frame processing)
- Audio PII (voiceprints / names / phone numbers) text scanning
- Configuration files to control blur strength and which types to process

## Interface Preview

```python
from blur_faces import FaceBlur
from blur_plates import PlateBlur

fb = FaceBlur(blur_strength=51)
fb.process_file("raw/frame_001.jpg", "anon/frame_001.jpg")

pb = PlateBlur(blur_strength=71)
pb.process_file("raw/frame_001.jpg", "anon/frame_001.jpg")
```

## Contact

cto@goldmanglobal.com.au
