# Terranigma Decompiler

Experimental tooling for analyzing and progressively recompiling **Terranigma** from a user-supplied original SNES ROM dump into portable C.

## Current mechanical baseline

The supported Spanish PAL ROM now has a reproducible SNESRecomp project under `recomp/` plus a ROM-local front-end in `tools/decompile_terranigma.py`. On the exact supported dump, the current baseline materializes **237 exact `(PC,M,X)` variants: 218 AOT and 19 exact LLE**, with 450 function-exit M/X variants proven. See [`docs/DECOMPILATION_STATUS.md`](docs/DECOMPILATION_STATUS.md) for what remains and why the LLE count is not being mislabeled as completed AOT coverage.

## ROM-required design

This repository intentionally contains **no Terranigma ROM, game assets, extracted data, generated decompilation output, or compiled game binary**.

Every analysis/build begins from an **original, user-supplied `.sfc` dump**. The front-end also accepts a ZIP containing exactly one `.sfc`/`.smc`. The toolchain verifies the input before processing it. Generated code and extracted data remain local and are ignored by Git.

The initial supported target is the clean Spanish PAL dump:

- Size: `4,194,304` bytes (headerless `.sfc`)
- SHA-256: `7f731f4bb620e682132660da39641dda5762211dca4732f8192dd2411211b822`
- SHA-1: `1e1a85cf28bcb69cb34fc71f48347279d7cfea7e`
- MD5: `5223853d5edc9856f2bf8a9f04d01d3a`
- CRC32: `00E61534`

Other verified original revisions can be added to `config/roms.json` without ever committing their contents.

## Generate the local C project

Obtain the ROM-free SNESRecomp source artifact from the repository's **Vendor SNESRecomp framework** workflow, unpack it, and point `SNESRECOMP_ROOT` at its `snesrecomp` directory. Then run:

```bash
export SNESRECOMP_ROOT=/path/to/snesrecomp
python tools/decompile_terranigma.py "/path/to/Terranigma (Spain).zip"
```

An uncompressed `.sfc`/`.smc` can be passed instead. Output defaults to `generated/terranigma-spain/` and includes:

- `bank*_v2.c` — exact AOT C translation units;
- `dispatch_v2.c` — exact dispatch table;
- `program_manifest.json` — whole-program variant manifest;
- `decompilation_report.json` — concise AOT/LLE status and unresolved reasons.

Use `--analysis-only` to produce the manifest/report without C emission. Use `--strict-aot` in experiments when you intentionally want any remaining LLE variant to make the command fail.

## Goal

The first milestone is a mechanically correct and traceable **65C816 -> C** recompilation. Readable game-level code can then be recovered incrementally while preserving behavior.

Layers:

1. ROM verification and SNES header analysis.
2. 65C816 control-flow discovery and C emission.
3. Hybrid recompilation/interpreter fallback for unresolved dynamic code.
4. SNES hardware runtime (PPU, DMA, APU/DSP, input, SRAM).
5. Behavior/trace comparison against the original ROM.
6. Optional native backends and presentation enhancements.

## Usage principle

```text
original user-owned Terranigma.sfc / .zip
              |
              v
  decompile_terranigma.py
       verify exact dump
              |
              v
 SNESRecomp + Terranigma cfg
              |
              v
 generated/  (never committed)
```

The repository is designed so that cloning it alone is insufficient to reconstruct or play the commercial game.

## Repository policy

See [`docs/ROM_INPUT_AND_DISTRIBUTION_POLICY.md`](docs/ROM_INPUT_AND_DISTRIBUTION_POLICY.md).

This project is an independent research project and is not affiliated with or endorsed by the game's rights holders. The repository policy is intended to avoid redistribution of copyrighted game content; it is not legal advice and does not guarantee that every possible use is lawful in every jurisdiction.
