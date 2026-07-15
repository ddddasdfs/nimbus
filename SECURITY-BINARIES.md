# Coral — Bundled Binary Provenance & Verification

Coral's core Python and JavaScript are auditable source. This document tracks the
**pre-compiled binaries** that ship in the tree, which source review cannot clear on
its own. For a fully trustworthy build, each binary should be either (a) verified by
hash against an official upstream release, or (b) rebuilt from audited source.

Recorded on 2026-07-14. Hashes are SHA-256 of the files currently in the repo.

## Inventory

### Injection tools — `injection/tools/` (from CSLOL-manager / LeagueToolkit)

| File | Size (bytes) | SHA-256 (as committed) | Notes |
|------|-------------:|------------------------|-------|
| `mod-tools.exe`   | 897,144 | `25FA57EB81ED308DCF8E3E2ABA1E3981E1697C99752F879E84746D1D90B4CB44` | Does the actual overlay build + injection (`mkoverlay`/`runoverlay`). No version resource. |
| `wad-extract.exe` | 833,024 | `0344A013E7FA03D1623938CD83F52EDB29ECA01A5A12F10004FB5266F30138C5` | WAD archive extraction. No version resource. |
| `wad-make.exe`    | 930,816 | `AC93DDC21A01917713957C6E9FF250CB0DA5AF53DF2BBB08EA11DB02D12AAF79` | WAD archive creation. No version resource. |
| `cslol-diag.exe`  | 190,976 | `C58B62AA91F7FBA02D3F1D6F58434EA8B981AD5247ADF642550BF7A68BAF0D31` | Diagnostics helper. No version resource. |

Upstream project: <https://github.com/LeagueToolkit/cslol-manager> (MIT). Latest release
at time of writing: `2026-04-15-23f2308`, shipped as `cslol-manager-windows.exe`
(published SHA-256 `f528db8cf63ebd580886c747bff7ca2de69644307724738eea3de22ce8ea04ac`).
The project is in maintenance/deprecation mode. Official releases publish a checksum
only for the top-level package, **not** for the individual tools — so verifying these
four files means downloading the official package, verifying its published hash, then
extracting and hash-comparing the tools inside.

### Client loader — `Pengu Loader/`

| File | Size (bytes) | SHA-256 (as committed) | Notes |
|------|-------------:|------------------------|-------|
| `Pengu Loader.exe` | 2,552,440 | `0AEBE2AAD56AF05908048E22214EFD424B4E1EF6AB4E1230797D4574622AE4E7` | **⚠ Custom rebrand.** Version resource reports Product="Rose Loader", Company="ROSE", Version 2.0.0. |
| `core.dll`         |   505,464 | `280C894F800D4C00AE2363CCF2F55E63456CD6DE67341AA7B2709C737487679A` | Pengu Loader core (the injected `d3d9.dll` proxy payload). |
| `ModernWpf.Controls.dll` | 711,168 | `70BB5BB9B0268BE973D13EDCA5EECDDABBC07F58423C88C4F6EDA6BEDBCA8E99` | Third-party WPF UI library (open source, from NuGet). |
| `ModernWpf.dll`    |   924,160 | `DD9F01178911A942CBAB963D311C675C298D288A0079B5A9BB47FC86F1A74AC3` | Third-party WPF UI library. |
| `Ookii.Dialogs.Wpf.dll` | 104,448 | `C5C2B40EB870CF4F46E002A6C40656096CBBF7C062C19BC01CE26E503611553F` | Third-party WPF dialogs library. |
| `System.ValueTuple.dll` | 25,232 | `E905D102585B22C6DF04F219AF5CBDBFA7BC165979E9788B62DF6DCC165E10F4` | Microsoft BCL shim. |

Official Pengu Loader: <https://github.com/PenguLoader/PenguLoader> (LGPL/MIT), latest
**v1.1.6** (Dec 2024), code-signed via SignPath, actively maintained.

### Verified findings (2026-07-14)

Downloaded the official `pengu-loader-v1.1.6.zip`
(SHA-256 `D9AAFFD776A1594E4FB5EF060814C40CAB0CB4DE07F1F0CE3246E9C12EDA8836`) and compared:

- **The bundled `Pengu Loader.exe` + `core.dll` are code-signed by "Open Source Developer
  Alban CLIQUET" (Alban1911, the Rose author); signature status = Valid.** They are
  authentically the author's signed build and were not tampered with in transit.
- The bundle is a **rebrand of official Pengu Loader v1.1.6**: the shipped
  `ModernWpf.Controls.dll`, `ModernWpf.dll`, `Ookii.Dialogs.Wpf.dll`, and
  `System.ValueTuple.dll` are **byte-identical** to the official v1.1.6 release, and the
  official `Pengu Loader.exe`/`core.dll` are signed by SignPath Foundation.
- **The Rose build ADDS custom headless CLI flags** — `--force-activate`,
  `--force-deactivate`, `--set-league-path`, `--restart-client`, `--silent` — that Coral's
  `utils/integration/pengu_loader.py` depends on for automatic activation. **Official
  Pengu Loader v1.1.6 does NOT contain these flags** (only `--install`). Therefore a
  drop-in swap to the official binary would break Coral's auto-activation; using official
  Pengu Loader requires rewriting `pengu_loader.py` to its actual mechanism.

**Net:** the Pengu binary is not an opaque unknown — it is the Rose author's Authenticode-
signed fork of official Pengu Loader v1.1.6. Residual risk is trusting Alban's closed-source
modifications (the added CLI automation), not third-party malware injection.

### User-supplied injection DLL — `injection/tools/cslol-dll.dll`

Not committed (DMCA). Supplied by the user and **hash-pinned**: `main/__init__.py`
verifies it against a known-good SHA-256 before the app will start. This is the
best-controlled binary in the project and needs no change.

## Trust status

- **CSLOL tools (4 files):** Plausibly authentic CSLOL-manager artifacts, but *unverified*
  — no version resource and no per-file upstream checksum. Verify by hash against the
  official package before trusting.
- **`Pengu Loader.exe` + `core.dll`:** Custom "Rose Loader" fork — cannot be verified
  against any official release. Either replace with official Pengu Loader v1.1.6
  (code-signed; test that the CORAL-* plugins still load) or obtain and audit the fork's
  source and rebuild.
- **ModernWpf / Ookii / ValueTuple DLLs:** Standard open-source NuGet packages; verify
  against nuget.org package hashes if desired.

## Local rebuild feasibility (this machine, 2026-07-14)

Present: git, Node, npm, Rust/Cargo. **Absent: MSVC (cl), CMake, Qt (qmake), .NET/MSBuild.**
CSLOL-manager (C++/Qt) and Pengu Loader (C++/.NET-WPF) cannot be built here without
first installing Visual Studio Build Tools, the Qt SDK, and the .NET SDK. From-source
rebuild is therefore a separate, toolchain-dependent task.

## Recommended path

1. **Verify the 4 CSLOL tools** against the official cslol-manager package by hash. If they
   match, they are as trustworthy as upstream; record the verified hashes below. If they
   do not match, replace them with the extracted official tools.
2. **Replace `Pengu Loader.exe`/`core.dll`** with official Pengu Loader v1.1.6, or vendor
   and audit the Rose-Pengu fork source and rebuild. Confirm the `CORAL-*` plugins load
   after any swap.
3. Once each binary is from a source you trust, record its verified hash in the
   "verified upstream SHA-256" column (add it) and keep this file under version control so
   any future change to a binary is detectable in review.

_Do not download or run replacement binaries from unofficial mirrors. Use only the
official GitHub releases linked above, and verify published hashes/signatures first._
