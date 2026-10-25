"""Реестр инструментов + файловые операции. Остальные инструменты — в tools_gui / tools_browser / tools_system."""
import os, ctypes, shutil, subprocess, time, zipfile

CFG, REGISTRY = {}, {}

APPEND = {}   # сюда дополнительные модули с инструментами могут дописывать REGISTRY

def init(cfg):
    CFG.update(cfg)

def tool(name, desc, props=None, req=None, danger=None):
    """Регистрация инструмента. props: {имя: 'описание'} или {имя: ('integer','описание')}.
    danger: None или функция args -> текст вопроса (тогда нужно подтверждение пользователя)."""
    spec = {}
    for k, v in (props or {}).items():
        spec[k] = {"type": "string", "description": v} if isinstance(v, str) else {"type": v[0], "description": v[1]}
    def deco(fn):
        REGISTRY[name] = dict(fn=fn, desc=desc, props=spec, req=req or [], danger=danger)
        return fn
    return deco

def schemas():
    return [{"type": "function", "function": {
        "name": n, "description": t["desc"],
        "parameters": {"type": "object", "properties": t["props"], "required": t["req"]}}}
        for n, t in REGISTRY.items()]

# ---------- пути ----------
def _known(csidl, fallback):
    try:
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buf)
        return buf.value or fallback
    except Exception:
        return fallback

def _folders():
    home = os.path.expanduser("~")
    desk = _known(0x10, os.path.join(home, "Desktop"))
    docs = _known(5, os.path.join(home, "Documents"))
    pics = _known(0x27, os.path.join(home, "Pictures"))
    dl = os.path.join(home, "Downloads")
    m = {}
    for k in ("рабочий стол", "рабочем столе", "рабочего стола", "desktop"):
        m[k] = desk
    for k in ("документы", "документах", "documents", "мои документы"):
        m[k] = docs
    for k in ("загрузки", "загрузках", "downloads"):
        m[k] = dl
    for k in ("картинки", "изображения", "pictures", "фото"):
        m[k] = pics
    for k in ("домашняя папка", "home"):
        m[k] = home
    return m

def resolve(path):
    p = str(path).strip().strip('"')
    if os.path.isabs(p) or p[1:2] == ":":
        return os.path.normpath(p if len(p) > 2 or p[1:2] != ":" else p + "\\")
    parts = [x for x in p.replace("\\", "/").split("/") if x]
    f = _folders()
    if parts and parts[0].lower() in f:
        return os.path.normpath(os.path.join(f[parts[0].lower()], *parts[1:]))
    return os.path.normpath(os.path.join(f["desktop"], *parts))   # по умолчанию — рабочий стол

# ---------- программы ----------
APPS = {
    "блокнот": "notepad.exe", "notepad": "notepad.exe",
    "калькулятор": "calc.exe", "calculator": "calc.exe",
    "paint": "mspaint.exe", "пейнт": "mspaint.exe",
    "проводник": "explorer.exe", "explorer": "explorer.exe",
    "браузер": "msedge", "edge": "msedge", "chrome": "chrome", "хром": "chrome", "firefox": "firefox",
    "word": "winword", "ворд": "winword", "excel": "excel", "эксель": "excel",
}

@tool("open_app", "Запустить программу (блокнот, калькулятор, браузер, chrome, word, excel, проводник или имя exe)",
      {"name": "название программы"}, ["name"])
def open_app(name):
    exe = APPS.get(name.strip().lower(), name.strip())
    try:
        os.startfile(exe)
        return f"Запущено: {name}"
    except Exception as e:
        return f"Ошибка: не удалось запустить «{name}» ({e})"

@tool("close_app", "Закрыть программу (мягко, как кнопкой закрытия)", {"name": "название программы"}, ["name"])
def close_app(name):
    exe = os.path.basename(APPS.get(name.strip().lower(), name.strip()))
    if not exe.lower().endswith(".exe"):
        exe += ".exe"
    r = subprocess.run(["taskkill", "/IM", exe], capture_output=True, creationflags=0x08000000)
    return f"Закрыто: {name}" if r.returncode == 0 else f"Ошибка: «{name}» не запущено или не закрылось"

@tool("open_path", "Открыть папку, диск (например D:\\), файл или ссылку в Проводнике / программе по умолчанию",
      {"path": "путь, диск или ссылка"}, ["path"])
def open_path(path):
    p = path if path.lower().startswith(("http://", "https://")) else resolve(path)
    try:
        os.startfile(p)
        return f"Открыто: {p}"
    except Exception as e:
        return f"Ошибка: {e}"

# ---------- файлы ----------
@tool("create_folder", "Создать папку. Путь: 'рабочий стол/Отчёты' или полный 'D:\\\\Папка'", {"path": "путь к новой папке"}, ["path"])
def create_folder(path):
    p = resolve(path)
    if os.path.exists(p):
        return f"Папка уже существует: {p}"
    os.makedirs(p)
    return f"Папка создана: {p}"

@tool("create_file", "Создать текстовый файл", {"path": "путь к файлу", "content": "содержимое"}, ["path"])
def create_file(path, content=""):
    p = resolve(path)
    if os.path.exists(p):
        return f"Ошибка: файл уже существует: {p}"
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Файл создан: {p}"

@tool("append_file", "Дописать текст в конец файла (создаст, если нет)", {"path": "путь", "content": "текст"}, ["path", "content"])
def append_file(path, content):
    p = resolve(path)
    d = os.path.dirname(p)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(content)
    return f"Дописано в {p}"

@tool("read_file", "Прочитать текстовый файл (до 3000 символов)", {"path": "путь"}, ["path"])
def read_file(path):
    p = resolve(path)
    if not os.path.isfile(p):
        return f"Ошибка: нет файла {p}"
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read(3000)

@tool("rename_path", "Переименовать файл или папку", {"path": "путь", "new_name": "новое имя без пути"}, ["path", "new_name"])
def rename_path(path, new_name):
    p = resolve(path)
    if not os.path.exists(p):
        return f"Ошибка: не найдено: {p}"
    if "/" in new_name or "\\" in new_name:
        return "Ошибка: новое имя не должно содержать слэшей"
    dst = os.path.join(os.path.dirname(p), new_name)
    if os.path.exists(dst):
        return f"Ошибка: уже существует {dst}"
    os.rename(p, dst)
    return f"Переименовано в {dst}"

@tool("rename_by_date", "Переименовать все файлы с расширением в папке по дате изменения (ГГГГ-ММ-ДД_ЧЧММСС)",
      {"folder": "папка", "extension": "расширение, например jpg"}, ["folder", "extension"])
def rename_by_date(folder, extension):
    p = resolve(folder)
    if not os.path.isdir(p):
        return f"Ошибка: нет папки {p}"
    ext, n = "." + extension.lstrip(".").lower(), 0
    for f in sorted(os.listdir(p)):
        if f.lower().endswith(ext):
            src = os.path.join(p, f)
            base = time.strftime("%Y-%m-%d_%H%M%S", time.localtime(os.path.getmtime(src)))
            dst, i = os.path.join(p, base + ext), 1
            while os.path.exists(dst) and dst != src:
                dst = os.path.join(p, f"{base}_{i}{ext}")
                i += 1
            if dst != src:
                os.rename(src, dst)
                n += 1
    return f"Переименовано файлов: {n}"

@tool("copy_path", "Скопировать файл или папку (например в OneDrive)", {"src": "что копировать", "dst": "куда (папка или новый путь)"}, ["src", "dst"])
def copy_path(src, dst):
    s, d = resolve(src), resolve(dst)
    if not os.path.exists(s):
        return f"Ошибка: не найдено {s}"
    if os.path.isdir(d):
        d = os.path.join(d, os.path.basename(s))
    if os.path.isdir(s):
        shutil.copytree(s, d)
    else:
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(s, d)
    return f"Скопировано в {d}"

@tool("move_path", "Переместить файл или папку", {"src": "что", "dst": "куда"}, ["src", "dst"])
def move_path(src, dst):
    s, d = resolve(src), resolve(dst)
    if not os.path.exists(s):
        return f"Ошибка: не найдено {s}"
    if os.path.isdir(d):
        d = os.path.join(d, os.path.basename(s))
    if os.path.exists(d):
        return f"Ошибка: уже существует {d}"
    shutil.move(s, d)
    return f"Перемещено в {d}"

@tool("delete_path", "Удалить файл или папку (требует подтверждения; сначала резервная копия, затем корзина)",
      {"path": "путь"}, ["path"],
      danger=lambda a: f"Удалить {a.get('path')}? Сначала сделаю копию, потом отправлю в корзину.")
def delete_path(path):
    from send2trash import send2trash
    p = resolve(path)
    if not os.path.exists(p):
        return f"Ошибка: не найдено: {p}"
    bdir = os.path.join(CFG["backup_dir"], time.strftime("%Y%m%d_%H%M%S"))
    os.makedirs(bdir, exist_ok=True)
    dst = os.path.join(bdir, os.path.basename(p))
    if os.path.isdir(p):
        shutil.copytree(p, dst)
    else:
        shutil.copy2(p, dst)
    send2trash(p)
    return f"Удалено в корзину: {p}. Резервная копия: {dst}"

@tool("list_folder", "Показать содержимое папки", {"path": "путь к папке"}, ["path"])
def list_folder(path):
    p = resolve(path)
    if not os.path.isdir(p):
        return f"Ошибка: нет такой папки: {p}"
    items = os.listdir(p)[:50]
    return f"В {p} ({len(items)} элементов): " + ", ".join(items) if items else f"Папка {p} пуста"

TEXT_EXT = {".txt", ".md", ".csv", ".log", ".json", ".xml", ".html", ".py", ".yaml", ".yml", ".ini"}

@tool("search_files", "Найти файлы в папке (с подпапками) по части имени, расширению, году изменения или тексту внутри",
      {"folder": "где искать", "name": "часть имени", "extension": "расширение, например pdf",
       "year": "год последнего изменения, например 2024", "content": "текст внутри файла"}, ["folder"])
def search_files(folder, name="", extension="", year="", content=""):
    root = resolve(folder)
    if not os.path.isdir(root):
        return f"Ошибка: нет папки {root}"
    ext = ("." + extension.lstrip(".").lower()) if extension else ""
    t0, found = time.time(), []
    stop = False
    for d, _, files in os.walk(root):
        for f in files:
            if len(found) >= 30 or time.time() - t0 > 60:
                stop = True
                break
            fp = os.path.join(d, f)
            if name and name.lower() not in f.lower():
                continue
            if ext and not f.lower().endswith(ext):
                continue
            try:
                if year and time.strftime("%Y", time.localtime(os.path.getmtime(fp))) != str(year):
                    continue
                if content:
                    if os.path.splitext(f)[1].lower() not in TEXT_EXT or os.path.getsize(fp) > 2_000_000:
                        continue
                    with open(fp, encoding="utf-8", errors="ignore") as fh:
                        if content.lower() not in fh.read().lower():
                            continue
            except OSError:
                continue
            found.append(fp)
        if stop:
            break
    return f"Найдено {len(found)}:\n" + "\n".join(found) if found else "Ничего не найдено"

@tool("zip_path", "Упаковать файл или папку в zip-архив", {"path": "что упаковать", "archive": "путь к архиву .zip"}, ["path"])
def zip_path(path, archive=""):
    p = resolve(path)
    if not os.path.exists(p):
        return f"Ошибка: не найдено {p}"
    a = resolve(archive) if archive else p.rstrip("\\/") + ".zip"
    with zipfile.ZipFile(a, "w", zipfile.ZIP_DEFLATED) as z:
        if os.path.isdir(p):
            for d, _, files in os.walk(p):
                for f in files:
                    fp = os.path.join(d, f)
                    z.write(fp, os.path.relpath(fp, os.path.dirname(p)))
        else:
            z.write(p, os.path.basename(p))
    return f"Архив создан: {a}"

@tool("extract_archive", "Распаковать архив (zip, tar) в папку", {"archive": "путь к архиву", "dest": "куда распаковать"}, ["archive"])
def extract_archive(archive, dest=""):
    a = resolve(archive)
    if not os.path.isfile(a):
        return f"Ошибка: нет архива {a}"
    d = resolve(dest) if dest else os.path.splitext(a)[0]
    shutil.unpack_archive(a, d)
    return f"Распаковано в {d}"

@tool("print_file", "Отправить файл на печать (принтер по умолчанию)", {"path": "путь к файлу"}, ["path"])
def print_file(path):
    p = resolve(path)
    if not os.path.isfile(p):
        return f"Ошибка: нет файла {p}"
    try:
        os.startfile(p, "print")
        return f"Отправлено на печать: {p}"
    except Exception as e:
        return f"Ошибка печати: {e}. Возможно, для этого типа файлов нет программы печати."
