"""ЭТАП 5: установка/удаление ПО, громкость, яркость, настройки; память, секреты, план задач."""
import os, subprocess
from .tools import tool
from . import memory, secrets_store

def _winget(args, timeout=1500):
    try:
        r = subprocess.run(["winget"] + args + ["--accept-source-agreements"], capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace", creationflags=0x08000000)
        return r.returncode, (r.stdout + r.stderr).strip()[-500:]
    except FileNotFoundError:
        return 1, "winget не найден (нужна Windows 10 1809+ с «Установщиком приложений»)"
    except subprocess.TimeoutExpired:
        return 1, "Слишком долго, остановлено"

@tool("install_program", "Установить программу через winget (требует подтверждения)", {"name": "название программы или id в winget"}, ["name"],
      danger=lambda a: f"Установить программу «{a.get('name')}»? Windows может дополнительно запросить разрешение.")
def install_program(name):
    code, out = _winget(["install", name, "--accept-package-agreements", "--silent"])
    return f"Установлено: {name}" if code == 0 else f"Ошибка установки: {out}"

@tool("uninstall_program", "Удалить программу через winget (требует подтверждения)", {"name": "название программы"}, ["name"],
      danger=lambda a: f"Удалить программу «{a.get('name')}»? Это необратимо.")
def uninstall_program(name):
    code, out = _winget(["uninstall", name, "--silent"])
    return f"Удалено: {name}" if code == 0 else f"Ошибка удаления: {out}"

@tool("set_volume", "Установить громкость 0–100%", {"percent": ("integer", "громкость в процентах")}, ["percent"])
def set_volume(percent):
    import pyautogui
    pct = max(0, min(100, int(percent)))
    pyautogui.press("volumedown", presses=50, interval=0.005)
    pyautogui.press("volumeup", presses=round(pct / 2), interval=0.005)
    return f"Громкость около {pct}%"

@tool("set_brightness", "Установить яркость экрана 0–100% (работает на ноутбуках)", {"percent": ("integer", "яркость в процентах")}, ["percent"])
def set_brightness(percent):
    pct = max(0, min(100, int(percent)))
    cmd = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{pct})"
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, creationflags=0x08000000)
    return f"Яркость {pct}%" if r.returncode == 0 else "Ошибка: яркость этого экрана не управляется программно (обычно внешние мониторы)"

SETTINGS = {"bluetooth": "bluetooth", "блютуз": "bluetooth", "wifi": "network-wifi", "вайфай": "network-wifi", "wi-fi": "network-wifi",
            "звук": "sound", "экран": "display", "обновления": "windowsupdate", "приложения": "appsfeatures",
            "принтеры": "printers", "сеть": "network"}

@tool("open_settings", "Открыть раздел настроек Windows (bluetooth, wifi, звук, экран, обновления, приложения, принтеры)", {"page": "раздел"}, ["page"])
def open_settings(page):
    os.startfile("ms-settings:" + SETTINGS.get(page.strip().lower(), page.strip()))
    return f"Открыты настройки: {page}. Переключатели Windows защищены от автоматизации, нажмите нужный выключатель сами."

# ---------- память, секреты, план ----------
@tool("remember", "Запомнить предпочтение или факт о пользователе надолго", {"key": "ключ, например 'любимый браузер'", "value": "значение"}, ["key", "value"])
def remember(key, value):
    memory.remember(key, value)
    return f"Запомнил: {key} = {value}"

@tool("recall", "Вспомнить сохранённые предпочтения (по части ключа или все)", {"key": "часть ключа, необязательно"})
def recall(key=""):
    r = memory.recall(key)
    return "; ".join(f"{k}: {v}" for k, v in r) if r else "Ничего не сохранено"

@tool("forget", "Забыть сохранённое предпочтение", {"key": "точный ключ"}, ["key"])
def forget(key):
    return "Забыл" if memory.forget(key) else "Такого нет"

@tool("save_secret", "Сохранить логин и пароль в зашифрованное хранилище Windows (DPAPI)",
      {"name": "имя записи, например 'почта'", "login": "логин", "password": "пароль"}, ["name", "login", "password"])
def save_secret(name, login, password):
    secrets_store.save(name, login, password)
    return f"Данные «{name}» сохранены в зашифрованном виде. Пароль нигде не отображается."

@tool("propose_plan", "Для СЛОЖНЫХ задач (более 4 шагов): показать краткий план и получить согласие до выполнения",
      {"plan": "краткий план одним-двумя предложениями"}, ["plan"],
      danger=lambda a: f"Мой план: {a.get('plan')} Выполнять?")
def propose_plan(plan):
    return "План подтверждён пользователем. Выполняй шаги."
