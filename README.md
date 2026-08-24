# Terranigma Decompiler

Experimental tooling for analyzing and progressively recompiling **Terranigma** from a user-supplied original SNES ROM dump into portable C.

## ROM-required design

This repository intentionally contains **no Terranigma ROM, game assets, extracted data, generated decompilation output, or compiled game binary**.

Every analysis/build begins from an **original, user-supplied `.sfc` dump**. The toolchain verifies the input before processing it. Generated code and extracted data remain local and are ignored by Git.

The initial supported target is the clean Spanish PAL dump:

- Size: `4,194,304` bytes (headerless `.sfc`)
- SHA-256: `7f731f4bb620e682132660da39641dda5762211dca4732f8192dd2411211b822`
- SHA-1: `1e1a85cf28bcb69cb34fc71f48347279d7cfea7e`
- MD5: `5223853d5edc9856f2bf8a9f04d01d3a`
- CRC32: `00E61534`

Other verified original revisions can be added to `config/roms.json` without ever committing their contents.

## Goal

The first milestone is a mechanically correct and traceable **65C816 -> C** recompilation. Readable game-level code can then be recovered incrementally while preserving behavior.

Planned layers:

1. ROM verification and SNES header analysis.
2. 65C816 control-flow discovery and C emission.
3. Hybrid recompilation/interpreter fallback for unresolved dynamic code.
4. SNES hardware runtime (PPU, DMA, APU/DSP, input, SRAM).
5. Behavior/trace comparison against the original ROM.
6. Optional native backends and presentation enhancements.

## Usage principle

```text
original user-owned Terranigma.sfc
              |
              v
        verify_rom.py
              |
              v
       local decompilation
              |
              v
    generated/  (never committed)
```

The repository is designed so that cloning it alone is insufficient to reconstruct or play the commercial game.

## Repository policy

See [`docs/ROM_INPUT_AND_DISTRIBUTION_POLICY.md`](docs/ROM_INPUT_AND_DISTRIBUTION_POLICY.md).

This project is an independent research project and is not affiliated with or endorsed by the game's rights holders. The repository policy is intended to avoid redistribution of copyrighted game content; it is not legal advice and does not guarantee that every possible use is lawful in every jurisdiction.
