"""Build and validate the local Shinsekai character package."""

from __future__ import annotations

import json
import struct
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent / "package"
OUTPUT = ROOT / "dist" / "shinomiya-kaguya-v0.1.0.char"
EXPECTED_SPRITES = (
    "01_composed.png",
    "02_flustered.png",
    "03_stern.png",
    "04_warm.png",
)


def png_color_type(path: Path) -> int:
    """Return the PNG IHDR color type; 4 and 6 include an alpha channel."""
    with path.open("rb") as stream:
        signature = stream.read(8)
        if signature != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"Not a PNG file: {path}")
        length = struct.unpack(">I", stream.read(4))[0]
        chunk_type = stream.read(4)
        if chunk_type != b"IHDR" or length != 13:
            raise ValueError(f"Invalid PNG IHDR: {path}")
        ihdr = stream.read(length)
        return ihdr[9]


def validate() -> list[Path]:
    required = [SOURCE / "character.yaml", SOURCE / "manifest.json"]
    sprite_dir = SOURCE / "sprites" / "shinomiya_kaguya"
    sprites = [sprite_dir / name for name in EXPECTED_SPRITES]
    missing = [path for path in (*required, *sprites) if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing package files: " + ", ".join(map(str, missing)))

    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("character") != "四宫辉夜":
        raise ValueError("manifest character name does not match")

    config_text = (SOURCE / "character.yaml").read_text(encoding="utf-8")
    for name in EXPECTED_SPRITES:
        if f"path: {name}" not in config_text:
            raise ValueError(f"character.yaml does not reference {name}")

    for sprite in sprites:
        if png_color_type(sprite) not in (4, 6):
            raise ValueError(f"Sprite does not contain an alpha channel: {sprite}")
    return [*required, *sprites]


def build() -> Path:
    files = validate()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(SOURCE).as_posix())
    return OUTPUT


if __name__ == "__main__":
    try:
        output = build()
    except Exception as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"Built: {output}")
