import os, time, subprocess, requests

def ollama_exe():
    p = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe")
    if os.path.exists(p):
        return p
    import shutil
    return shutil.which("ollama")

def server_tags(url):
    try:
        return requests.get(url + "/api/tags", timeout=2).json()
    except Exception:
        return None

def ensure_server(url, log):
    if server_tags(url) is not None:
        return True
    exe = ollama_exe()
    if not exe:
        log("Ollama не найдена. Установите: winget install Ollama.Ollama (или с ollama.com) и перезапустите.")
        return False
    subprocess.Popen([exe, "serve"], creationflags=0x08000000)
    for _ in range(30):
        time.sleep(1)
        if server_tags(url) is not None:
            return True
    return False

def ensure_model(cfg, log):
    tags = server_tags(cfg["ollama_url"]) or {}
    names = [m["name"] for m in tags.get("models", [])]
    model = cfg["llm_model"]
    if model in names or model + ":latest" in names:
        return True
    log(f"Скачиваю модель {model}. Это несколько гигабайт, подождите…")
    exe = ollama_exe()
    if not exe:
        log("Ollama не найдена — не могу скачать модель.")
        return False
    try:
        r = subprocess.run([exe, "pull", model], creationflags=0x08000000)
    except FileNotFoundError:
        return False
    return r.returncode == 0

class LLM:
    def __init__(self, cfg):
        self.cfg = cfg

    def chat(self, messages, tool_schemas):
        r = requests.post(self.cfg["ollama_url"] + "/api/chat", json={
            "model": self.cfg["llm_model"], "messages": messages, "tools": tool_schemas,
            "stream": False, "keep_alive": "10m", "options": {"temperature": 0.2},
        }, timeout=600)
        r.raise_for_status()
        return r.json()["message"]
