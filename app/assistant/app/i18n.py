"""Локализация интерфейса (ru/en). Текст ответов ассистента определяет LLM."""
_LANG = "ru"

STRINGS = {
    # ---- мастер первого запуска ----
    "wizard_title": {"ru": "Первый запуск", "en": "First run"},
    "wizard_hello": {"ru": "Давайте познакомимся", "en": "Let's get acquainted"},
    "wizard_hint": {"ru": "Придумайте имя ассистенту. Лучше короткое, 2–3 слога: так его легче расслышать.",
                    "en": "Give the assistant a name. Short, 2–3 syllables works best for speech recognition."},
    "wizard_placeholder": {"ru": "Например: Алиса, Макс, Джарвис", "en": "For example: Alice, Max, Jarvis"},
    "wizard_model": {"ru": "Языковая модель (ваша память: {ram} ГБ). Скачается сама, это бесплатно.",
                     "en": "Language model (your RAM: {ram} GB). It will download automatically, it's free."},
    "wizard_next": {"ru": "Продолжить", "en": "Continue"},
    # ---- главное окно ----
    "status_start": {"ru": "Запуск", "en": "Starting"},
    "chat_empty": {"ru": "Диалог появится здесь", "en": "The conversation will appear here"},
    "confirm_text": {"ru": "Подтвердите действие", "en": "Confirm action"},
    "yes": {"ru": "Да", "en": "Yes"},
    "no": {"ru": "Нет", "en": "No"},
    "input_placeholder": {"ru": "Спросите или поручите что-нибудь…", "en": "Ask or command something…"},
    "stop": {"ru": "Стоп", "en": "Stop"},
    "hint_keys": {"ru": "Ctrl+Alt+Пробел — говорить   ·   Ctrl+Alt+S — стоп",
                  "en": "Ctrl+Alt+Space — talk   ·   Ctrl+Alt+S — stop"},
    "tip_mic": {"ru": "Сказать команду без имени (Ctrl+Alt+Пробел)", "en": "Speak a command without the name (Ctrl+Alt+Space)"},
    "tip_stop": {"ru": "Остановить всё (Ctrl+Alt+S)", "en": "Stop everything (Ctrl+Alt+S)"},
    "tip_settings": {"ru": "Настройки", "en": "Settings"},
    "tip_minimize": {"ru": "Свернуть", "en": "Minimize"},
    "tip_close": {"ru": "Свернуть в трей", "en": "Minimize to tray"},
    "tray_show": {"ru": "Показать", "en": "Show"},
    "tray_quit": {"ru": "Выход", "en": "Quit"},
    "say_listen": {"ru": "Скажите «{name}» и команду", "en": "Say “{name}” and a command"},
    "settings_saved": {"ru": "Настройки сохранены. Микрофон, динамики, язык, модель и клавиши заработают после перезапуска.",
                       "en": "Settings saved. Microphone, speakers, language, model and hotkeys apply after restart."},
    # ---- статусы оркестратора ----
    "st_loading": {"ru": "Загрузка моделей…", "en": "Loading models…"},
    "st_listening": {"ru": "Слушаю", "en": "Listening"},
    "st_speaking": {"ru": "Говорю…", "en": "Speaking…"},
    "st_recognizing": {"ru": "Распознаю…", "en": "Recognizing…"},
    "st_thinking": {"ru": "Думаю…", "en": "Thinking…"},
    "st_running": {"ru": "Выполняю", "en": "Running"},
    "st_error_llm": {"ru": "Ошибка: нет LLM", "en": "Error: no LLM"},
    "st_error_boot": {"ru": "Ошибка запуска", "en": "Startup error"},
    "st_speak_now": {"ru": "Говорите команду…", "en": "Speak your command…"},
    # ---- сообщения оркестратора ----
    "msg_loading_stt": {"ru": "Загружаю распознавание речи (в первый раз нужен интернет)…",
                        "en": "Loading speech recognition (internet needed for the first run)…"},
    "msg_no_llm": {"ru": "Не удалось подготовить языковую модель. Проверьте, что Ollama установлена.",
                   "en": "Could not prepare the language model. Make sure Ollama is installed."},
    "msg_boot_error": {"ru": "Ошибка запуска: {e}", "en": "Startup error: {e}"},
    "greeting": {"ru": "Привет! Я {name}. Скажите моё имя и команду.", "en": "Hi! I am {name}. Say my name and a command."},
    "msg_hotkeys": {"ru": "Горячие клавиши недоступны: {e}", "en": "Hotkeys unavailable: {e}"},
    "msg_listen_short": {"ru": "Слушаю.", "en": "I'm listening."},
    "msg_busy": {"ru": "Я ещё выполняю предыдущую задачу. Скажите «стоп», чтобы прервать.",
                 "en": "I'm still busy with the previous task. Say “stop” to interrupt."},
    "msg_confirm_ask": {"ru": "Скажите «да» или «нет».", "en": "Say “yes” or “no”."},
    "msg_stopped": {"ru": "⛔ Стоп", "en": "⛔ Stop"},
    "msg_loop_error": {"ru": "Ошибка прослушивания: {e}", "en": "Listening error: {e}"},
    "msg_done": {"ru": "Готово.", "en": "Done."},
    "msg_no_tool": {"ru": "Пользователь отказал. Действие не выполнено.", "en": "User refused. Action not performed."},
    "msg_tool_missing": {"ru": "Ошибка: нет такого инструмента", "en": "Error: no such tool"},
    "msg_too_long": {"ru": "Задача получилась слишком длинной, я остановился. Скажите, что делать дальше.",
                     "en": "The task turned out too long, I stopped. Tell me what to do next."},
    "msg_cmd_error": {"ru": "Произошла ошибка. Подробности в окне.", "en": "An error occurred. Details are in the window."},
    # ---- системные подсказки инструментов ----
    "sys_autostart_fail": {"ru": "Автозапуск не настроен: {e}", "en": "Autostart not configured: {e}"},
    # ---- ошибки конфигурации ----
    "err_title": {"ru": "Ошибка", "en": "Error"},
    "err_crash": {"ru": "Программа упала. Подробности в файле data\\error.log",
                  "en": "The program crashed. Details are in data\\error.log"},
    # ---- диалог настроек ----
    "set_autostart": {"ru": "Запускать вместе с Windows", "en": "Start with Windows"},
    "set_stealth": {"ru": "Режим «невидимка» (без иконки в трее; показать окно — Ctrl+Alt+H)",
                    "en": "Stealth mode (no tray icon; show window with Ctrl+Alt+H)"},
    "set_barge": {"ru": "Перебивать ассистента голосом (лучше в наушниках)", "en": "Interrupt the assistant with your voice (headphones recommended)"},
    "set_name": {"ru": "Имя ассистента", "en": "Assistant name"},
    "set_mic": {"ru": "Микрофон", "en": "Microphone"},
    "set_speakers": {"ru": "Динамики", "en": "Speakers"},
    "set_model": {"ru": "Языковая модель", "en": "Language model"},
    "set_ui_lang": {"ru": "Язык интерфейса", "en": "Interface language"},
    "set_stt_lang": {"ru": "Язык распознавания", "en": "Speech recognition language"},
    "set_sens": {"ru": "Чувствительность", "en": "Sensitivity"},
    "set_sens_hint": {"ru": "(меньше = чувствительнее)", "en": "(lower = more sensitive)"},
    "set_hk_talk": {"ru": "Клавиша «говорить»", "en": "Talk hotkey"},
    "set_hk_stop": {"ru": "Клавиша «стоп»", "en": "Stop hotkey"},
    "set_hk_show": {"ru": "Показать окно", "en": "Show window"},
    "set_hk_quit": {"ru": "Выйти", "en": "Quit"},
    "set_save": {"ru": "Сохранить", "en": "Save"},
}

def set_lang(code):
    global _LANG
    _LANG = code if code in ("ru", "en") else "ru"

def t(key, **kw):
    pair = STRINGS.get(key)
    if not pair:
        return key
    s = pair.get(_LANG, pair["ru"])
    if kw:
        try:
            s = s.format(**kw)
        except Exception:
            pass
    return s
