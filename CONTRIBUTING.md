# Contributing to nimbus

Contributions are welcome! Report bugs or suggest features via GitHub Issues, or submit pull requests.

## Setting up dev environment

```powershell
# Create conda environment with Python 3.11
conda create -n nimbus python=3.11 -y

# Activate the environment
conda activate nimbus

# Clone the repository
git clone https://github.com/ddddasdfs/Nimbus.git

# Navigate to project directory
cd nimbus

# Create a feature branch (e.g. feat/skin-preview, fix/chroma-crash, docs/readme)
git checkout -b feat/your-feature-name

# Install all dependencies
pip install -r requirements.txt

# Ready to develop! Run main.py as administrator when testing
```

## Project Structure

```
nimbus/
├── main.py                 # Application entry point
├── config.py               # Configuration constants
├── requirements.txt        # Python dependencies
├── assets/                 # Application assets (icons, fonts, images)
│
├── main/                   # Main application package
│   ├── core/               # Core initialization and lifecycle
│   │   ├── initialization.py
│   │   ├── threads.py
│   │   ├── state.py
│   │   ├── signals.py
│   │   ├── lockfile.py
│   │   ├── lcu_handler.py
│   │   └── cleanup.py
│   ├── setup/              # Application setup and configuration
│   │   ├── console.py
│   │   ├── arguments.py
│   │   └── initialization.py
│   └── runtime/            # Main runtime loop
│       └── loop.py
│
├── injection/              # Skin injection system
│   ├── core/               # Core injection logic
│   │   ├── manager.py      # Injection manager & coordination
│   │   └── injector.py     # Skin injector
│   ├── game/               # Game detection and monitoring
│   │   ├── game_detector.py
│   │   └── game_monitor.py
│   ├── config/             # Configuration management
│   │   ├── config_manager.py
│   │   └── threshold_manager.py
│   ├── mods/               # Mod management
│   │   ├── mod_manager.py
│   │   └── zip_resolver.py
│   ├── overlay/            # Overlay process management
│   │   ├── overlay_manager.py
│   │   └── process_manager.py
│   └── tools/              # Injection tools (mod-tools.exe, etc.)
│       └── tools_manager.py
│
├── lcu/                    # League Client API integration
│   ├── core/               # Core LCU client components
│   │   ├── client.py       # Main LCU client orchestrator
│   │   ├── lcu_api.py      # LCU API wrapper
│   │   ├── lcu_connection.py
│   │   └── lockfile.py
│   ├── data/               # Data management
│   │   ├── skin_scraper.py
│   │   ├── skin_cache.py
│   │   ├── types.py
│   │   └── utils.py
│   └── features/           # LCU feature implementations
│       ├── lcu_properties.py
│       ├── lcu_skin_selection.py
│       ├── lcu_game_mode.py
│       └── lcu_swiftplay.py
│
├── threads/                # Background threads
│   ├── core/               # Core thread implementations
│   │   ├── websocket_thread.py
│   │   ├── phase_thread.py
│   │   └── lcu_monitor_thread.py
│   ├── handlers/            # Event handlers
│   │   ├── champ_thread.py
│   │   ├── champion_lock_handler.py
│   │   ├── game_mode_detector.py
│   │   ├── injection_trigger.py
│   │   ├── lobby_processor.py
│   │   ├── phase_handler.py
│   │   └── swiftplay_handler.py
│   ├── utilities/           # Thread utilities
│   │   ├── timer_manager.py
│   │   ├── loadout_ticker.py
│   │   └── skin_name_resolver.py
│   └── websocket/           # WebSocket components
│       ├── websocket_connection.py
│       └── websocket_event_handler.py
│
├── utils/                  # Utility modules
│   ├── core/               # Core utilities
│   │   ├── logging.py
│   │   ├── paths.py
│   │   ├── utilities.py
│   │   ├── validation.py
│   │   ├── normalization.py
│   │   ├── historic.py
│   │   ├── mod_historic.py
│   │   ├── issue_reporter.py
│   │   ├── junction.py
│   │   └── safe_extract.py
│   ├── crypto/             # Skin encryption
│   │   ├── skin_crypto.py
│   │   └── key_provider.py
│   ├── download/           # Download utilities
│   │   ├── skin_downloader.py
│   │   ├── smart_skin_downloader.py
│   │   ├── repo_downloader.py
│   │   ├── hashes_downloader.py
│   │   └── hash_updater.py
│   ├── integration/        # External integrations
│   │   ├── pengu_loader.py
│   │   ├── tray_manager.py
│   │   └── tray_settings.py
│   ├── system/             # System utilities
│   │   ├── admin_utils.py
│   │   ├── win32_base.py
│   │   ├── window_utils.py
│   │   └── resolution_utils.py
│   └── threading/          # Threading utilities
│       └── thread_manager.py
│
├── ui/                     # UI components
│   ├── core/               # Core UI management
│   │   ├── user_interface.py
│   │   └── lifecycle_manager.py
│   ├── chroma/             # Chroma selection UI
│   │   ├── selector.py
│   │   ├── ui.py
│   │   ├── panel.py
│   │   ├── preview_manager.py
│   │   ├── selection_handler.py
│   │   └── special_cases.py
│   └── handlers/           # UI feature handlers
│       ├── historic_mode_handler.py
│       ├── randomization_handler.py
│       └── skin_display_handler.py
│
├── pengu/                  # Pengu Loader integration
│   ├── core/               # Core Pengu functionality
│   │   ├── websocket_server.py
│   │   ├── http_handler.py
│   │   └── skin_monitor.py
│   ├── communication/      # Communication layer
│   │   ├── message_handler.py
│   │   └── broadcaster.py
│   └── processing/         # Data processing
│       ├── skin_processor.py
│       ├── skin_mapping.py
│       └── flow_controller.py
│
├── state/                  # Shared application state
│   └── core/
│       ├── shared_state.py
│       └── app_status.py
│
├── launcher/               # Application launcher (startup checks)
│   ├── core/
│   │   └── launcher.py     # Runs hash check + skin sync on startup (no auto-update)
│   ├── sequences/          # Launch sequences
│   │   ├── hash_check_sequence.py
│   │   └── skin_sync_sequence.py
│   ├── update/             # Auto-updater REMOVED in nimbus; only a no-op stub remains
│   │   └── update_sequence.py  # No-op (download/execute path + github_client deleted)
│   ├── ui/
│   │   └── update_dialog.py
│   └── updater.py          # No-op auto_update() kept for backward compatibility
│
├── party/                  # Party mode (skin sharing)
│   ├── core/               # Party orchestration
│   │   ├── party_manager.py  # Main party mode orchestrator
│   │   └── party_state.py
│   ├── network/            # Networking layer
│   │   ├── ws_relay.py     # WebSocket relay client
│   │   ├── peer_connection.py
│   │   ├── stun_client.py
│   │   └── udp_transport.py
│   ├── protocol/           # Wire protocol
│   │   ├── crypto.py       # XOR cipher with dynamic keys
│   │   ├── message_types.py
│   │   └── token_codec.py
│   ├── discovery/          # Lobby and skin discovery
│   │   ├── lobby_matcher.py
│   │   └── skin_collector.py
│   └── integration/        # UI and injection hooks
│       ├── injection_hook.py
│       └── ui_bridge.py
│
├── relay-worker/           # Cloudflare Worker — party relay (source kept for reference; party networking is disabled in this fork)
│   ├── src/
│   │   ├── index.ts        # Worker entry point
│   │   └── room.ts         # Durable Object party room
│   └── wrangler.toml
│
│   # NOTE: The upstream `analytics/` package was REMOVED in nimbus — no telemetry.
│
└── Pengu Loader/           # Pengu Loader and plugins
    ├── Pengu Loader.exe    # Pengu Loader executable
    └── plugins/            # JavaScript plugins
        ├── nimbus-UI/
        ├── nimbus-SkinMonitor/
        ├── nimbus-ChromaWheel/
        ├── nimbus-FormsWheel/
        ├── nimbus-CustomWheel/
        ├── nimbus-SettingsPanel/
        ├── nimbus-RandomSkin/
        ├── nimbus-HistoricMode/
        └── nimbus-PartyMode/   # UI only; party networking disabled
```
