# 🪸 Coral - Effortless Skin Changer for LoL

<div align="center">

  <img src="./assets/icon.png" alt="Coral Icon" width="128" height="128">

[![Installer](https://img.shields.io/badge/Installer-Windows-32A832)](https://github.com/ddddasdfs/Coral/releases/latest) [![License](https://img.shields.io/badge/License-MIT-C03030)](LICENSE) [![Downloads](https://img.shields.io/github/downloads/ddddasdfs/Coral/total?color=32A832&label=Downloads)](https://github.com/ddddasdfs/Coral/releases/latest)


</div>

---

## About this fork

**Coral is a security-hardened fork of [Rose](https://github.com/Alban1911/Rose) by Alban1911 and FlorentTariolle** (MIT-licensed). It keeps Rose's skin-changing functionality but removes or disables the components that reach outside the machine, so the app does only what a skin changer needs to. Relative to upstream Rose, this fork:

- **Removes analytics/telemetry entirely** — upstream sent a machine identifier to an external server every few minutes; Coral sends no usage data of any kind.
- **Removes the auto-updater's download-and-execute path** — upstream downloaded and ran GitHub releases as administrator with no signature/hash check; Coral never downloads or runs update code.
- **Hard-disables party mode networking** — no connection to any relay is made and no data leaves the machine.
- **Deletes the CORAL-Jade plugin** — it loaded remote JavaScript from a third-party CDN at runtime.
- **Hardens skin extraction** against path-traversal (zip-slip).
- **Makes administrator rights optional** — upstream forced the whole session to run elevated and quit if you declined. Coral only uses admin to suspend the game process during injection (a reliability aid); decline the UAC prompt to run unelevated in a limited mode, or set `request_admin=false` under `[General]` in `config.ini` to stop being asked.

## Overview

Coral is an open-source automatic skin changer for League of Legends that enables seamless access to all skins in the game. The application runs silently in the system tray and automatically detects skin selections during champion select, injecting the chosen skin when the game loads.

Built on the [Pengu Loader](https://github.com/PenguLoader/PenguLoader) framework, Coral integrates JavaScript extensions into the League Client to enable modular UI interactions. It strictly modifies local rendering variables to display custom models and textures. It is designed purely as an exploration of client-side asset management, providing no manipulation of network data, memory states, or gameplay mechanics, thereby **offering zero competitive advantage**.

## Architecture

Coral consists of three main components:

### Python Backend

- **LCU API Integration**: Communicates with the League Client via the League Client Update (LCU) API
- **Skin Injection**: Handles skin injection compatible with Riot Vanguard
- **WebSocket Bridge**: Operates a WebSocket server for real-time communication with frontend plugins
- **Skin Management**: Downloads and manages skin files from the [LeagueSkins repository](https://github.com/Alban1911/LeagueSkins)
- **Party Mode** *(disabled in this fork)*: Upstream enabled skin sharing between friends via a Cloudflare WebSocket relay. The code is retained but hard-disabled — no relay connection is ever made.
- **Game Monitoring**: Tracks game state, champion select phases, and loadout countdowns
- ~~**Auto-Updater**~~: *Removed in Coral.* Update by downloading a build you trust and verifying it yourself.
- ~~**Analytics**~~: *Removed in Coral.* No usage data is collected or sent.

### Cloudflare Workers

- **coral-party-relay** *(unused in this fork)*: The source for the Durable Object-backed WebSocket relay is kept for reference, but party networking is disabled, so Coral never connects to it.

### Pengu Loader Plugins

Coral includes a suite of JavaScript plugins that extend the League Client UI:

- **CORAL-UI**: Unlocks locked skin previews in champion select, enabling hover interactions on all skins
- **CORAL-SkinMonitor**: Monitors currently selected skin's name and sends it to the Python backend via WebSocket
- **CORAL-CustomWheel**: Displays custom mod metadata for hovered skins and exposes quick access to the mods folder
- **CORAL-ChromaWheel**: Enhanced chroma selection interface for choosing any chroma variant
- **CORAL-FormsWheel**: Custom form selection interface for skins with multiple forms (Elementalist Lux, Sahn Uzal Mordekaiser, Spirit Blossom Morgana, Radiant Sett)
- **CORAL-SettingsPanel**: Settings panel accessible from the League of Legends Client
- **CORAL-RandomSkin**: Random skin selection feature
- **CORAL-HistoricMode**: Access to the last used skin for every champion
- **CORAL-PartyMode**: Party mode UI panel *(party networking is disabled in this fork; the toggle reports party mode as unavailable)*

## How It Works

1. **League Client Integration**: Coral activates **[Pengu Loader](https://github.com/PenguLoader/PenguLoader)** on startup, which injects the JavaScript plugins into the League Client
2. **Skin Detection**: When you hover over a skin in champion select, `CORAL-SkinMonitor` detects the selection and sends it to the Python backend
3. **Game Opening Delay**: To make sure the injection has time to occur we suspend League of Legend's game process as long as the overlay is not ran
4. **Game Injection**: Coral injects the selected skin when the game starts
5. **Seamless Experience**: The skin loads as if you owned it, with full chroma support and no gameplay impact (Coral will **never** provide any competitive advantage to its users)

## Features

- **Smart Injection**: Never injects skins you already own
- **Multi-Language Support**: Works with any client language
- **Open Source**: Fully open source and extensible
- **Free**: If you bought this software, you got scammed 💀

## Requirements

- **Windows 10/11**
- **League of Legends** installed
- **Injection DLL** - You must provide your own signed DLL (see below)

### DLL Requirement

Due to DMCA restrictions, Coral cannot distribute the injection DLL file. You must obtain this file yourself from an authorized source and sign it with your own code signing certificate.

On first launch, Coral will prompt you to provide this file and open the folder where it should be placed.

## Installation

1. Download the latest installer from [Releases](https://github.com/ddddasdfs/Coral/releases/latest)
2. Run the installer as Administrator
3. Launch Coral from the Start Menu or desktop shortcut

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and project structure.

## Legal Disclaimer

This project is not endorsed by or affiliated with Riot Games. Riot Games and all related properties are trademarks or registered trademarks of Riot Games, Inc.

Custom skins are allowed under Riot's terms of service and are not detected. Do not discuss or advertise skin tools in game. Users proceed at their own risk.

---

**Coral** - _League, unlocked._
