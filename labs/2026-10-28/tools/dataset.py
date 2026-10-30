"""Capture JPEGs, audit labels/sessions, and split whole sessions without leakage."""
import argparse
import hashlib
import io
import json
import re
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image, ImageOps


def token(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError("label/session must use letters, digits, _ or -")
    return value


def capture(url, root, label, session, count=1, interval=1.0):
    if count < 1 or interval < 0:
        raise ValueError("invalid count/interval")
    folder = Path(root) / token(label) / token(session)
    folder.mkdir(parents=True, exist_ok=True)
    saved = []
    for _ in range(count):
        with urllib.request.urlopen(url, timeout=10) as response:
            payload = response.read(8_000_001)
        if len(payload) > 8_000_000:
            raise ValueError("image exceeds 8MB")
        with Image.open(io.BytesIO(payload)) as image:
            image.load()
            rgb = ImageOps.exif_transpose(image).convert("RGB")
        path = folder / (str(time.time_ns()) + ".jpg")
        rgb.save(path, quality=95)
        saved.append(str(path))
        if len(saved) < count:
            time.sleep(interval)
    return saved


def audit(root, test_sessions):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("dataset directory does not exist")
    rows, errors = [], []
    hashes = defaultdict(list)
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        relative = path.relative_to(root)
        if len(relative.parts) != 3:
            errors.append(f"expected label/session/image: {relative}")
            continue
        label, session, _ = relative.parts
        try:
            token(label)
            token(session)
            with Image.open(path) as im:
                rgb = ImageOps.exif_transpose(im).convert("RGB")
                rgb.load()
                # Hash decoded pixels, so metadata-only changes are duplicates too.
                digest = hashlib.sha256(str(rgb.size).encode() + rgb.tobytes()).hexdigest()
                width, height = rgb.size
        except (OSError, ValueError) as exc:
            errors.append(f"unreadable image: {relative}: {type(exc).__name__}")
            continue
        row = dict(path=relative.as_posix(), label=label, session=session,
                   split="testing" if session in test_sessions else "training",
                   width=width, height=height, pixel_sha256=digest)
        hashes[digest].append(row)
        rows.append(row)
    if not rows:
        errors.append("no readable images")
    missing = set(test_sessions) - {r["session"] for r in rows}
    if missing:
        errors.append("test sessions not found: " + ", ".join(sorted(missing)))
    counts = Counter((r["label"], r["split"]) for r in rows)
    for label in sorted({r["label"] for r in rows}):
        for split in ("training", "testing"):
            if not counts[label, split]:
                errors.append(f"missing {split} samples for {label}")
    duplicates = []
    for entries in hashes.values():
        if len(entries) < 2:
            continue
        duplicates.append([r["path"] for r in entries])
        if len({r["split"] for r in entries}) > 1:
            errors.append("duplicate pixels across train/test: " + entries[0]["path"])
        if len({r["label"] for r in entries}) > 1:
            errors.append("conflicting labels: " + entries[0]["path"])
    return dict(images=rows, counts={f"{a}/{b}": c for (a, b), c in sorted(counts.items())},
                duplicates=duplicates, errors=errors, valid=not errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    cap = commands.add_parser("capture")
    cap.add_argument("--url", required=True)
    cap.add_argument("--root", default="runtime/images")
    cap.add_argument("--label", required=True)
    cap.add_argument("--session", required=True)
    cap.add_argument("--count", type=int, default=1)
    cap.add_argument("--interval", type=float, default=1.0)
    check = commands.add_parser("audit")
    check.add_argument("root")
    check.add_argument("--test-session", action="append", required=True)
    check.add_argument("--out", default="runtime/manifest.json")
    args = parser.parse_args()
    if args.command == "capture":
        print(json.dumps(capture(args.url, args.root, args.label, args.session,
                                 args.count, args.interval), ensure_ascii=False, indent=2))
    else:
        result = audit(args.root, set(args.test_session))
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in result.items() if k != "images"}, ensure_ascii=False, indent=2))
        raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
