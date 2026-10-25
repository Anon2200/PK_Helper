import os, sys, yaml

if getattr(sys, "frozen", False):
    BASE = os.path.dirname(sys.executable)      # рядом с Assistant.exe
else:
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)
CFG_PATH = os.path.join(DATA, "config.yaml")

DEFAULTS = {
    "assistant_name": "",
    "first_run_done": False,
    "app_language": "ru",           # язык интерфейса: ru / en
    "llm_model": "qwen2.5:7b",
    "ollama_url": "http://localhost:11434",
    "stt_model": "small",          # tiny/base/small/medium
    "language": "auto",            # язык речи для распознавания: auto / ru / en
    "vad_threshold": 0.015,        # громкость, с которой считаем что человек говорит (ниже = чувствительнее)
    "silence_sec": 0.9,            # пауза, после которой фраза считается законченной
    "hotkey_ptt": "ctrl+alt+space",
    "hotkey_stop": "ctrl+alt+s",
    "input_device": None,          # номер микрофона (None = по умолчанию)
    "output_device": None,
    "autostart": False,
    "stealth": False,              # режим «невидимка»: нет иконки в трее и окна при старте
    "barge_in": False,             # перебивание голосом (лучше в наушниках)
    "hotkey_show": "ctrl+alt+h",
    "hotkey_quit": "ctrl+alt+q",
    "backup_dir": os.path.join(DATA, "backup"),
}

def load():
    cfg = dict(DEFAULTS)
    if os.path.exists(CFG_PATH):
        with open(CFG_PATH, encoding="utf-8") as f:
            cfg.update(yaml.safe_load(f) or {})
    return cfg

def save(cfg):
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True)
