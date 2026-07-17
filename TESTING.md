# nimbus — First-Run Safety Test

A step-by-step checklist for verifying, on real hardware, that nimbus behaves as the
audit expects: it talks only to the handful of hosts a skin changer needs, writes
only where it should, and doesn't re-introduce anything that was removed (analytics,
remote code, party relay). Run this the first time you build/run nimbus, and again
after any change to the download, injection, or Pengu integration code.

> Do this on a **VM or a spare machine**, not your daily driver. Skin injection is
> against Riot's ToS and carries ban risk; a throwaway Riot account and an isolated
> environment keep the blast radius small. Take a VM snapshot before you start so you
> can roll back.

---

## 0. What "pass" looks like

**Network — nimbus should only ever connect to:**

| Host | Why |
|------|-----|
| `api.github.com`, `github.com`, `codeload.github.com` | List/download skins (LeagueSkins, darkseal-org/lol-skins) |
| `raw.githubusercontent.com`, `objects.githubusercontent.com` | Raw skin files / release assets |
| `raw.communitydragon.org` | Game asset data + `hashes.game.txt` |
| `127.0.0.1` / `localhost` | Local bridge (ports ~50000-50010) and the LCU API |

**Red flags — if you EVER see these, something regressed. Stop and investigate:**

| Host | What it would mean |
|------|--------------------|
| `api.leagueunlocked.net` (or any `leagueunlocked.*`) | Analytics came back (should be deleted) |
| `unpkg.com` / any CDN loading `.js` | Jade-style remote code execution returned |
| `*.workers.dev` / any Cloudflare relay | Party-mode networking is no longer disabled |
| Any other unexpected domain/IP | Unknown egress — worth explaining before trusting the build |

> League of Legends and the Riot client generate their **own** traffic to Riot/Amazon
> servers while running. That is League, not nimbus — don't count it against nimbus. The
> point is to confirm *nimbus's* traffic matches the allowlist above.

**Files** — nimbus should only write under:
`%LOCALAPPDATA%\nimbus\...`, the **League install dir** (Pengu drops a `d3d9.dll` proxy
into the client folder — expected), and, only if you enable autostart, a Task Scheduler
task named `nimbus`. Nothing in `System32`, Startup folders, or unrelated locations.

---

## 1. Set up the isolated environment

- [ ] Fresh Windows 10/11 VM (or spare PC). Install League of Legends. Log in once with a **throwaway account**.
- [ ] Take a **VM snapshot** labelled "clean, pre-nimbus".
- [ ] Install monitoring tools (all free):
  - [ ] **Wireshark** — https://www.wireshark.org (network capture)
  - [ ] **TCPView** (Sysinternals) — per-process connections, easiest for attributing traffic to nimbus
  - [ ] **Process Monitor (Procmon)** (Sysinternals) — file/registry writes
  - [ ] (optional) **Process Explorer** (Sysinternals) — see child processes nimbus spawns

## 2. Build nimbus from the audited source

- [ ] Build on a **separate dev machine** (or the VM) from this repo — do not download a prebuilt nimbus.exe from anywhere.
- [ ] Provide your own signed `cslol-dll.dll` (nimbus hash-pins it; see the DLL prompt on first launch).
- [ ] Copy the build into the VM.

## 3. Static sanity re-check (30 seconds, before running)

From the repo root in the VM (or dev box), confirm the removed things are still gone:

- [ ] `grep -rniE "leagueunlocked|unpkg|workers\.dev" .` → no hits in code (only mentions should be in `SECURITY-BINARIES.md` / this file / audit notes).
- [ ] `analytics/` directory does **not** exist.
- [ ] `launcher/update/update_downloader.py` and `update_installer.py` do **not** exist.

## 4. Capture a clean baseline

- [ ] Start **Wireshark** capturing on the VM's network adapter. Apply this display filter to list only the hostnames things reach out to:
  ```
  tls.handshake.extensions_server_name or http.request or dns.qry.name
  ```
- [ ] Start **TCPView** and **Procmon**. In Procmon, set a filter: `Operation is WriteFile` (and later add `RegSetValue`) to reduce noise.
- [ ] Leave League **closed** for now.

## 5. Launch nimbus and watch startup

- [ ] Start nimbus.
- [ ] **Admin check:** it should offer a UAC prompt but **not force-quit if you decline**. Try declining once — nimbus should keep running (limited mode, logged). Then relaunch and accept, or set `[General] request_admin=false` in `%LOCALAPPDATA%\nimbus\config.ini` to skip the prompt.
- [ ] In **TCPView**, watch the nimbus process (`nimbus.exe` or `python.exe` for a source run). Every remote endpoint it opens should be on the Section 0 allowlist. Note anything that isn't.
- [ ] Startup will do a hash check + skin sync → expect GitHub / communitydragon connections. **No update-server contact** should occur (the auto-updater is gone).

## 6. Exercise the real features

With League open and nimbus running, drive the actual flow:

- [ ] Open the client; confirm the nimbus plugins load (settings panel, skin wheels).
- [ ] Hover/select skins in champion select (triggers the local bridge + possible skin download).
- [ ] Download a skin you don't own; start a game (Practice Tool / custom vs bots on the throwaway account) to trigger injection.
- [ ] Open the in-client Settings panel — confirm the **Discord/Ko-Fi buttons are gone**, only GitHub remains.
- [ ] If you want, toggle Party Mode in the UI — it should report **unavailable/disabled** and open **no** network connection (verify in TCPView: no `workers.dev`).

## 7. Review the captures — the actual verdict

- [ ] In **Wireshark**, look at the collected `server_name` / `dns.qry.name` values. Build the set of hosts nimbus's traffic touched. Every one should be on the allowlist. Search the capture explicitly:
  ```
  frame contains "leagueunlocked" or frame contains "unpkg" or frame contains "workers.dev"
  ```
  Expected result: **0 packets**.
- [ ] In **Procmon**, review WriteFile/RegSetValue events for the nimbus process. Confirm writes are confined to `%LOCALAPPDATA%\nimbus`, the League client dir (`d3d9.dll` proxy), and — only if you enabled autostart — the `nimbus` scheduled task. Flag anything else.
- [ ] Check `%LOCALAPPDATA%\nimbus\logs\` for the startup log: it should show the admin mode, hash/skin sync, and **no** analytics/updater activity.

## 8. Pass / fail

**PASS** if: every nimbus connection was on the allowlist; zero packets to the red-flag hosts;
file/registry writes stayed in the expected locations; declining admin didn't kill the app.

**INVESTIGATE** if: any unexpected host appears, any write lands outside the expected dirs,
or a red-flag domain shows up. Capture the details (host/IP, the Procmon stack) before trusting the build.

- [ ] When done, **restore the VM snapshot** to discard the League install and test account state.

---

*Companion docs: [`SECURITY-BINARIES.md`](SECURITY-BINARIES.md) (binary provenance) and the
"About this fork" section of [`README.md`](README.md) (what was changed and why).*
