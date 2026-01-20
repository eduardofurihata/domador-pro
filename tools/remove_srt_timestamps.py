#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


TIMESTAMP_LINE_RE = re.compile(
    r"^\s*\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}.*\s*$"
)
INDEX_LINE_RE = re.compile(r"^\s*\d+\s*$")


def read_text_best_effort(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def write_text_utf8(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def remove_srt_metadata(text: str) -> str:
    lines = text.splitlines()
    kept: list[str] = []

    for line in lines:
        if TIMESTAMP_LINE_RE.match(line):
            continue

        if INDEX_LINE_RE.match(line):
            # Treat as an SRT cue index only when it appears at a cue boundary
            # (start of file or after a blank line).
            prev = kept[-1] if kept else ""
            if not prev.strip():
                continue

        kept.append(line)
    # Preserve trailing newline if present
    out = "\n".join(kept)
    if text.endswith("\n") and not out.endswith("\n"):
        out += "\n"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove SRT timestamp lines (e.g. 00:00:00,000 --> 00:00:04,740)."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default="doc/aulas",
        help="Root directory to scan (default: doc/aulas).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write files; just report which would change.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"Root does not exist: {root}")

    changed_files = 0
    for path in sorted(root.rglob("*.srt")):
        original = read_text_best_effort(path)
        updated = remove_srt_metadata(original)
        if updated != original:
            changed_files += 1
            if not args.dry_run:
                write_text_utf8(path, updated)
            print(path)

    if args.dry_run:
        print(f"\nWould change {changed_files} file(s).")
    else:
        print(f"\nChanged {changed_files} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
