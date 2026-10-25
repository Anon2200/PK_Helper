"""Шифрованное хранилище логинов/паролей (Windows DPAPI). Расшифровать может только эта учётная запись Windows."""
import os, json, base64
from . import config

PATH = os.path.join(config.DATA, "secrets.json")

def _enc(b):
    import win32crypt
    return win32crypt.CryptProtectData(b, "assistant", None, None, None, 0)

def _dec(b):
    import win32crypt
    return win32crypt.CryptUnprotectData(b, None, None, None, 0)[1]

def _read():
    if not os.path.exists(PATH):
        return {}
    with open(PATH, encoding="utf-8") as f:
        return json.load(f)

def save(name, login, password):
    d = _read()
    blob = json.dumps({"login": login, "password": password}).encode("utf-8")
    d[name] = base64.b64encode(_enc(blob)).decode()
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(d, f)

def load(name):
    d = _read()
    if name not in d:
        raise KeyError(f"Секрет «{name}» не найден")
    return json.loads(_dec(base64.b64decode(d[name])).decode("utf-8"))

def names():
    return list(_read().keys())
