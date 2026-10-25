"""Пользовательские команды без кода: data/commands.yaml (РЕШЕНО-5)."""
import os, re, time, subprocess, yaml
from . import config, tools

PATH = os.path.join(config.DATA, "commands.yaml")

EXAMPLE = """# Свои команды. Каждая команда — это список шагов. Ассистент сам поймёт по описанию, когда её запускать.
# Допустимые шаги: open_app, close_app, open_path, hotkey, type_text, run, wait (секунды)
# Чтобы включить пример ниже — уберите решётки в начале строк и сохраните файл (после этого перезапустите ассистента).
#
# commands:
#   - id: work_start
#     description: "Начать рабочий день: открыть браузер и блокнот"
#     steps:
#       - open_app: браузер
#       - wait: 2
#       - open_app: блокнот
commands: []
"""

def _runner(steps):
    def run():
        from . import tools_gui
        out = []
        for s in steps:
            for k, v in s.items():
                if k == "open_app":
                    out.append(tools.open_app(str(v)))
                elif k == "close_app":
                    out.append(tools.close_app(str(v)))
                elif k == "open_path":
                    out.append(tools.open_path(str(v)))
                elif k == "hotkey":
                    out.append(tools_gui.press_keys(str(v)))
                elif k == "type_text":
                    out.append(tools_gui.type_text(str(v)))
                elif k == "run":
                    subprocess.Popen(str(v), shell=True)
                    out.append(f"Запущено: {v}")
                elif k == "wait":
                    time.sleep(float(v))
                else:
                    out.append(f"Неизвестный шаг: {k}")
        return "; ".join(out) or "Команда пуста"
    return run

def load():
    """Загружает/перезагружает пользовательские команды. Повторный вызов заменяет предыдущие."""
    for k in [k for k in tools.REGISTRY if k.startswith("user_")]:
        del tools.REGISTRY[k]
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            f.write(EXAMPLE)
        return 0
    try:
        with open(PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return 0
    n = 0
    for c in data.get("commands") or []:
        cid = re.sub(r"[^a-zA-Z0-9_]", "_", str(c.get("id", "")))
        if not cid:
            continue
        tools.REGISTRY["user_" + cid] = dict(fn=_runner(c.get("steps") or []), desc=str(c.get("description", cid)),
                                             props={}, req=[], danger=None)
        n += 1
    return n
