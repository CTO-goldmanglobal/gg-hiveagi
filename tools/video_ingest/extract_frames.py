#!/usr/bin/env python3
"""
extract_frames.py —— 用 ffmpeg 由 video 抽 frame。

兩種模式：
  --every Ns    每 N 秒抽一帧（適合 auto-vision 全片掃描）
  --at HH:MM:SS 抽指定時間點（適合 manual curate：你睇片見到 moment）

唔需要新 Python 依賴 —— 淨係 subprocess call ffmpeg（要預先裝）。

CLI:
    python extract_frames.py video.mp4 --every 30 --out frames/
    python extract_frames.py video.mp4 --at 00:01:23 --out frames/
    python extract_frames.py video.mp4 --at 00:01:23,00:02:45 --out frames/
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def video_duration(video_path: Path) -> float:
    """用 ffprobe 拎 video 時長（秒）。"""
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ], stderr=subprocess.DEVNULL)
        return float(out.decode().strip())
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return 0.0


def extract_at(video_path: Path, timestamps: list, out_dir: Path,
               quality: int = 2) -> list:
    """
    喺指定時間點抽 frame。
    timestamps: ["00:01:23", "00:02:45", ...]
    quality: 2 = 高質（ffmpeg -qscale:v，2–5 為常用範圍）
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for ts in timestamps:
        out_file = out_dir / f"frame_{ts.replace(':', '')}.jpg"
        cmd = [
            "ffmpeg", "-y", "-ss", ts,
            "-i", str(video_path),
            "-frames:v", "1",
            "-qscale:v", str(quality),
            str(out_file),
        ]
        try:
            subprocess.run(cmd, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if out_file.exists():
                written.append(out_file)
        except subprocess.CalledProcessError as e:
            print(f"⚠️  抽 {ts} 失敗：{e}", file=sys.stderr)
    return written


def extract_every(video_path: Path, interval_sec: int, out_dir: Path,
                  quality: int = 2) -> list:
    """
    每 N 秒抽一 frame。
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    duration = video_duration(video_path)
    if duration <= 0:
        print("⚠️  攞唔到 video 時長，fallback 用 1 fps 抽（可能唔準）", file=sys.stderr)
        # fallback：fps filter
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vf", f"fps=1/{interval_sec}",
            "-qscale:v", str(quality),
            str(out_dir / "frame_%05d.jpg"),
        ]
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return sorted(out_dir.glob("frame_*.jpg"))

    # 用 list of -ss 抽（每個獨立 seek，更準確）
    timestamps = []
    t = 0
    while t < duration:
        timestamps.append(_format_timestamp(t))
        t += interval_sec
    return extract_at(video_path, timestamps, out_dir, quality)


def _format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main():
    parser = argparse.ArgumentParser(description="用 ffmpeg 抽 video frame")
    parser.add_argument("video", help="輸入 video 路徑")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--every", type=int, metavar="Ns",
                      help="每 N 秒抽一 frame")
    group.add_argument("--at", metavar="HH:MM:SS[,HH:MM:SS,...]",
                      help="喺指定時間點抽（逗號分隔）")
    parser.add_argument("--out", default="./frames",
                        help="輸出目錄（預設 ./frames）")
    parser.add_argument("--quality", type=int, default=2,
                        help="JPEG 質素 2–31，細 = 高質（預設 2）")
    args = parser.parse_args()

    if not ffmpeg_available():
        print("❌ ffmpeg 未安裝。macOS：brew install ffmpeg", file=sys.stderr)
        return 1

    video = Path(args.video)
    if not video.exists():
        print(f"❌ video 唔存在：{video}", file=sys.stderr)
        return 1

    out_dir = Path(args.out)

    if args.every:
        written = extract_every(video, args.every, out_dir, args.quality)
    else:
        ts_list = [t.strip() for t in args.at.split(",") if t.strip()]
        written = extract_at(video, ts_list, out_dir, args.quality)

    print(f"✅ 抽咗 {len(written)} 個 frame → {out_dir}/")
    for f in written[:5]:
        print(f"   {f.name}")
    if len(written) > 5:
        print(f"   ... 同埋另外 {len(written) - 5} 個")
    return 0


if __name__ == "__main__":
    sys.exit(main())
