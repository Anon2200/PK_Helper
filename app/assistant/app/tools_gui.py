"""ЭТАП 3: управление окнами, мышью, клавиатурой, экран + OCR. Цепочка: UI Automation -> мышь/клавиатура + OCR."""
import os, re, ctypes, shutil, time, urllib.request
from .tools import tool, resolve
from . import config

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

def _pg():
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.05
    return pyautogui

def _active_title():
    try:
        h = ctypes.windll.user32.GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetWindowTextW(h, buf, 256)
        return buf.value
    except Exception:
        return ""

@tool("type_text", "Напечатать текст в активном окне (работает с русским и английским)", {"text": "текст"}, ["text"])
def type_text(text):
    import pyperclip
    pg = _pg()
    old = ""
    try:
        old = pyperclip.paste()
    except Exception:
        pass
    pyperclip.copy(text)
    time.sleep(0.1)
    pg.hotkey("ctrl", "v")
    time.sleep(0.2)
    try:
        pyperclip.copy(old)
    except Exception:
        pass
    return f"Напечатано в окне «{_active_title()}»"

@tool("press_keys", "Нажать клавишу или сочетание, например 'enter', 'ctrl+s', 'win+d', 'alt+tab'", {"keys": "клавиши через +"}, ["keys"])
def press_keys(keys):
    _pg().hotkey(*[k.strip().lower() for k in keys.split("+")])
    return f"Нажато: {keys}"

@tool("mouse_click", "Кликнуть мышью по координатам экрана", {"x": ("integer", "x"), "y": ("integer", "y"),
      "button": "left или right", "double": "true для двойного клика"}, ["x", "y"])
def mouse_click(x, y, button="left", double="false"):
    pg = _pg()
    pg.click(int(x), int(y), clicks=2 if str(double).lower() == "true" else 1, button=button)
    return f"Клик ({x}, {y})"

@tool("list_windows", "Показать список открытых окон")
def list_windows():
    from pywinauto import Desktop
    t = [w.window_text() for w in Desktop(backend="uia").windows() if w.window_text().strip()]
    return "Окна: " + "; ".join(t[:25])

@tool("focus_window", "Переключиться на окно по части заголовка (например Excel, Блокнот)", {"title": "часть заголовка окна"}, ["title"])
def focus_window(title):
    from pywinauto import Desktop
    for w in Desktop(backend="uia").windows():
        if title.lower() in w.window_text().lower():
            try:
                w.restore()
            except Exception:
                pass
            w.set_focus()
            return f"Активно окно: {w.window_text()}"
    return f"Ошибка: окно «{title}» не найдено (откройте программу сначала)"

@tool("uia_click", "Нажать кнопку/элемент в окне через UI Automation (надёжнее мыши)",
      {"window": "часть заголовка окна", "control": "название кнопки или элемента"}, ["window", "control"])
def uia_click(window, control):
    from pywinauto import Desktop
    w = Desktop(backend="uia").window(title_re=f".*{re.escape(window)}.*")
    w.child_window(title_re=f".*{re.escape(control)}.*").click_input()
    return f"Нажато «{control}» в «{window}»"

@tool("minimize_all", "Свернуть все окна (показать рабочий стол)")
def minimize_all():
    _pg().hotkey("win", "d")
    return "Окна свёрнуты"

@tool("take_screenshot", "Сделать снимок экрана и сохранить (по умолчанию на рабочий стол)", {"path": "куда сохранить, необязательно"})
def take_screenshot(path=""):
    p = resolve(path) if path else resolve("рабочий стол/screenshot_" + time.strftime("%Y%m%d_%H%M%S") + ".png")
    if not p.lower().endswith(".png"):
        p = os.path.join(p, "screenshot_" + time.strftime("%Y%m%d_%H%M%S") + ".png")
    _pg().screenshot(p)
    return f"Скриншот сохранён: {p}"

# ---------- OCR ----------
TESS = [r"C:\Program Files\Tesseract-OCR\tesseract.exe", os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe")]

def _ocr():
    import pytesseract
    exe = next((p for p in TESS if os.path.exists(p)), None) or shutil.which("tesseract")
    if not exe:
        raise RuntimeError("Tesseract не установлен (install.bat ставит его через winget)")
    pytesseract.pytesseract.tesseract_cmd = exe
    d = os.path.join(config.DATA, "tessdata")
    os.makedirs(d, exist_ok=True)
    for lang in ("eng", "rus"):
        f = os.path.join(d, lang + ".traineddata")
        if not os.path.exists(f):
            urllib.request.urlretrieve(f"https://github.com/tesseract-ocr/tessdata_fast/raw/main/{lang}.traineddata", f)
    os.environ["TESSDATA_PREFIX"] = d
    return pytesseract

@tool("read_screen", "Прочитать, что сейчас на экране: заголовок активного окна + распознанный текст (OCR). Для вопроса «что на экране?»")
def read_screen():
    ocr = _ocr()
    img = _pg().screenshot()
    text = ocr.image_to_string(img, lang="rus+eng").strip()
    text = re.sub(r"\n{2,}", "\n", text)[:2500]
    return f"Активное окно: {_active_title()}\nТекст на экране:\n{text or '(текст не найден)'}"

@tool("click_on_text", "Найти надпись на экране (OCR) и кликнуть по ней. Запасной способ, если нет UI Automation",
      {"text": "надпись на экране"}, ["text"])
def click_on_text(text):
    ocr = _ocr()
    img = _pg().screenshot()
    data = ocr.image_to_data(img, lang="rus+eng", output_type=ocr.Output.DICT)
    q = text.lower()
    for i, wd in enumerate(data["text"]):
        if wd.strip() and q in wd.lower():
            x = data["left"][i] + data["width"][i] // 2
            y = data["top"][i] + data["height"][i] // 2
            _pg().click(x, y)
            return f"Кликнул по «{wd}» ({x}, {y})"
    return f"Ошибка: надпись «{text}» на экране не найдена"
