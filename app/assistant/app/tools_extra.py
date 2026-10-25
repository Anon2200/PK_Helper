"""Дополнительные инструменты: корзина, системная информация, часы/таймер, буфер обмена, батарея."""
import datetime as _dt
from .tools import tool


class _Shell:
    """Ленинный доступ к shell32 (чтобы модуль импортировался и вне Windows)."""
    def __getattr__(self, name):
        import ctypes
        return getattr(ctypes.windll.shell32, name)

_SHELL = _Shell()

# Оркестратор вызывает set_notifier(...), чтобы таймеры могли разбудить ассистента.
_NOTIFY = lambda title, text: None

def set_notifier(fn):
    global _NOTIFY
    _NOTIFY = fn

_TIMERS = []   # [(datetime_когда, текст), ...] — обрабатывает поток таймеров в assistant.py

@tool("empty_recycle_bin", "Очистить корзину Windows (требует подтверждения)", {}, [],
      danger=lambda a: "Очистить корзину? Восстановить файлы будет нельзя.")
def empty_recycle_bin():
    try:
        r = _SHELL.SHEmptyRecycleBinW(None, None, 0x0007)  # без диалогов и звука
        if r in (0, -2147418113, -2147024894):   # S_OK или корзина уже пуста
            return "Корзина очищена (или уже была пуста)."
        return f"Корзина не очищена, код Windows: {r}"
    except Exception as e:
        return f"Ошибка: {e}"

@tool("system_info", "Показать информацию о компьютере: ОС, процессор, память, диски. Для вопроса «какой у меня компьютер»")
def system_info():
    try:
        import psutil, platform, shutil as _sh
        vm = psutil.virtual_memory()
        disks = []
        for p in psutil.disk_partitions():
            try:
                u = _sh.disk_usage(p.mountpoint)
                disks.append(f"{p.device}: всего {u.total/1e9:.0f} ГБ, свободно {u.free/1e9:.0f} ГБ")
            except OSError:
                continue
        cpu = platform.processor() or ""
        return (f"Windows {platform.release()} ({platform.version()}), {cpu} ядер: {psutil.cpu_count()}, "
                f"память {vm.total/1e9:.0f} ГБ (свободно {vm.available/1e9:.0f} ГБ). Диски: " + "; ".join(disks))
    except Exception as e:
        return f"Ошибка: {e}"

@tool("get_time", "Сказать текущие дату и время")
def get_time():
    return _dt.datetime.now().strftime("%d.%m.%Y %H:%M")

@tool("set_timer", "Таймер/напоминание: через N минут ассистент подаст сигнал и покажет окно с напоминанием",
      {"minutes": ("number", "через сколько минут"), "message": "о чём напомнить"}, ["minutes"])
def set_timer(minutes, message="Напоминание"):
    try:
        m = float(minutes)
    except (TypeError, ValueError):
        return "Ошибка: минуты должны быть числом"
    if not 0.1 <= m <= 60 * 24:
        return "Ошибка: значение от 0.1 минуты (6 секунд) до 24 часов"
    when = _dt.datetime.now() + _dt.timedelta(minutes=m)
    _TIMERS.append((when, str(message)))
    return f"Таймер на {when.strftime('%H:%M')} ({m:g} мин): {message}"

@tool("list_timers", "Показать активные таймеры и напоминания")
def list_timers():
    if not _TIMERS:
        return "Активных таймеров нет"
    return "Таймеры: " + "; ".join(f"{w.strftime('%H:%M')} {m}" for w, m in sorted(_TIMERS))

@tool("clipboard_read", "Прочитать текст из буфера обмена")
def clipboard_read():
    try:
        import pyperclip
        return pyperclip.paste()[:2000] or "(буфер пуст)"
    except Exception as e:
        return f"Ошибка: {e}"

@tool("clipboard_write", "Записать текст в буфер обмена", {"text": "текст"}, ["text"])
def clipboard_write(text):
    try:
        import pyperclip
        pyperclip.copy(str(text))
        return "Скопировано в буфер обмена"
    except Exception as e:
        return f"Ошибка: {e}"

@tool("battery_status", "Состояние батареи ноутбука (заряд, подключён ли к сети)")
def battery_status():
    try:
        import psutil
        b = psutil.sensors_battery()
        if not b:
            return "Батарея не найдена (наверное, настольный компьютер)"
        ch = "заряжается" if b.power_plugged else "от батареи"
        return f"Заряд {b.percent:.0f}%, {ch}"
    except Exception as e:
        return f"Ошибка: {e}"
