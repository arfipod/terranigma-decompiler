#!/usr/bin/env python3
"""Verify that an input ROM is an explicitly supported original dump.

This tool intentionally does not download, patch, normalize, trim, deheader,
or otherwise manufacture a supported ROM. The caller must supply the exact
original .sfc dump locally.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "roms.json"


def hashes(data: bytes) -> dict[str, str | int]:
    return {
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "md5": hashlib.md5(data).hexdigest(),  # compatibility identifier only
        "crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08X}",
    }


def load_manifest(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc["roms"]


def find_match(actual: dict[str, str | int], candidates: list[dict]) -> dict | None:
    for rom in candidates:
        if (
            rom.get("size") == actual["size"]
            and rom.get("sha256", "").lower() == actual["sha256"]
        ):
            return rom
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a user-supplied Terranigma .sfc against supported clean dumps."
    )
    parser.add_argument("rom", type=Path, help="path to the user's local original .sfc dump")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if args.rom.suffix.lower() != ".sfc":
        print("ERROR: input must be an original .sfc file; no conversion is performed.", file=sys.stderr)
        return 2
    if not args.rom.is_file():
        print(f"ERROR: ROM not found: {args.rom}", file=sys.stderr)
        return 2

    actual = hashes(args.rom.read_bytes())
    match = find_match(actual, load_manifest(args.manifest))

    result = {
        "verified": bool(match),
        "input": str(args.rom),
        "actual": actual,
        "rom": match,
    }

    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif match:
        print(f"VERIFIED: {match['display_name']} ({match['id']})")
        print(f"SHA-256: {actual['sha256']}")
    else:
        print("ERROR: ROM is not an explicitly supported verified dump.", file=sys.stderr)
        print(f"Size:    {actual['size']}", file=sys.stderr)
        print(f"SHA-256: {actual['sha256']}", file=sys.stderr)
        print("No patches or analysis have been applied.", file=sys.stderr)

    return 0 if match else 1


if __name__ == "__main__":
    raise SystemExit(main())
