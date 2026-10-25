"""Автозапуск Windows (реестр текущего пользователя)."""
import os, sys

KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
NAME = "VoiceAssistant"

def set_autostart(enabled):
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY, 0, winreg.KEY_SET_VALUE) as k:
        if enabled:
            if getattr(sys, "frozen", False):
                cmd = f'"{sys.executable}"'
            else:
                main = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
                cmd = f'"{sys.executable.replace("python.exe", "pythonw.exe")}" "{main}"'
            winreg.SetValueEx(k, NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(k, NAME)
            except FileNotFoundError:
                pass
