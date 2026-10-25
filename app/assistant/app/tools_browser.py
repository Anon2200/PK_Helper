"""ЭТАП 4: браузер (Playwright + установленный Microsoft Edge, ничего дополнительно не скачивается)."""
import os, re, queue, threading, urllib.parse, requests
from .tools import tool, resolve
from . import secrets_store

class _Worker:
    """Playwright требует один поток — держим браузер в отдельном потоке."""
    def __init__(self):
        self.q, self.th, self.pw, self.browser, self.page = queue.Queue(), None, None, None, None

    def _loop(self):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            self.pw = pw
            while True:
                fn, res = self.q.get()
                try:
                    res.put((True, fn()))
                except Exception as e:
                    res.put((False, str(e)[:300]))

    def call(self, fn, timeout=120):
        if self.th is None or not self.th.is_alive():
            self.th = threading.Thread(target=self._loop, daemon=True)
            self.th.start()
        res = queue.Queue()
        self.q.put((fn, res))
        ok, val = res.get(timeout=timeout)
        if not ok:
            raise RuntimeError(val)
        return val

    def page_(self):
        if self.page is None or self.page.is_closed():
            if self.browser is None or not self.browser.is_connected():
                self.browser = self.pw.chromium.launch(channel="msedge", headless=False)
            self.page = self.browser.new_page()
        return self.page

W = _Worker()

def _run(fn):
    try:
        return W.call(fn)
    except Exception as e:
        return f"Ошибка браузера: {e}"

def _url(u):
    return u if re.match(r"^https?://", u, re.I) else "https://" + u

@tool("web_open", "Открыть сайт в браузере", {"url": "адрес сайта"}, ["url"])
def web_open(url):
    def f():
        p = W.page_()
        p.goto(_url(url), timeout=45000)
        return f"Открыто: {p.title()}"
    return _run(f)

@tool("web_search", "Найти в интернете и вернуть заголовки и описания первых результатов", {"query": "поисковый запрос"}, ["query"])
def web_search(query):
    def f():
        p = W.page_()
        p.goto("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query), timeout=45000)
        out = []
        for r in p.query_selector_all(".result")[:5]:
            t, s = r.query_selector(".result__title"), r.query_selector(".result__snippet")
            if t:
                out.append(t.inner_text().strip() + (" — " + s.inner_text().strip() if s else ""))
        return "\n".join(out) or "Результатов нет (поисковик мог показать проверку)"
    return _run(f)

@tool("web_read", "Прочитать текст текущей открытой страницы (до 3000 символов)")
def web_read():
    return _run(lambda: W.page_().inner_text("body")[:3000])

@tool("web_click", "Нажать на ссылку или кнопку на странице по тексту", {"text": "текст ссылки/кнопки"}, ["text"])
def web_click(text):
    def f():
        W.page_().get_by_text(text).first.click(timeout=10000)
        return f"Нажато: {text}"
    return _run(f)

@tool("web_fill", "Заполнить поле формы на странице (по подписи или подсказке поля)", {"field": "подпись поля", "value": "значение"}, ["field", "value"])
def web_fill(field, value):
    def f():
        p = W.page_()
        loc = p.get_by_label(field)
        if loc.count() == 0:
            loc = p.get_by_placeholder(field)
        loc.first.fill(value, timeout=10000)
        return f"Поле «{field}» заполнено"
    return _run(f)

@tool("web_login", "Войти на сайт, используя логин и пароль из зашифрованного хранилища (пароль ассистент не раскрывает)",
      {"url": "адрес страницы входа", "secret_name": "имя сохранённых данных"}, ["url", "secret_name"],
      danger=lambda a: f"Войти на сайт {a.get('url')} с сохранёнными данными «{a.get('secret_name')}»?")
def web_login(url, secret_name):
    try:
        s = secrets_store.load(secret_name)
    except Exception as e:
        return f"Ошибка: {e}"
    def f():
        p = W.page_()
        p.goto(_url(url), timeout=45000)
        p.locator("input:not([type=hidden]):not([type=password]):visible").first.fill(s["login"], timeout=10000)
        p.locator("input[type=password]").first.fill(s["password"], timeout=10000)
        p.keyboard.press("Enter")
        return "Данные для входа введены"
    return _run(f)

@tool("web_close", "Закрыть браузер, которым управляет ассистент")
def web_close():
    def f():
        if W.browser:
            W.browser.close()
        return "Браузер закрыт"
    return _run(f)

@tool("download_file", "Скачать файл по ссылке в папку (по умолчанию «загрузки»)", {"url": "ссылка на файл", "folder": "папка"}, ["url"])
def download_file(url, folder="загрузки"):
    d = resolve(folder)
    os.makedirs(d, exist_ok=True)
    name = os.path.basename(urllib.parse.urlparse(url).path) or "download.bin"
    dst = os.path.join(d, name)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dst, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
    return f"Скачано: {dst}"
