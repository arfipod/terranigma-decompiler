# Decompilation status — Terranigma (Spain PAL)

This document tracks **mechanically verified** progress for the supported 4 MiB Spanish PAL dump. It deliberately distinguishes native AOT coverage from interpreter fallback.

## Reproducible baseline

Input:

- SHA-256: `7f731f4bb620e682132660da39641dda5762211dca4732f8192dd2411211b822`
- Mapping: FastROM HiROM
- SNESRecomp upstream revision used for the baseline: `64946723e592ef83d4a96158764c3feaf0991a94`
- Project patch: `patches/snesrecomp-rtsstack-live-mx.patch`

With the current `recomp/` declarations and `tools/decompile_terranigma.py`:

- 170 explicit/architectural analysis roots
- 237 exact `(PC, M, X)` variants materialized
- 218 variants proven AOT-eligible
- 19 variants intentionally retained on the exact LLE tier
- 450 function exit `(M, X)` variants proven and fed back to the whole-program analyzer

The generated C is local-only and is not tracked by Git.

## Terranigma-specific findings already modeled

### Stack-backed DMA helpers

`85:FC52` and `85:FCBA` temporarily move the hardware stack into scratch RAM with `TCS`, consume DMA/VRAM command data with stack pulls, restore the entry stack via `TXS`, restore 8-bit accumulator mode with `SEP #$20`, and return. The generic exit analyzer cannot prove these because arbitrary `TCS/TXS` makes stack height indeterminate. Their exact demanded `M1X0 -> M1X0` contracts are therefore recorded explicitly in `recomp/exit_modes.json`.

### PHA/RTS dispatcher at `80:C967`

`80:C967` computes an index, reads one of 15 pre-decremented handler addresses from the table at `80:C9C1`, executes `PHA`, and transfers with `RTS`. The table resolves to handlers `C9DF`, `CA1A`, `CA29`, `CA6D`, `CA8E`, `CAD5`, `CAE5`, `CAF5`, `CAFE`, `CB07`, `CB1C`, `CB2C`, `CB3C`, `CB4C`, and `CB5C`.

Unlike the canonical SNESRecomp PHA/SEP/RTS pattern, Terranigma does **not** execute `SEP #$30` before the synthetic RTS. The project patch therefore makes an explicit `rtsstack` authorization preserve the dispatch site's live M/X widths, while leaving the framework's existing canonical behavior unchanged.

### Runtime code at `86:0402`

The direct call target `86:0402` lies in the low half of a HiROM bank, which maps to system/WRAM space rather than cartridge ROM. It is therefore not valid to fabricate a ROM function for it. Until its runtime byte image is captured and declared as a `ram_routine`, calls depending on it remain on LLE.

## Remaining debt

The 19 LLE variants are not one homogeneous problem. The current report separates them into:

- unresolved callee-exit semantics around the PHA/RTS dispatcher and the runtime routine at `86:0402`;
- structural poison where a naïve linear decode reaches `BRK`/`COP`, indicating inline data, computed control flow, or a missing exact function/data boundary;
- downstream callers that become AOT-eligible automatically when one of the above facts is resolved.

Every run writes `decompilation_report.json` beside the generated C with the exact LLE nodes and reasons. A reduction in the LLE count is therefore measurable and reviewable.

## Definition of “complete”

For this project, “complete decompilation” means all executable behavior from the supported ROM is accounted for by one of these auditable mechanisms:

1. an exact AOT C variant;
2. a captured and guarded runtime `ram_routine` promoted to AOT; or
3. a deliberately documented LLE boundary for behavior that is intrinsically dynamic.

It does **not** mean decoding every byte in the 4 MiB ROM as instructions; much of the image is graphics, text, maps, scripts, music, compressed resources, tables, and other data.
