# 🌹 Rose - Effortless Skin Changer for LoL

<div align="center">

  <img src="./assets/icon.png" alt="Rose Icon" width="128" height="128">

[![Installer](https://img.shields.io/badge/Installer-Windows-32A832)](https://github.com/Alban1911/Rose/releases/latest) [![Ko-Fi](https://img.shields.io/badge/KoFi-Donate-C03030?logo=ko-fi&logoColor=white)](https://ko-fi.com/roseapp) [![Discord](https://img.shields.io/discord/1465467335946272780?color=32A832&logo=discord&logoColor=white&label=Discord)](https://discord.com/invite/roseapp) [![License](https://img.shields.io/badge/License-Open%20Source-C03030)](LICENSE) [![Downloads](https://img.shields.io/github/downloads/Alban1911/Rose/total?color=32A832&label=Downloads)](https://github.com/Alban1911/Rose/releases/latest)


</div>

---

## Overview

Rose is an open-source automatic skin changer for League of Legends that enables seamless access to all skins in the game. The application runs silently in the system tray and automatically detects skin selections during champion select, injecting the chosen skin when the game loads.

**Rose is built on Pengu Loader**, a plugin system that injects JavaScript plugins into the League Client, enabling enhanced UI interactions and quick skin detection.

## Architecture

Rose consists of three main components:

### Python Backend

- **LCU API Integration**: Communicates with the League Client via the League Client Update (LCU) API
- **Skin Injection**: Handles skin injection compatible with Riot Vanguard
- **WebSocket Bridge**: Operates a WebSocket server for real-time communication with frontend plugins
- **Skin Management**: Downloads and manages encrypted skin files from the [RoseSkins repository](https://github.com/Alban1911/RoseSkins) — files are decrypted at runtime and wiped after use
- **Party Mode**: Enables skin sharing between friends in the same lobby via a Cloudflare WebSocket relay
- **Game Monitoring**: Tracks game state, champion select phases, and loadout countdowns
- **Analytics**: Sends periodic pings to track unique users (configurable, runs in background thread)

### Cloudflare Workers

- **rose-party-relay**: Durable Object-backed WebSocket relay that manages party rooms (max 10 members per room) for real-time skin selection broadcasting between friends
- **rose-skin-key**: Serves the skin decryption key at runtime

### Pengu Loader Plugins

Rose includes a suite of JavaScript plugins that extend the League Client UI:

- **ROSE-UI**: Unlocks locked skin previews in champion select, enabling hover interactions on all skins
- **ROSE-SkinMonitor**: Monitors currently selected skin's name and sends it to the Python backend via WebSocket
- **ROSE-CustomWheel**: Displays custom mod metadata for hovered skins and exposes quick access to the mods folder
- **ROSE-ChromaWheel**: Enhanced chroma selection interface for choosing any chroma variant
- **ROSE-FormsWheel**: Custom form selection interface for skins with multiple forms (Elementalist Lux, Sahn Uzal Mordekaiser, Spirit Blossom Morgana, Radiant Sett)
- **ROSE-SettingsPanel**: Settings panel accessible from the League of Legends Client
- **ROSE-RandomSkin**: Random skin selection feature
- **ROSE-HistoricMode**: Access to the last used skin for every champion
- **ROSE-PartyMode**: Party mode UI — displays a panel in lobby and champion select to enable skin sharing, view connected peers, and see friends' skin selections in real time

## How It Works

1. **League Client Integration**: Rose activates **Pengu Loader** on startup, which injects the JavaScript plugins into the League Client
2. **Skin Detection**: When you hover over a skin in champion select, `ROSE-SkinMonitor` detects the selection and sends it to the Python backend
3. **Game Opening Delay**: To make sure the injection has time to occur we suspend League of Legend's game process as long as the overlay is not ran
4. **Game Injection**: Rose decrypts and injects the selected skin when the game starts
6. **Seamless Experience**: The skin loads as if you owned it, with full chroma support and no gameplay impact (**Rose will never provide any competitive advantage to its users**)

## Features

- **Automatic Skin Detection**: Detects skin selections through hover events in champion select
- **All Skins Accessible**: Access to every skin for every champion
- **Chroma Support**: Select any chroma variant through the enhanced UI
- **Party Mode**: Share skins with friends — see each other's selected skins in the same lobby via a secure WebSocket relay
- **Random Skin Mode**: Automatically select random skins
- **Historic Mode**: Access last used skin on every champion
- **Custom Mod Insights**: ROSE-CustomWheel surfaces installed mods relevant to the skin you're hovering over, along with timestamps and quick folder access
- **Encrypted Skin Files**: Skins are encrypted and only decrypted at injection time
- **Smart Injection**: Never injects skins you already own
- **Safe & Compatible**: Injection method compatible with Riot Vanguard
- **Multi-Language Support**: Works with any client language
- **Open Source**: Fully open source and extensible
- **Free**: If you bought this software, you got scammed 💀

## Requirements

- **Windows 10/11**
- **League of Legends** installed
- **Injection DLL** - You must provide your own signed DLL (see below)

### DLL Requirement

Due to DMCA restrictions, Rose cannot distribute the injection DLL file. You must obtain this file yourself from an authorized source and sign it with your own code signing certificate.

On first launch, Rose will prompt you to provide this file and open the folder where it should be placed.

## Installation

1. Download the latest installer from [Releases](https://github.com/Alban1911/Rose/releases/latest)
2. Run the installer as Administrator
3. Launch Rose from the Start Menu or desktop shortcut

## Setting up dev environment

```powershell
# Create conda environment with Python 3.11
conda create -n rose python=3.11 -y

# Activate the environment
conda activate rose

# Clone the repository
git clone https://github.com/Alban1911/Rose.git

# Navigate to project directory
cd Rose

# Switch to dev branch
git checkout dev

# Install all dependencies
pip install -r requirements.txt

# Ready to develop! Run main.py as administrator when testing
```

## Project Structure

```
Rose/
├── main.py                 # Application entry point
├── config.py              # Configuration constants
├── requirements.txt        # Python dependencies
├── assets/                 # Application assets (icons, fonts, images)
│
├── main/                   # Main application package
│   ├── core/              # Core initialization and lifecycle
│   │   ├── initialization.py
│   │   ├── threads.py
│   │   ├── state.py
│   │   ├── signals.py
│   │   ├── lockfile.py
│   │   ├── lcu_handler.py
│   │   └── cleanup.py
│   ├── setup/             # Application setup and configuration
│   │   ├── console.py
│   │   ├── arguments.py
│   │   └── initialization.py
│   └── runtime/           # Main runtime loop
│       └── loop.py
│
├── injection/             # Skin injection system
│   ├── core/              # Core injection logic
│   │   ├── manager.py    # Injection manager & coordination
│   │   └── injector.py   # Skin injector
│   ├── game/              # Game detection and monitoring
│   │   ├── game_detector.py
│   │   └── game_monitor.py
│   ├── config/            # Configuration management
│   │   ├── config_manager.py
│   │   └── threshold_manager.py
│   ├── mods/              # Mod management
│   │   ├── mod_manager.py
│   │   └── zip_resolver.py
│   ├── overlay/           # Overlay process management
│   │   ├── overlay_manager.py
│   │   └── process_manager.py
│   └── tools/             # Injection tools (mod-tools.exe, etc.)
│       └── tools_manager.py
│
├── lcu/                   # League Client API integration
│   ├── core/              # Core LCU client components
│   │   ├── client.py      # Main LCU client orchestrator
│   │   ├── lcu_api.py     # LCU API wrapper
│   │   ├── lcu_connection.py
│   │   └── lockfile.py
│   ├── data/              # Data management
│   │   ├── skin_scraper.py
│   │   ├── skin_cache.py
│   │   ├── types.py
│   │   └── utils.py
│   └── features/          # LCU feature implementations
│       ├── lcu_properties.py
│       ├── lcu_skin_selection.py
│       ├── lcu_game_mode.py
│       └── lcu_swiftplay.py
│
├── threads/               # Background threads
│   ├── core/              # Core thread implementations
│   │   ├── websocket_thread.py
│   │   ├── phase_thread.py
│   │   └── lcu_monitor_thread.py
│   ├── handlers/         # Event handlers
│   │   ├── champ_thread.py
│   │   ├── champion_lock_handler.py
│   │   ├── game_mode_detector.py
│   │   ├── injection_trigger.py
│   │   ├── lobby_processor.py
│   │   ├── phase_handler.py
│   │   └── swiftplay_handler.py
│   ├── utilities/         # Thread utilities
│   │   ├── timer_manager.py
│   │   ├── loadout_ticker.py
│   │   └── skin_name_resolver.py
│   └── websocket/         # WebSocket components
│       ├── websocket_connection.py
│       └── websocket_event_handler.py
│
├── utils/                 # Utility modules
│   ├── core/              # Core utilities
│   │   ├── logging.py
│   │   ├── paths.py
│   │   ├── utilities.py
│   │   ├── validation.py
│   │   ├── normalization.py
│   │   └── historic.py
│   ├── crypto/            # Skin encryption
│   │   ├── skin_crypto.py
│   │   └── key_provider.py
│   ├── download/          # Download utilities
│   │   ├── skin_downloader.py
│   │   ├── smart_skin_downloader.py
│   │   ├── repo_downloader.py
│   │   ├── hashes_downloader.py
│   │   └── hash_updater.py
│   ├── integration/       # External integrations
│   │   ├── pengu_loader.py
│   │   ├── tray_manager.py
│   │   └── tray_settings.py
│   ├── system/            # System utilities
│   │   ├── admin_utils.py
│   │   ├── win32_base.py
│   │   ├── window_utils.py
│   │   └── resolution_utils.py
│   └── threading/         # Threading utilities
│       └── thread_manager.py
│
├── ui/                    # UI components
│   ├── core/              # Core UI management
│   │   ├── user_interface.py
│   │   └── lifecycle_manager.py
│   ├── chroma/            # Chroma selection UI
│   │   ├── selector.py
│   │   ├── ui.py
│   │   ├── panel.py
│   │   ├── preview_manager.py
│   │   ├── selection_handler.py
│   │   └── special_cases.py
│   └── handlers/          # UI feature handlers
│       ├── historic_mode_handler.py
│       ├── randomization_handler.py
│       └── skin_display_handler.py
│
├── pengu/                 # Pengu Loader integration
│   ├── core/              # Core Pengu functionality
│   │   ├── websocket_server.py
│   │   ├── http_handler.py
│   │   └── skin_monitor.py
│   ├── communication/     # Communication layer
│   │   ├── message_handler.py
│   │   └── broadcaster.py
│   └── processing/        # Data processing
│       ├── skin_processor.py
│       ├── skin_mapping.py
│       └── flow_controller.py
│
├── state/                 # Shared application state
│   └── core/
│       ├── shared_state.py
│       └── app_status.py
│
├── launcher/              # Application launcher and updater
│   ├── core/
│   │   └── launcher.py
│   ├── sequences/         # Launch sequences
│   │   ├── hash_check_sequence.py
│   │   └── skin_sync_sequence.py
│   ├── update/            # Update system
│   │   ├── update_sequence.py
│   │   ├── update_downloader.py
│   │   ├── update_installer.py
│   │   └── github_client.py
│   ├── ui/
│   │   └── update_dialog.py
│   └── updater.py
│
├── party/                 # Party mode (skin sharing)
│   ├── core/              # Party orchestration
│   │   ├── party_manager.py  # Main party mode orchestrator
│   │   └── party_state.py
│   ├── network/           # Networking layer
│   │   ├── ws_relay.py    # WebSocket relay client
│   │   ├── peer_connection.py
│   │   ├── stun_client.py
│   │   └── udp_transport.py
│   ├── protocol/          # Wire protocol
│   │   ├── crypto.py      # XOR cipher with dynamic keys
│   │   ├── message_types.py
│   │   └── token_codec.py
│   ├── discovery/         # Lobby and skin discovery
│   │   ├── lobby_matcher.py
│   │   └── skin_collector.py
│   └── integration/       # UI and injection hooks
│       ├── injection_hook.py
│       └── ui_bridge.py
│
├── relay-worker/          # Cloudflare Worker — party relay
│   ├── src/
│   │   ├── index.ts       # Worker entry point
│   │   └── room.ts        # Durable Object party room
│   └── wrangler.toml
│
├── skin-key-worker/       # Cloudflare Worker — skin key server
│   ├── src/
│   │   └── index.ts
│   └── wrangler.toml
│
├── analytics/             # Analytics and user tracking
│   └── core/
│       ├── machine_id.py  # Machine ID retrieval (Windows Machine GUID)
│       ├── analytics_client.py  # HTTP client for analytics pings
│       └── analytics_thread.py  # Background thread for periodic pings
│
└── Pengu Loader/          # Pengu Loader and plugins
    ├── Pengu Loader.exe   # Pengu Loader executable
    └── plugins/           # JavaScript plugins
        ├── ROSE-UI/
        ├── ROSE-SkinMonitor/
        ├── ROSE-ChromaWheel/
        ├── ROSE-FormsWheel/
        ├── ROSE-CustomWheel/
        ├── ROSE-SettingsPanel/
        ├── ROSE-RandomSkin/
        ├── ROSE-HistoricMode/
        └── ROSE-PartyMode/
```

## Development

### Key Technologies

- **Python 3.11+**: Backend application
- **Pengu Loader**: Plugin system for League Client
- **LCU API**: League Client communication
- **WebSocket**: Real-time frontend-backend communication
- **Cloudflare Workers + Durable Objects**: Party relay and skin key server
- **JavaScript/HTML/CSS**: Client UI plugins

### Contributing

Rose is open source! Contributions are welcome:

- Report bugs or suggest features via GitHub Issues
- Submit pull requests for improvements
- Join our [Discord](https://discord.com/invite/roseapp) for discussions

## Legal Disclaimer

**Important**: This project is not endorsed by Riot Games and does not represent the views or opinions of Riot Games or any of its affiliates. Riot Games and all related properties are trademarks or registered trademarks of Riot Games, Inc.

The use of custom skin tools may violate Riot Games' Terms of Service. Users proceed at their own risk.

Custom skins are allowed under Riot's terms of service and do not trigger detection as long as you are not discussing or advertising the use of the skins within the game.

## Support

If you enjoy Rose and want to support its development:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/roseapp)

Your support helps keep the project alive and motivates continued development!

---

**Rose** - _League, unlocked._
