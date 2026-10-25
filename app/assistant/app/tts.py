import os, sys, time, wave, subprocess, tempfile, urllib.request
import numpy as np
import sounddevice as sd
from . import config

VOICE_DIR = os.path.join(config.DATA, "voices")
os.makedirs(VOICE_DIR, exist_ok=True)
HF = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
VOICES = {
    "ru": ("ru_RU-irina-medium", "ru/ru_RU/irina/medium/"),
    "en": ("en_US-lessac-medium", "en/en_US/lessac/medium/"),
}

PIPER_DIR = os.path.join(config.DATA, "piper")
PIPER_EXE = os.path.join(PIPER_DIR, "piper", "piper.exe")
PIPER_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"

def ensure_piper(log):
    if os.path.exists(PIPER_EXE):
        return True
    try:
        import zipfile
        log("Скачиваю программу озвучки Piper…")
        os.makedirs(PIPER_DIR, exist_ok=True)
        z = os.path.join(PIPER_DIR, "piper.zip")
        urllib.request.urlretrieve(PIPER_URL, z)
        with zipfile.ZipFile(z) as f:
            f.extractall(PIPER_DIR)
        os.remove(z)
        return os.path.exists(PIPER_EXE)
    except Exception as e:
        log(f"Не удалось скачать Piper ({e}). Буду использовать голос Windows.")
        return False

def ensure_voices(log):
    if not ensure_piper(log):
        return
    for lang, (name, path) in VOICES.items():
        for ext in (".onnx", ".onnx.json"):
            dst = os.path.join(VOICE_DIR, name + ext)
            if not os.path.exists(dst):
                try:
                    log(f"Скачиваю голос {name}{ext}…")
                    urllib.request.urlretrieve(HF + path + name + ext, dst)
                except Exception as e:
                    log(f"Не удалось скачать голос ({e}). Буду использовать голос Windows.")
                    if os.path.exists(dst):
                        os.remove(dst)
                    return

def _lang(text):
    return "ru" if any("а" <= c.lower() <= "я" or c.lower() == "ё" for c in text) else "en"

class TTS:
    def synth(self, text, out):
        lang = _lang(text)
        model = os.path.join(VOICE_DIR, VOICES[lang][0] + ".onnx")
        if os.path.exists(PIPER_EXE) and os.path.exists(model) and os.path.exists(model + ".json"):
            try:
                r = subprocess.run(
                    [PIPER_EXE, "--model", model, "--data-dir", VOICE_DIR, "--output_file", out],
                    input=text.encode("utf-8"), capture_output=True, timeout=60,
                    cwd=os.path.dirname(PIPER_EXE), creationflags=0x08000000)
                if r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 100:
                    return True
            except Exception:
                pass
        return self._sapi(text, out, lang)

    def _sapi(self, text, out, lang):
        try:
            import pyttsx3
            eng = pyttsx3.init()
            key = ("russian", "irina", "pavel", "ru-") if lang == "ru" else ("english", "zira", "david", "en-")
            for v in eng.getProperty("voices"):
                if any(k in (v.name + v.id).lower() for k in key):
                    eng.setProperty("voice", v.id)
                    break
            eng.save_to_file(text, out)
            eng.runAndWait()
            return os.path.exists(out) and os.path.getsize(out) > 100
        except Exception:
            return False

    def speak(self, text, stop_event):
        out = os.path.join(tempfile.gettempdir(), f"asst_{int(time.time()*1000)}.wav")
        if not self.synth(text, out) or stop_event.is_set():
            return
        try:
            with wave.open(out, "rb") as w:
                sr, ch = w.getframerate(), w.getnchannels()
                data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
            if ch > 1:
                data = data.reshape(-1, ch)
            sd.play(data, sr)
            end = time.time() + len(data) / sr / (1 if ch == 1 else 1) + 0.2
            t0 = time.time()
            while time.time() < end and not stop_event.is_set():
                time.sleep(0.05)
                if time.time() - t0 > 0.3:
                    try:
                        if not sd.get_stream().active:
                            break
                    except Exception:
                        break
            sd.stop()
        finally:
            try:
                os.remove(out)
            except OSError:
                pass

    def stop(self):
        try:
            sd.stop()
        except Exception:
            pass
