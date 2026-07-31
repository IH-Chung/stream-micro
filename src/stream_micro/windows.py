"""Legacy Windows foreground-window bindings for non-OpenChamber plugins."""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes


class WindowCaptureError(RuntimeError):
    pass


def foreground_window_binding() -> dict[str, str]:
    """Return a stable, display-safe identity for the active Windows window."""

    if os.name != "nt":
        raise WindowCaptureError("Window binding is available only on Windows")
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        raise WindowCaptureError("No foreground window is available")
    title = ctypes.create_unicode_buffer(1024)
    window_class = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, title, len(title))
    user32.GetClassNameW(hwnd, window_class, len(window_class))
    process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    if not process_id.value:
        raise WindowCaptureError("Could not identify the foreground window process")
    process = kernel32.OpenProcess(0x1000, False, process_id.value)
    if not process:
        raise WindowCaptureError("Could not inspect the foreground window process")
    try:
        executable = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(executable))
        if not kernel32.QueryFullProcessImageNameW(process, 0, executable, ctypes.byref(size)):
            raise WindowCaptureError("Could not read the foreground window executable")
    finally:
        kernel32.CloseHandle(process)
    if not title.value or not window_class.value:
        raise WindowCaptureError("Foreground window has no usable title or class")
    return {
        "executable": executable.value,
        "window_class": window_class.value,
        "title_pattern": title.value,
    }


def focus_window_binding(binding: dict[str, str]) -> None:
    """Focus the first visible top-level window matching a confirmed binding."""

    if os.name != "nt":
        raise WindowCaptureError("Window focusing is available only on Windows")
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    target_executable = binding["executable"].casefold()
    target_class = binding["window_class"]
    target_title = binding["title_pattern"].casefold()
    found: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def check(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        title = ctypes.create_unicode_buffer(1024)
        window_class = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title, len(title))
        user32.GetClassNameW(hwnd, window_class, len(window_class))
        if window_class.value != target_class or target_title not in title.value.casefold():
            return True
        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        process = kernel32.OpenProcess(0x1000, False, process_id.value)
        if not process:
            return True
        try:
            executable = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(executable))
            if not kernel32.QueryFullProcessImageNameW(process, 0, executable, ctypes.byref(size)):
                return True
        finally:
            kernel32.CloseHandle(process)
        if executable.value.casefold() == target_executable:
            found.append(hwnd)
            return False
        return True

    callback = callback_type(check)
    user32.EnumWindows(callback, 0)
    if not found:
        raise WindowCaptureError("The bound Windows window is not currently open")
    _activate_window(found[0], "The bound Windows window")


def _activate_window(hwnd: int, label: str) -> None:
    """Focus a window from Bridge's background HID callback thread."""

    user32 = ctypes.windll.user32
    foreground = user32.GetForegroundWindow()
    foreground_thread = user32.GetWindowThreadProcessId(foreground, None) if foreground else 0
    target_thread = user32.GetWindowThreadProcessId(hwnd, None)
    attached = False
    if foreground_thread and target_thread and foreground_thread != target_thread:
        attached = bool(user32.AttachThreadInput(foreground_thread, target_thread, True))
    try:
        # Restore only minimized windows; preserve a user's maximized size.
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.BringWindowToTop(hwnd)
        if not user32.SetForegroundWindow(hwnd):
            raise WindowCaptureError(f"Windows did not allow {label.lower()} to be focused")
    finally:
        if attached:
            user32.AttachThreadInput(foreground_thread, target_thread, False)
