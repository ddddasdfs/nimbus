#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin rights utilities for Windows
Handles elevation and Task Scheduler registration for auto-start

Security Notes:
    - subprocess calls use only trusted, hardcoded commands (schtasks)
    - sys.executable is used for elevation - points to current Python/frozen executable
    - No user input is passed directly to subprocess commands
    - All subprocess calls use CREATE_NO_WINDOW to prevent console flashing
"""

import sys
import ctypes
import subprocess
from pathlib import Path
from utils.core.logging import get_logger
from config import get_config_option

log = get_logger()


def is_admin():
    """Check if the current process has administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except (OSError, AttributeError) as e:
        log.debug(f"Failed to check admin status: {e}")
        return False


def request_admin_elevation():
    """
    Request administrator privileges by re-launching the application with elevation.
    This will show the UAC prompt.

    If the user accepts, an elevated instance is launched and the current
    (non-elevated) process exits. If the user declines the UAC prompt or
    elevation otherwise fails, this returns False WITHOUT exiting, so the caller
    can decide to continue unelevated.

    Returns:
        bool: False if already admin or elevation was declined/failed. On success
              the process exits and does not return.
    """
    if is_admin():
        return False

    # Get the path to the current executable or script
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        exe_path = sys.executable
        script_path = None
    else:
        # Running as Python script
        exe_path = sys.executable
        script_path = Path(sys.argv[0]).resolve()

    # Build the command line arguments
    params = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in sys.argv[1:]])
    if script_path is not None:
        params = f'"{script_path}" {params}'

    try:
        # Request elevation via ShellExecute with 'runas' verb.
        # ShellExecuteW returns a value > 32 on success; <= 32 indicates an
        # error, including 1223 (ERROR_CANCELLED) when the user declines UAC.
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            exe_path,
            params,
            None,
            1,  # SW_SHOWNORMAL
        )
    except Exception as e:
        log.error(f"Failed to request elevation: {e}")
        return False

    if int(ret) > 32:
        # Elevated instance launched successfully; quit this non-elevated one.
        sys.exit(0)

    log.warning(
        "Administrator elevation was declined or failed (ShellExecute code %s); "
        "continuing without admin.", ret
    )
    return False


def is_registered_for_autostart():
    """
    Check if the application is registered in Task Scheduler for auto-start
    
    Returns:
        bool: True if registered, False otherwise
    """
    try:
        result = subprocess.run(
            ['schtasks', '/Query', '/TN', 'nimbus'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, OSError) as e:
        log.debug(f"Failed to check autostart registration: {e}")
        return False


def register_autostart():
    """
    Register the application in Windows Task Scheduler to auto-start at logon with admin rights.
    This avoids UAC prompts on every startup.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not is_admin():
        return False, "Administrator privileges required to register auto-start"
    
    # Get the path to the executable
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
    else:
        exe_path = Path(sys.argv[0]).resolve()
    
    exe_dir = Path(exe_path).parent
    
    # Check if already registered
    if is_registered_for_autostart():
        return True, "Already registered for auto-start"
    
    try:
        # Create a scheduled task that runs at logon with highest privileges
        cmd = [
            'schtasks',
            '/Create',
            '/TN', 'nimbus',  # Task name
            '/TR', f'"{exe_path}"',  # Task to run
            '/SC', 'ONLOGON',  # Trigger: On user logon
            '/RL', 'HIGHEST',  # Run with highest privileges (admin)
            '/F'  # Force create (overwrite if exists)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0:
            return True, "Successfully registered for auto-start with admin rights"
        else:
            return False, f"Failed to register: {result.stderr}"
    
    except Exception as e:
        return False, f"Failed to register auto-start: {e}"


def unregister_autostart():
    """
    Remove the application from Windows Task Scheduler auto-start.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not is_admin():
        return False, "Administrator privileges required to unregister auto-start"
    
    # Check if registered
    if not is_registered_for_autostart():
        return True, "Not registered for auto-start"
    
    try:
        # Delete the scheduled task
        cmd = [
            'schtasks',
            '/Delete',
            '/TN', 'nimbus',  # Task name
            '/F'  # Force delete without confirmation
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0:
            return True, "Successfully unregistered from auto-start"
        else:
            return False, f"Failed to unregister: {result.stderr}"
    
    except Exception as e:
        return False, f"Failed to unregister auto-start: {e}"


def show_message_box_threaded(message: str, title: str, flags: int = 0x40):
    """
    Show a Windows MessageBox in a separate thread to ensure responsiveness.
    
    Args:
        message: The message text to display
        title: The title of the message box
        flags: MessageBox flags (default: MB_ICONINFORMATION)
    """
    import threading
    
    def show_dialog():
        """Show the dialog in a separate thread with proper message handling"""
        try:
            # Always add MB_SETFOREGROUND | MB_TOPMOST | MB_TASKMODAL for proper focus
            final_flags = flags | 0x10000 | 0x40000 | 0x2000
            ctypes.windll.user32.MessageBoxW(
                None,  # Use None for hwndOwner to create a top-level window
                message,
                title,
                final_flags
            )
        except Exception as e:
            log.error(f"Error showing message box '{title}': {e}")
    
    # Run the dialog in a separate daemon thread to avoid blocking
    dialog_thread = threading.Thread(target=show_dialog, daemon=True)
    dialog_thread.start()


def show_admin_required_dialog():
    """Show a dialog box explaining how admin rights are used (optional)."""
    show_message_box_threaded(
        "nimbus works best with Administrator privileges: they let it suspend the "
        "game process during injection, which makes skin injection more reliable.\n\n"
        "nimbus will now request elevation. You may click 'Yes' to grant it, or "
        "'No' to continue without admin (injection may be less reliable).\n\n"
        "To stop being asked, set request_admin=false under [General] in config.ini.",
        "Administrator Rights (optional)",
        0x30  # MB_ICONWARNING
    )


def show_autostart_success_dialog():
    """Show a dialog box confirming auto-start registration"""
    show_message_box_threaded(
        "nimbus will now start automatically when turn on your computer.",
        "Auto-Start Enabled",
        0x40  # MB_ICONINFORMATION
    )


def show_autostart_removed_dialog():
    """Show a dialog box confirming auto-start removal"""
    show_message_box_threaded(
        "nimbus has been removed from auto-start.\n\n"
        "The application will no longer start automatically with Windows.\n\n"
        "You can re-enable auto-start from the settings menu.",
        "Auto-Start Removed",
        0x40  # MB_ICONINFORMATION
    )


def ensure_admin_rights() -> bool:
    """
    Try to run with admin rights, but do NOT require them.

    nimbus only needs admin for one thing: suspending the game process during
    injection (which improves injection reliability). Rather than forcing the
    whole session to run elevated and quitting if the user declines, nimbus now
    treats admin as optional:

      * If already elevated, returns True.
      * Otherwise, unless disabled via config ([General] request_admin=false),
        it offers a UAC elevation prompt. Accepting relaunches elevated (this
        process exits inside request_admin_elevation). Declining is fine — the
        app continues unelevated in a limited mode.

    Returns:
        bool: True if running with admin rights, False if continuing unelevated.
    """
    if is_admin():
        return True

    # Allow users to opt out of the elevation prompt entirely.
    request_admin = (get_config_option("General", "request_admin", "true") or "true").strip().lower()
    if request_admin in ("0", "false", "no", "off"):
        log.warning(
            "Admin elevation is disabled via config ([General] request_admin). "
            "Running without administrator rights; game-process suspension during "
            "injection will be unavailable, which may make injection less reliable."
        )
        return False

    show_admin_required_dialog()
    request_admin_elevation()  # exits this process if the user accepts UAC

    # Reaching here means elevation was declined or failed. Continue unelevated.
    log.warning(
        "Continuing without administrator rights. Skin injection may be less "
        "reliable because nimbus cannot suspend the game process during injection. "
        "Run nimbus as administrator (or set [General] request_admin=true) to enable it."
    )
    return False
