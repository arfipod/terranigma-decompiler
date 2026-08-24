# ROM Input and Distribution Policy

## Core rule

**The original game ROM is always an external input.**

The repository must never contain, vendor, download, reconstruct, or embed the Terranigma ROM. Users are expected to provide their own lawfully obtained dump locally as a headerless `.sfc` file.

## What may be committed

The repository may contain original project code and metadata needed to operate on a local ROM, including:

- decompiler/recompiler source code;
- control-flow and analysis tooling;
- hardware runtime implementations;
- build scripts and tests;
- hashes, checksums, addresses, symbols and small patch descriptions;
- documentation describing the ROM format or reverse-engineered behavior;
- tests built from synthetic or independently authored fixtures.

## What must not be committed

Do not commit:

- `.sfc`, `.smc` or other commercial ROM images;
- extracted graphics, music, text, maps or other game assets;
- generated C/C++ that is a direct mechanical transformation of substantial portions of the commercial ROM;
- compiled executables containing the commercial ROM or substantial extracted game data;
- SRAM/save-state files containing unnecessary game data;
- temporary memory/VRAM/APU dumps containing substantial copyrighted content.

Generated material from a user's ROM belongs in ignored local directories such as `generated/`, `extracted/`, `work/` or `build/`.

## Input verification

All supported workflows should call `tools/verify_rom.py` before analysis or generation. The verifier compares file size and cryptographic hashes against `config/roms.json`.

A mismatching ROM must fail closed rather than silently selecting offsets intended for another revision. Supporting a new revision requires adding only its non-reconstructive metadata (for example, hashes and mapper information) to the manifest.

## Clean-room-friendly project structure

Where practical, keep these concerns separate:

1. **ROM-specific metadata:** addresses, symbols, hashes and configuration.
2. **Generated local output:** mechanically derived code/data, never committed.
3. **Original implementation:** reusable runtime, tools, tests and native backends authored in this repository.

This makes the public repository useful only when combined with a user's own ROM and helps avoid redistributing the commercial work itself.

## No claim of blanket legality

This policy is a technical and repository-hygiene measure intended to reduce copyright-distribution risk. It is **not legal advice**, does not grant rights to the game, and does not guarantee that reverse engineering, decompilation, modification or use is lawful in every jurisdiction or circumstance. Contributors are responsible for complying with applicable law and licenses.
