#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for nimbus
"""

import argparse
import sys
from typing import Optional
from pathlib import Path

# Python version check
MIN_PYTHON = (3, 11)
if sys.version_info < MIN_PYTHON:
    raise RuntimeError(
        f"nimbus requires Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer. "
        "Please upgrade your interpreter and rebuild the application."
    )


def _get_tools_dir() -> Path:
    """Get the tools directory path (works in both frozen and development environments)"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable (PyInstaller)
        if hasattr(sys, '_MEIPASS'):
            # One-file mode: tools are in _MEIPASS
            base_path = Path(sys._MEIPASS)
            return base_path / "injection" / "tools"
        else:
            # One-dir mode: tools are alongside executable
            base_dir = Path(sys.executable).parent
            possible_dirs = [
                base_dir / "injection" / "tools",
                base_dir / "_internal" / "injection" / "tools",
            ]
            for dir_path in possible_dirs:
                if dir_path.exists():
                    return dir_path
            return possible_dirs[0]
    else:
        # Running as Python script
        return Path(__file__).parent.parent / "injection" / "tools"


_VALID_DLL_HASHES = {
    "4a009619c6dea691780b2f20cf17e08de478a78b3f11cd72759dd71c00ad1c90",
}


def _check_dll_hash(dll_path) -> bool:
    """Verify cslol-dll.dll matches a known-good SHA-256 hash."""
    import hashlib
    try:
        sha = hashlib.sha256()
        with open(dll_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest() in _VALID_DLL_HASHES
    except Exception:
        return False


def _dll_status(tools_dir) -> str:
    """Pure DLL-gate decision: 'ok' | 'missing' | 'invalid'. No dialogs, no side effects."""
    dll_path = tools_dir / "cslol-dll.dll"
    if not dll_path.exists():
        return "missing"
    return "ok" if _check_dll_hash(dll_path) else "invalid"


def _show_dll_dialog(tools_dir, status: str) -> str:
    """Show the DLL onboarding dialog. Returns 'open_folder' | 'continue' | 'cancel'.

    status: 'missing' (no file yet) or 'invalid' (present but wrong hash).
    Native TaskDialog with a MessageBox fallback. Distributes nothing; preserves the
    DMCA + Discord warnings.
    """
    import ctypes
    from ctypes import wintypes
    import webbrowser

    # Button ids
    IDCANCEL = 2
    ID_OPEN_FOLDER = 1000
    ID_CONTINUE = 1001

    # TaskDialog flags / notifications
    TDF_ENABLE_HYPERLINKS = 0x0001
    TDF_ALLOW_DIALOG_CANCELLATION = 0x0008
    TD_WARNING_ICON = 0xFFFF
    TDN_HYPERLINK_CLICKED = 3

    # Init common controls (required for TaskDialog)
    class INITCOMMONCONTROLSEX(ctypes.Structure):
        _fields_ = [("dwSize", ctypes.c_uint), ("dwICC", ctypes.c_uint)]

    icc = INITCOMMONCONTROLSEX()
    icc.dwSize = ctypes.sizeof(INITCOMMONCONTROLSEX)
    icc.dwICC = 0x000000FF  # ICC_WIN95_CLASSES
    ctypes.windll.comctl32.InitCommonControlsEx(ctypes.byref(icc))

    if status == "invalid":
        main_instruction = "DLL not recognized"
        content_text = (
            "The cslol-dll.dll you placed isn't the recognized build.\n\n"
            "It may be corrupted, outdated, or from an untrusted source. Replace it "
            "with the correct signed file, then click Continue.\n\n"
            "This file is NOT available on our Discord. Do not ask for it there.\n"
            "Asking for or sharing this file will result in a permanent ban.\n\n"
            "<a href=\"https://github.com/ddddasdfs/Nimbus\">https://github.com/ddddasdfs/Nimbus</a>"
        )
    else:  # missing
        main_instruction = "DLL file required"
        content_text = (
            "Due to DMCA restrictions, nimbus cannot distribute the cslol-dll.dll file.\n\n"
            "You must provide your own signed cslol-dll.dll file. Click Open Folder, "
            "place the file inside, then click Continue - no restart needed.\n\n"
            "This file is NOT available on our Discord. Do not ask for it there.\n"
            "Asking for or sharing this file will result in a permanent ban.\n\n"
            "<a href=\"https://github.com/ddddasdfs/Nimbus\">https://github.com/ddddasdfs/Nimbus</a>"
        )

    # Hyperlink callback (kept referenced to avoid GC)
    @ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM, ctypes.c_long)
    def _cb(hwnd, msg, wparam, lparam, refdata):
        if msg == TDN_HYPERLINK_CLICKED:
            try:
                webbrowser.open(ctypes.wstring_at(lparam))
            except Exception:
                pass
        return 0

    class TASKDIALOG_BUTTON(ctypes.Structure):
        _fields_ = [("nButtonID", ctypes.c_int), ("pszButtonText", wintypes.LPCWSTR)]

    class TASKDIALOGCONFIG(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_uint), ("hwndParent", wintypes.HWND),
            ("hInstance", wintypes.HINSTANCE), ("dwFlags", ctypes.c_uint),
            ("dwCommonButtons", ctypes.c_uint), ("pszWindowTitle", wintypes.LPCWSTR),
            ("pszMainIcon", wintypes.LPCWSTR), ("pszMainInstruction", wintypes.LPCWSTR),
            ("pszContent", wintypes.LPCWSTR), ("cButtons", ctypes.c_uint),
            ("pButtons", ctypes.POINTER(TASKDIALOG_BUTTON)), ("nDefaultButton", ctypes.c_int),
            ("cRadioButtons", ctypes.c_uint), ("pRadioButtons", ctypes.c_void_p),
            ("nDefaultRadioButton", ctypes.c_int), ("pszVerificationText", wintypes.LPCWSTR),
            ("pszExpandedInformation", wintypes.LPCWSTR), ("pszExpandedControlText", wintypes.LPCWSTR),
            ("pszCollapsedControlText", wintypes.LPCWSTR), ("pszFooterIcon", wintypes.LPCWSTR),
            ("pszFooter", wintypes.LPCWSTR), ("pfCallback", ctypes.c_void_p),
            ("lpCallbackData", ctypes.c_void_p), ("cxWidth", ctypes.c_uint),
        ]

    buttons = (TASKDIALOG_BUTTON * 3)()
    buttons[0].nButtonID = ID_OPEN_FOLDER
    buttons[0].pszButtonText = "Open Folder"
    buttons[1].nButtonID = ID_CONTINUE
    buttons[1].pszButtonText = "Continue"
    buttons[2].nButtonID = IDCANCEL
    buttons[2].pszButtonText = "Cancel"

    config = TASKDIALOGCONFIG()
    config.cbSize = ctypes.sizeof(TASKDIALOGCONFIG)
    config.hwndParent = None
    config.hInstance = None
    config.dwFlags = TDF_ENABLE_HYPERLINKS | TDF_ALLOW_DIALOG_CANCELLATION
    config.dwCommonButtons = 0
    config.pszWindowTitle = "nimbus - DLL Required"
    config.pszMainIcon = ctypes.cast(TD_WARNING_ICON, wintypes.LPCWSTR)
    config.pszMainInstruction = main_instruction
    config.pszContent = content_text
    config.cButtons = 3
    config.pButtons = ctypes.cast(buttons, ctypes.POINTER(TASKDIALOG_BUTTON))
    config.nDefaultButton = ID_OPEN_FOLDER if status == "missing" else ID_CONTINUE
    config.pfCallback = ctypes.cast(_cb, ctypes.c_void_p)
    config.lpCallbackData = 0
    config.cxWidth = 0

    pressed = ctypes.c_int(0)
    hr = ctypes.windll.comctl32.TaskDialogIndirect(
        ctypes.byref(config), ctypes.byref(pressed), None, None
    )

    if hr != 0:
        # Fallback: MessageBox (no Continue button available -> OK maps to open_folder,
        # so the user can still place the file; the loop re-checks on the next pass).
        fallback_text = content_text.replace(
            '<a href="https://github.com/ddddasdfs/Nimbus">https://github.com/ddddasdfs/Nimbus</a>',
            "",
        ) + "\nClick OK to open the folder; nimbus re-checks automatically - no restart needed."
        result = ctypes.windll.user32.MessageBoxW(
            0,
            fallback_text,
            "nimbus - DLL Required",
            0x40031,  # MB_OKCANCEL | MB_ICONWARNING | MB_SETFOREGROUND
        )
        return "open_folder" if result == 1 else "cancel"

    if pressed.value == ID_OPEN_FOLDER:
        return "open_folder"
    if pressed.value == ID_CONTINUE:
        return "continue"
    return "cancel"


def _check_dll_present() -> bool:
    """Gate startup on a valid cslol-dll.dll. Loops so the user can place the file and
    click Continue without relaunching. Returns True to boot, False to exit."""
    if sys.platform != "win32":
        return True  # Only relevant on Windows

    import subprocess

    tools_dir = _get_tools_dir()
    tools_dir.mkdir(parents=True, exist_ok=True)

    while True:
        status = _dll_status(tools_dir)
        if status == "ok":
            return True

        action = _show_dll_dialog(tools_dir, status)
        if action == "open_folder":
            try:
                subprocess.run(["explorer", str(tools_dir)], check=False)
            except Exception:
                pass
            # fall through -> loop re-shows; user places file then clicks Continue
        elif action == "continue":
            continue  # re-evaluate _dll_status at top
        else:  # "cancel"
            return False

# Setup console first (before any imports that might use it)
from .setup.console import setup_console, redirect_none_streams, start_console_buffer_manager
setup_console()
redirect_none_streams()
start_console_buffer_manager()

# Setup signal handlers
from .core.signals import setup_signal_handlers
setup_signal_handlers()

# Now import everything else
from .setup.arguments import setup_arguments
from .setup.initialization import setup_logging_and_cleanup, initialize_tray_manager
from .core.lockfile import check_single_instance
from .core.initialization import initialize_core_components
from .core.threads import initialize_threads
from .core.lcu_handler import create_lcu_disconnection_handler
from .core.cleanup import perform_cleanup
from .runtime.loop import run_main_loop

import utils.integration.pengu_loader as pengu_loader
from state import AppStatus
from utils.core.logging import get_logger, log_success
from utils.threading.thread_manager import create_daemon_thread
from config import APP_VERSION, MAIN_LOOP_FORCE_QUIT_TIMEOUT_S, set_config_option
from injection.config.config_manager import ConfigManager
from injection.game.game_detector import GameDetector
import time

log = get_logger()


def _setup_pengu_and_injection(lcu, injection_manager, activate_pengu: bool = True) -> None:
    """
    Detect and save leaguepath/clientpath, then setup Pengu Loader and injection system.

    Args:
        activate_pengu: If True, activate Pengu Loader (first startup).
                        If False, skip Pengu activation (reconnection after account swap).
    """
    log.info("Detecting League paths...")

    # Detect paths using GameDetector (only once)
    config_manager = ConfigManager()
    game_detector = GameDetector(config_manager)
    league_path, client_path = game_detector.detect_paths()

    if not league_path or not client_path:
        log.warning("Could not detect League paths, skipping setup")
        return

    # Save paths to config.ini
    log.info("Saving League paths to config.ini: league=%s, client=%s", league_path, client_path)
    config_manager.save_paths(str(league_path), str(client_path))

    # Verify paths are written to config.ini (with retries)
    max_verify_attempts = 5
    verify_interval = 0.2
    paths_verified = False

    for attempt in range(max_verify_attempts):
        saved_league_path = config_manager.load_league_path()
        saved_client_path = config_manager.load_client_path()

        if saved_league_path and saved_client_path:
            # Normalize paths for comparison
            saved_league_normalized = str(Path(saved_league_path).resolve())
            saved_client_normalized = str(Path(saved_client_path).resolve())
            league_normalized = str(league_path.resolve())
            client_normalized = str(client_path.resolve())

            if saved_league_normalized == league_normalized and saved_client_normalized == client_normalized:
                paths_verified = True
                log.info("Paths verified in config.ini")
                break

        if attempt < max_verify_attempts - 1:
            time.sleep(verify_interval)

    if not paths_verified:
        log.warning("Could not verify paths in config.ini, continuing anyway")

    # Set client path in Pengu Loader and activate (skip on reconnection)
    if activate_pengu:
        log.info("Setting client path in Pengu Loader and activating...")
        pengu_loader.activate_on_start(str(client_path))

    # Initialize injection system now (with detected paths already in config.ini)
    log.info("Initializing injection system...")
    injection_manager.initialize_when_ready()


def _update_registry_version() -> None:
    """Update the DisplayVersion in Windows registry to match the current app version.

    After an auto-update the Inno Setup registry entry still shows the version
    that was originally installed.  Writing the current ``APP_VERSION`` on every
    startup keeps "Apps & features" in sync.
    """
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return
    try:
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\nimbus"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
    except Exception:
        pass


def run_league_unlock(args: Optional[argparse.Namespace] = None,
                      injection_threshold: Optional[float] = None) -> None:
    """Run the core nimbus application startup and main loop."""
    # Check for single instance before doing anything else
    check_single_instance()

    # Keep the Windows "Apps & features" version in sync after auto-updates
    _update_registry_version()

    # Safety net: if a previous session didn't shut down cleanly, deactivate
    # Pengu Loader before we re-activate it later in the startup sequence.
    pengu_loader.cleanup_if_dirty()

    # Parse arguments if they were not provided
    if args is None:
        args = setup_arguments()
    
    # Setup logging and cleanup
    setup_logging_and_cleanup(args)

    # Clean up old Pengu Loader IFEO registry entry that can cause client crashes
    # This runs on every startup to handle both fresh installs and updates
    pengu_loader.cleanup_old_pengu_ifeo()

    # Initialize system tray manager immediately to hide console
    tray_manager = initialize_tray_manager(args)
    
    # Initialize app status manager
    app_status = AppStatus(tray_manager)
    log_success(log, "App status manager initialized", "")
    
    # Check initial status (will show locked until all components are ready)
    app_status.update_status(force=True)
    
    # Initialize core components
    lcu, skin_scraper, state, injection_manager = initialize_core_components(args, injection_threshold)
    
    # Configure skin writing based on the final injection threshold (seconds → ms)
    state.skin_write_ms = max(0, int(injection_manager.injection_threshold * 1000))
    state.inject_batch = getattr(args, 'inject_batch', state.inject_batch) or state.inject_batch
    
    # Create LCU disconnection handler
    on_lcu_disconnected = create_lcu_disconnection_handler(state, skin_scraper, app_status)

    # Create LCU reconnection handler. Riot's account-swap flow repairs the
    # client and wipes Pengu's d3d9.dll proxy, so the restarted UX never loads
    # plugins. Always re-activate Pengu to re-drop the proxy and trigger a
    # client restart.
    def on_lcu_reconnected():
        log.info("[Main] LCU reconnected after account swap - re-activating Pengu Loader...")
        try:
            _setup_pengu_and_injection(lcu, injection_manager, activate_pengu=False)
            client_path = ConfigManager().load_client_path()
            if client_path:
                pengu_loader.activate_on_start(str(client_path))
            else:
                log.warning("[Main] Cannot re-activate Pengu — client path unknown")
        except Exception as e:
            log.warning(f"[Main] Failed to re-initialize after reconnection: {e}")

    # Update tray manager quit callback now that state is available
    if tray_manager:
        def updated_tray_quit_callback():
            """Callback for tray quit - set the shared state stop flag"""
            log.info("Setting stop flag from tray quit")
            log.debug(f"[DEBUG] State before setting stop: {state.stop}")
            state.stop = True
            log.debug(f"[DEBUG] State after setting stop: {state.stop}")
            log.info("Stop flag set - main loop should exit")
            
            # Immediately try to trigger any pending console operations that might be blocking
            if sys.platform == "win32":
                try:
                    # Force a console input check to unblock any stuck operations
                    import msvcrt  # Windows-only module
                    if msvcrt.kbhit():
                        msvcrt.getch()  # Consume any pending input
                except (ImportError, OSError) as e:
                    log.debug(f"Console input check failed: {e}")
            
            # Add a timeout to force quit if main loop doesn't exit
            def force_quit_timeout():
                import time
                from .core.signals import force_quit_handler
                time.sleep(MAIN_LOOP_FORCE_QUIT_TIMEOUT_S)
                from .core.state import get_app_state
                app_state = get_app_state()
                if not app_state.shutting_down:
                    log.warning(f"Main loop did not exit within {MAIN_LOOP_FORCE_QUIT_TIMEOUT_S}s - forcing quit")
                    force_quit_handler()
            
            timeout_thread = create_daemon_thread(target=force_quit_timeout, 
                                                 name="ForceQuitTimeout")
            timeout_thread.start()
        
        tray_manager.quit_callback = updated_tray_quit_callback
    
    # Initialize threads (this starts the WebSocket server)
    thread_manager, t_phase, t_ui, t_ws, t_lcu_monitor = initialize_threads(
        lcu, state, args, injection_manager, skin_scraper, app_status, on_lcu_disconnected, on_lcu_reconnected
    )
    
    # Wait for WebSocket status to be active before activating Pengu Loader
    log.info("Waiting for WebSocket status to be active before activating Pengu Loader...")
    while not t_ws.connection.is_connected:
        time.sleep(0.1)
    
    log.info("WebSocket status is active, proceeding with Pengu Loader and injection system setup")
    
    # Setup Pengu Loader and injection system (LCU is already connected when WebSocket is active)
    _setup_pengu_and_injection(lcu, injection_manager)
    
    # Run main loop
    try:
        run_main_loop(state, skin_scraper)
    finally:
        # Perform cleanup
        perform_cleanup(state, thread_manager, tray_manager, injection_manager)


def main() -> None:
    """Program entry point that prepares and launches nimbus."""
    # Check for required DLL before anything else
    if not _check_dll_present():
        sys.exit(1)

    args = setup_arguments()
    if sys.platform == "win32":
        if not args.dev:
            try:
                from launcher import run_launcher
                run_launcher(
                    dev_mode=args.dev,
                    test_download_fail=getattr(args, 'test_download_fail', False),
                )
            except ModuleNotFoundError as err:
                print(f"[Launcher] Unable to import launcher module: {err}")
            except Exception as err:  # noqa: BLE001
                print(f"[Launcher] Launcher encountered an error: {err}")

    run_league_unlock(args=args)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Top-level exception handler to catch any unhandled crashes
        import traceback
        import ctypes
        try:
            from utils.core.issue_reporter import report_issue
            report_issue(
                "FATAL_CRASH",
                "error",
                "nimbus crashed unexpectedly.",
                details={"type": type(e).__name__, "error": str(e)},
                hint="Check %LOCALAPPDATA%\\nimbus\\logs\\ for details.",
            )
        except Exception:
            pass
        
        error_msg = f"""
================================================================================
FATAL ERROR - nimbus Crashed
================================================================================
Error: {e}
Type: {type(e).__name__}

Traceback:
{traceback.format_exc()}
================================================================================

This error has been logged. Please report this issue with the log file.
Log location: Check %LOCALAPPDATA%\\nimbus\\logs\\
================================================================================
"""
        
        # Try to log the error
        try:
            log = get_logger()
            log.error(error_msg)
        except (AttributeError, RuntimeError, OSError) as e:
            # If logging fails, print to stderr
            print(error_msg, file=sys.stderr)
            print(f"Logging system error: {e}", file=sys.stderr)
        
        # Show error dialog on Windows
        if sys.platform == "win32":
            try:
                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"nimbus crashed with an unhandled error:\n\n{str(e)}\n\nError type: {type(e).__name__}\n\nPlease check the log file in:\n%LOCALAPPDATA%\\nimbus\\logs\\",
                    "nimbus - Fatal Error",
                    0x50010  # MB_OK | MB_ICONERROR | MB_SETFOREGROUND | MB_TOPMOST
                )
            except Exception:
                pass
        
        sys.exit(1)

