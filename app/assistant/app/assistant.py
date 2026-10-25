import re, time, difflib, threading
from . import i18n
from .i18n import t as _t
from . import tools, tools_gui, tools_browser, tools_system, tools_extra, usercmds, memory   # noqa: F401  (регистрируют инструменты)
from .audio import record_utterance
from .stt import STT
from .tts import TTS, ensure_voices
from .llm import LLM, ensure_server, ensure_model

STOP_WORDS = {"стоп", "stop", "подожди", "хватит", "wait", "pause"}
YES = {"да", "ага", "давай", "подтверждаю", "конечно", "угу", "yes", "yeah", "ok", "okay", "sure", "confirm"}
NO = {"нет", "не", "отмена", "no", "cancel", "nope", "deny"}

def words(t):
    return re.findall(r"\w+", t.lower())

class Assistant:
    def __init__(self, cfg, bus):
        import keyboard
        import sounddevice as sd
        self.cfg, self.bus = cfg, bus
        tools.init(cfg)
        usercmds.load()
        i18n.set_lang(cfg.get("app_language", "ru"))
        lang = cfg["language"] if cfg.get("language") in ("ru", "en") else None
        self.stt, self.tts, self.llm = STT(cfg["stt_model"], lang), TTS(), LLM(cfg)
        self.name = cfg["assistant_name"]
        try:
            if cfg.get("input_device") is not None or cfg.get("output_device") is not None:
                sd.default.device = (cfg.get("input_device"), cfg.get("output_device"))
        except Exception:
            pass
        self.quit_event = threading.Event()
        self.stop_event = threading.Event()
        self.speaking, self.speak_count, self.barged = False, 0, False
        self.force_command, self.busy = False, False
        self.awaiting_confirm, self.confirm_result = False, None
        self.confirm_event = threading.Event()
        self.history = []
        try:
            keyboard.add_hotkey(cfg["hotkey_stop"], self.stop)
            keyboard.add_hotkey(cfg["hotkey_ptt"], self.ptt)
            keyboard.add_hotkey(cfg["hotkey_show"], lambda: bus.show_window.emit())
            keyboard.add_hotkey(cfg["hotkey_quit"], lambda: bus.quit_app.emit())
        except Exception as e:
            self.log("system", _t("msg_hotkeys", e=e))

    # ---------- вывод ----------
    def log(self, who, text):
        self.bus.log.emit(who, text)

    def status(self, text):
        self.bus.status.emit(text)

    def _barge(self):
        """Перебивание голосом: если во время речи ассистента вы заговорили громко — он замолкает."""
        import numpy as np, sounddevice as sd
        hits = [0]
        def cb(indata, frames, t, status):
            rms = float(np.sqrt(np.mean(indata ** 2)))
            hits[0] = hits[0] + 1 if rms > self.cfg["vad_threshold"] * 4 else 0
            if hits[0] >= 5:
                self.barged = True
                self.tts.stop()
        try:
            with sd.InputStream(samplerate=16000, channels=1, dtype="float32", blocksize=1600, callback=cb):
                while self.speaking and not self.barged:
                    time.sleep(0.05)
        except Exception:
            pass

    def say(self, text):
        self.log("assistant", text)
        if self.stop_event.is_set():
            return
        self.speaking, self.barged = True, False
        self.speak_count += 1
        self.status(_t("st_speaking"))
        if self.cfg.get("barge_in"):
            threading.Thread(target=self._barge, daemon=True).start()
        try:
            self.tts.speak(text, self.stop_event)
        finally:
            self.speaking = False
            self.speak_count += 1
            self.status(_t("st_listening"))

    # ---------- управление ----------
    def stop(self):
        self.stop_event.set()
        self.tts.stop()
        if self.awaiting_confirm:
            self.confirm_result = False
            self.confirm_event.set()
        self.log("system", _t("msg_stopped"))

    def ptt(self):
        self.force_command = True
        self.status(_t("st_speak_now"))

    def shutdown(self):
        self.quit_event.set()
        self.stop()

    def answer_confirm(self, yes):
        self.confirm_result = bool(yes)
        self.confirm_event.set()

    def submit_text(self, text):
        self.log("user", text)
        self._dispatch(text, from_text=True)

    # ---------- запуск ----------
    def start(self):
        tools_extra.set_notifier(lambda title, text: (self.bus.notify.emit(title, text),
                                                      self.bus.show_window.emit()))
        threading.Thread(target=self._boot, daemon=True).start()
        threading.Thread(target=self._timers, daemon=True).start()

    def _timers(self):
        """Поток таймеров: срабатывание напоминаний set_timer."""
        import datetime as dt
        while not self.quit_event.is_set():
            due = [x for x in tools_extra._TIMERS if x[0] <= dt.datetime.now()]
            for x in due:
                try:
                    tools_extra._TIMERS.remove(x)
                except ValueError:
                    continue
                self.bus.notify.emit("Ассистент", x[1])
                self.bus.show_window.emit()
                if not self.speaking:
                    threading.Thread(target=self.say, args=(f"Напоминание: {x[1]}",), daemon=True).start()
            self.quit_event.wait(2)

    def _boot(self):
        log = lambda t: self.log("system", t)
        self.status(_t("st_loading"))
        try:
            log(_t("msg_loading_stt"))
            self.stt.load()
            if not ensure_server(self.cfg["ollama_url"], log) or not ensure_model(self.cfg, log):
                log(_t("msg_no_llm"))
                self.status(_t("st_error_llm"))
                return
            ensure_voices(log)
        except Exception as e:
            log(_t("msg_boot_error", e=e))
            self.status(_t("st_error_boot"))
            return
        self.say(_t("greeting", name=self.name))
        self._loop()

    # ---------- слушание ----------
    def _loop(self):
        while not self.quit_event.is_set():
            try:
                count = self.speak_count
                res = record_utterance(self.cfg["vad_threshold"], self.cfg["silence_sec"], self.quit_event)
                if res is None:
                    continue
                if self.speaking or count != self.speak_count:
                    continue          # эхо собственной речи
                self.status(_t("st_recognizing"))
                text = self.stt.transcribe(res[0])
                self.status(_t("st_listening"))
                if text:
                    self.log("user", text)
                    self._dispatch(text)
            except Exception as e:
                self.log("system", _t("msg_loop_error", e=e))
                time.sleep(2)

    def _name_in(self, ws):
        for i, w in enumerate(ws[:4]):
            if self.name and difflib.SequenceMatcher(None, w, self.name.lower()).ratio() >= 0.72:
                return i
        return None

    def _dispatch(self, text, from_text=False):
        ws = words(text)
        if not ws:
            return
        if self.awaiting_confirm:
            if any(w in YES for w in ws):
                self.answer_confirm(True)
            elif any(w in NO for w in ws) or any(w in STOP_WORDS for w in ws):
                self.answer_confirm(False)
            return
        if any(w in STOP_WORDS for w in ws) and len(ws) <= 3:
            self.stop()
            return
        low = text.lower()
        if ("перезагруз" in low and ("команд" in low or "commands" in low)) or "reload commands" in low:
            n = usercmds.load()
            threading.Thread(target=self.say, args=(f"Загружено своих команд: {n}." if i18n._LANG == "ru"
                                                    else f"Reloaded user commands: {n}.",), daemon=True).start()
            return
        if ("выключи компьютер" in low or "shutdown pc" in low or "заверши работу компьютера" in low) and len(ws) <= 6:
            if self.confirm("Выключить компьютер?"):
                import subprocess
                subprocess.Popen(["shutdown", "/s", "/t", "10"], creationflags=0x08000000)
                self.say("Выключаю компьютер через 10 секунд.")
            return
        if from_text or self.force_command:
            self.force_command = False
            idx = self._name_in(ws)
            command = " ".join(ws[idx + 1:]) if idx is not None else text
        else:
            idx = self._name_in(ws)
            if idx is None:
                return
            command = " ".join(ws[idx + 1:])
            if not command:
                self.force_command = True
                threading.Thread(target=self.say, args=(_t("msg_listen_short"),), daemon=True).start()
                return
        if self.busy:
            threading.Thread(target=self.say, args=(_t("msg_busy"),), daemon=True).start()
            return
        threading.Thread(target=self._run_command, args=(command,), daemon=True).start()

    # ---------- подтверждение ----------
    def confirm(self, question):
        self.awaiting_confirm, self.confirm_result = True, None
        self.confirm_event.clear()
        self.bus.confirm_show.emit(True)
        self.say(question + " " + _t("msg_confirm_ask"))
        self.confirm_event.wait(timeout=90)
        self.awaiting_confirm = False
        self.bus.confirm_show.emit(False)
        return bool(self.confirm_result)

    # ---------- выполнение ----------
    def _system_prompt(self):
        try:
            prefs = "; ".join(f"{k}: {v}" for k, v in memory.recall())
        except Exception:
            prefs = ""
        return (f"Ты — голосовой ассистент по имени {self.name}, управляешь компьютером с Windows. "
                "Отвечай на языке пользователя, очень коротко (1–2 предложения), без markdown и эмодзи: ответ озвучивается. "
                "Простые задачи выполняй сразу, вызывая инструменты. Для сложных задач (больше 4 шагов) СНАЧАЛА вызови propose_plan. "
                "Если данных не хватает или запрос неоднозначен — задай ОДИН уточняющий вопрос, не угадывай. "
                "Порядок способов: 1) специальные инструменты (файлы, браузер, winget, настройки); 2) окна и элементы "
                "(focus_window, uia_click); 3) клавиатура, мышь и экран (type_text, press_keys, click_on_text, read_screen). "
                "Чтобы ввести текст в программу — focus_window, затем type_text; сохранить — press_keys 'ctrl+s'. "
                "В Excel для перехода к ячейке: press_keys 'ctrl+g', type_text адрес, press_keys 'enter', затем type_text значение. "
                "На вопрос «что на экране» вызови read_screen и перескажи кратко. "
                "Папки «рабочий стол», «документы», «загрузки» можно ставить первой частью пути. "
                "Если инструмент вернул ошибку — честно скажи и предложи варианты (сделать вручную, другой способ). "
                "Пароли не называй и не показывай; для входа на сайт используй web_login. "
                "Подтверждение для удаления, установки и входа на сайт запрашивает система сама. "
                + (f"Известные предпочтения пользователя: {prefs}." if prefs else ""))

    def _run_command(self, command):
        self.busy = True
        self.stop_event.clear()
        self.status(_t("st_thinking"))
        try:
            self.history.append({"role": "user", "content": command})
            # обрезка по символам: не даём диалогу разрасти в гигантский запрос (защита от зависаний и OOM)
            budget, total, keep = 16000, 0, []
            for m in reversed(self.history):
                total += len(str(m.get("content", "")))
                if total > budget and keep:
                    break
                keep.append(m)
            self.history = list(reversed(keep))[-24:]
            msgs = [{"role": "system", "content": self._system_prompt()}] + self.history
            for _ in range(40):
                if self.stop_event.is_set():
                    return
                msg = self.llm.chat(msgs, tools.schemas())
                msgs.append(msg)
                calls = msg.get("tool_calls") or []
                if not calls:
                    reply = (msg.get("content") or "").strip() or _t("msg_done")
                    self.history.append({"role": "assistant", "content": reply})
                    self.say(reply)
                    return
                for c in calls:
                    if self.stop_event.is_set():
                        return
                    name = c["function"]["name"]
                    args = c["function"].get("arguments") or {}
                    t = tools.REGISTRY.get(name)
                    if not t:
                        msgs.append({"role": "tool", "content": _t("msg_tool_missing"), "tool_name": name})
                        continue
                    if t["danger"] and not self.confirm(t["danger"](args)):
                        msgs.append({"role": "tool", "content": _t("msg_no_tool"), "tool_name": name})
                        continue
                    self.status(_t("st_running") + f": {name}")
                    shown = {k: ("***" if "pass" in k.lower() else v) for k, v in args.items()}
                    self.log("system", f"▶ {name} {shown}")
                    try:
                        result = t["fn"](**args)
                    except Exception as e:
                        result = f"Ошибка: {e}"
                    self.log("system", f"   {str(result)[:300]}")
                    msgs.append({"role": "tool", "content": str(result), "tool_name": name})
            self.say(_t("msg_too_long"))
        except Exception as e:
            self.log("system", f"Ошибка: {e}" if i18n._LANG == "ru" else f"Error: {e}")
            self.say(_t("msg_cmd_error"))
        finally:
            self.busy = False
            self.status(_t("st_listening"))
