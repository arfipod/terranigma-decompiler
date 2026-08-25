#!/usr/bin/env python3
"""Reproducible Terranigma (Spain PAL) SNESRecomp front-end.

The original ROM is always user-supplied and remains local. Generated C is
written under the requested output directory and is intentionally not suitable
for redistributing as part of this repository.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

EXPECTED_SIZE = 4_194_304
EXPECTED_SHA256 = "7f731f4bb620e682132660da39641dda5762211dca4732f8192dd2411211b822"
MX_COMBOS = ((0, 0), (0, 1), (1, 0), (1, 1))


def _open_rom(path: Path) -> tuple[bytes, str]:
    raw = path.read_bytes()
    if path.suffix.lower() != ".zip":
        return raw, path.name
    with zipfile.ZipFile(path) as zf:
        members = [n for n in zf.namelist() if n.lower().endswith((".sfc", ".smc")) and not n.endswith("/")]
        if len(members) != 1:
            raise ValueError(f"ZIP must contain exactly one .sfc/.smc file; found {len(members)}")
        return zf.read(members[0]), members[0]


def _verify_rom(raw: bytes) -> None:
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) != EXPECTED_SIZE or digest != EXPECTED_SHA256:
        raise ValueError(
            "Unsupported ROM dump. Expected Terranigma (Spain) PAL, "
            f"size={EXPECTED_SIZE}, sha256={EXPECTED_SHA256}; got "
            f"size={len(raw)}, sha256={digest}")


def _load_manual_exit_modes(path: Path) -> dict[tuple[int, int, int], tuple[int, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    result = {}
    for item in data.get("variants", []):
        pc = int(str(item["pc24"]), 16)
        em, ex = int(item["entry_m"]), int(item["entry_x"])
        xm, xx = int(item["exit_m"]), int(item["exit_x"])
        result[(pc, em & 1, ex & 1)] = (xm & 1, xx & 1)
    return result


def _digest_files(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in sorted(paths):
        h.update(path.name.encode())
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Decompile Terranigma Spain PAL to local C using SNESRecomp")
    ap.add_argument("rom", type=Path, help="user-supplied .sfc/.smc or ZIP containing exactly one ROM")
    ap.add_argument("--out-dir", type=Path, default=Path("generated/terranigma-spain"))
    ap.add_argument("--snesrecomp-root", type=Path, default=os.environ.get("SNESRECOMP_ROOT"))
    ap.add_argument("--analysis-only", action="store_true")
    ap.add_argument("--strict-aot", action="store_true", help="fail if any exact variant remains on LLE")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parent.parent
    framework = args.snesrecomp_root
    if framework is None:
        raise SystemExit("Set SNESRECOMP_ROOT or pass --snesrecomp-root")
    framework = Path(framework).resolve()
    for p in (framework, framework / "recompiler", framework / "tools"):
        sys.path.insert(0, str(p))

    from snes65816 import clear_reloc_regions, detect_rom_mapping, set_rom_mapping  # type: ignore
    from v2.decoder import clear_decode_cache, decode_function, analyze_function_exit_mx  # type: ignore
    from v2.program_emit import emit_program  # type: ignore
    from v2_analyze import _load_cfgs, _seed_auto_vectors, build_manifest  # type: ignore

    raw, member_name = _open_rom(args.rom.resolve())
    _verify_rom(raw)
    clear_reloc_regions()
    set_rom_mapping(detect_rom_mapping(raw))

    cfg_dir = repo / "recomp"
    parsed = _load_cfgs(cfg_dir)
    _seed_auto_vectors(parsed, raw)
    manual = _load_manual_exit_modes(cfg_dir / "exit_modes.json")

    # Prove all exact exit-width variants that the generic analyzer can prove,
    # not only width-mutating exits. The whole-program AOT classifier needs
    # positive proof even when a callee preserves M/X.
    known = dict(manual)
    for _iteration in range(12):
        snapshot = dict(known)
        next_known = dict(known)
        clear_decode_cache()
        changes = 0
        for bank, _cfg_path, cfg in parsed:
            indirect = {(bank << 16) | d["site_pc16"]: d for d in cfg.indirect_dispatch}
            siblings = {(bank << 16) | (e.start & 0xFFFF) for e in cfg.entries}
            for entry in cfg.entries:
                pc24 = (bank << 16) | (entry.start & 0xFFFF)
                for em, ex in MX_COMBOS:
                    key = (pc24, em, ex)
                    if key in manual:
                        continue
                    try:
                        graph = decode_function(
                            raw, bank, entry.start & 0xFFFF,
                            entry_m=em, entry_x=ex, end=entry.end,
                            indirect_dispatch=indirect,
                            callee_exit_mx=snapshot,
                            sibling_entry_pcs=siblings,
                        )
                        pair = analyze_function_exit_mx(graph, snapshot)
                    except Exception:
                        continue
                    if pair[0] is None or pair[1] is None:
                        continue
                    resolved = (pair[0] & 1, pair[1] & 1)
                    if next_known.get(key) != resolved:
                        next_known[key] = resolved
                        changes += 1
        known = next_known
        if changes == 0:
            break

    # Feed every proven variant into the manifest classifier in-memory. This
    # keeps per-variant precision; broadcasting exit_mx_at would be unsound.
    for bank, _cfg_path, cfg in parsed:
        cfg.exit_mx_at_per_variant.clear()
        for entry in cfg.entries:
            pc24 = (bank << 16) | (entry.start & 0xFFFF)
            for em, ex in MX_COMBOS:
                pair = known.get((pc24, em, ex))
                if pair is not None:
                    cfg.exit_mx_at_per_variant.append(
                        (bank, entry.start & 0xFFFF, em, ex, pair[0], pair[1]))

    manifest, helpers, inline_args = build_manifest(
        raw, parsed, max_insns=4096, max_nodes=100_000, all_cfg_roots=True)
    manifest_json = manifest.to_json()
    data = json.loads(manifest_json)
    dispositions = collections.Counter(n["disposition"] for n in data["nodes"].values())
    reasons = collections.Counter(r for n in data["nodes"].values() for r in n.get("reasons", []))

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "rom_member": member_name,
        "rom_sha256": EXPECTED_SHA256,
        "mapping": "HiROM",
        "roots": len(data["roots"]),
        "exact_variants": len(data["nodes"]),
        "aot_variants": dispositions.get("aot_eligible", 0),
        "lle_variants": dispositions.get("lle_only", 0),
        "proven_exit_variants": len(known),
        "reason_counts": dict(sorted(reasons.items())),
        "lle_nodes": {
            k: v.get("reasons", []) for k, v in data["nodes"].items()
            if v["disposition"] != "aot_eligible"
        },
    }
    (out_dir / "decompilation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "program_manifest.json").write_text(manifest_json, encoding="utf-8")

    if not args.analysis_only:
        cfg_files = list(cfg_dir.glob("*.cfg")) + [cfg_dir / "exit_modes.json"]
        generator_digest = _digest_files([
            framework / "recompiler" / "v2" / "decoder.py",
            framework / "recompiler" / "v2" / "program_emit.py",
            Path(__file__).resolve(),
        ])
        config_digest = _digest_files(cfg_files)
        analysis_input_digest = hashlib.sha256(
            (EXPECTED_SHA256 + generator_digest + config_digest).encode()).hexdigest()
        emit_program(
            rom=raw, parsed=parsed, manifest=manifest,
            dispatch_helpers=helpers, inline_arg_map=inline_args,
            out_dir=out_dir, manifest_text=manifest_json,
            generator_digest=generator_digest, config_digest=config_digest,
            analysis_input_digest=analysis_input_digest,
            callee_exit_mx={(k.pc24, k.m, k.x): pair for k, pair in manifest.exit_modes.items()},
            callee_exit_mx_modes={(k.pc24, k.m, k.x): frozenset(v) for k, v in manifest.exit_mode_sets.items()},
            enable_hle=True,
        )
        # emit_program atomically replaces out_dir, so restore the concise report.
        (out_dir / "decompilation_report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"ROM verified: {member_name} ({EXPECTED_SHA256})")
    print(f"Exact variants: {report['exact_variants']} | AOT: {report['aot_variants']} | LLE: {report['lle_variants']}")
    print(f"Proven exit variants: {report['proven_exit_variants']}")
    print(f"Report: {out_dir / 'decompilation_report.json'}")
    if args.strict_aot and report["lle_variants"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
