import math
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QDialog,
                               QComboBox, QSystemTrayIcon, QMenu, QApplication, QScrollArea, QFrame, QSizeGrip)
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QPointF, QRectF, QSize, QPropertyAnimation
from PySide6.QtGui import (QIcon, QPixmap, QPainter, QColor, QAction, QLinearGradient, QRadialGradient,
                           QPen, QBrush, QPainterPath, QFont)
from . import i18n
from .i18n import t

GRAD = "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #6366f1,stop:1 #22d3ee)"
STYLE = f"""
QWidget{{background:transparent;color:#e8ebf5;font-family:'Segoe UI';font-size:14px}}
QDialog{{background:#0a0f1e}}
QToolTip{{background:#121a30;color:#e8ebf5;border:1px solid #2a3556;padding:4px 8px}}
QScrollArea{{border:none;background:transparent}}
QScrollBar:vertical{{background:transparent;width:6px;margin:4px 0}}
QScrollBar::handle:vertical{{background:rgba(255,255,255,0.14);border-radius:3px;min-height:30px}}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0}}
QSizeGrip{{background:transparent}}
QLineEdit#input{{background:transparent;border:none;padding:8px 6px;font-size:15px;color:#f4f6fc}}
QLineEdit#name{{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:18px;padding:12px 18px;font-size:15px}}
QLineEdit#name:focus{{border:1px solid #6366f1}}
QComboBox{{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:16px;padding:10px 16px}}
QComboBox QAbstractItemView{{background:#121a30;selection-background-color:#4f46e5;border:1px solid #2a3556;outline:0}}
QFrame#bar{{background:rgba(255,255,255,0.055);border:1px solid rgba(255,255,255,0.10);border-radius:30px}}
QPushButton{{border:none;border-radius:20px;padding:10px 20px;font-weight:600;background:rgba(255,255,255,0.08);color:#e8ebf5}}
QPushButton:hover{{background:rgba(255,255,255,0.14)}}
QPushButton#primary{{background:{GRAD};color:white;padding:12px 22px;border-radius:22px}}
QPushButton#primary:hover{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #7c7ff5,stop:1 #4de0f2)}}
QPushButton#mic,QPushButton#send{{background:{GRAD};min-width:44px;max-width:44px;min-height:44px;max-height:44px;border-radius:22px;padding:0}}
QPushButton#send{{min-width:38px;max-width:38px;min-height:38px;max-height:38px;border-radius:19px;background:rgba(255,255,255,0.10)}}
QPushButton#send:hover{{background:rgba(255,255,255,0.20)}}
QPushButton#mic:hover{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #7c7ff5,stop:1 #4de0f2)}}
QPushButton#stop{{background:rgba(239,68,68,0.14);color:#fca5a5;border:1px solid rgba(239,68,68,0.40);border-radius:17px;padding:6px 16px}}
QPushButton#stop:hover{{background:rgba(239,68,68,0.30)}}
QPushButton#yes{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #10b981,stop:1 #22d3ee);color:white;padding:10px 26px}}
QPushButton#no{{background:rgba(239,68,68,0.20);color:#fecaca;border:1px solid rgba(239,68,68,0.45);padding:10px 26px}}
QPushButton#win,QPushButton#winclose{{background:transparent;color:#8b93a7;border-radius:16px;min-width:32px;max-width:32px;min-height:32px;max-height:32px;padding:0;font-size:15px}}
QPushButton#win:hover{{background:rgba(255,255,255,0.10);color:white}}
QPushButton#winclose:hover{{background:rgba(239,68,68,0.55);color:white}}
QFrame#confirm{{background:rgba(245,158,11,0.10);border:1px solid rgba(245,158,11,0.45);border-radius:20px}}
QLabel#title{{font-size:22px;font-weight:700;color:white}}
"""

class Bus(QObject):
    log = Signal(str, str)
    status = Signal(str)
    notify = Signal(str, str)  # всплывающее уведомление Windows (таймеры)
    confirm_show = Signal(bool)
    show_window = Signal()
    quit_app = Signal()

# ---------- рисованные иконки ----------
def _pm(size=64):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    return pm, p

def icon_mic():
    pm, p = _pm()
    s = 64
    c = QColor("white")
    p.setPen(QPen(c, s * 0.07, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(c)
    p.drawRoundedRect(QRectF(s * .38, s * .12, s * .24, s * .40), s * .12, s * .12)
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(s * .27, s * .28, s * .46, s * .40), 180 * 16, 180 * 16)
    p.drawLine(QPointF(s * .5, s * .68), QPointF(s * .5, s * .84))
    p.drawLine(QPointF(s * .39, s * .84), QPointF(s * .61, s * .84))
    p.end()
    return QIcon(pm)

def icon_send():
    pm, p = _pm()
    s = 64
    p.setPen(QPen(QColor("white"), s * 0.08, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawLine(QPointF(s * .5, s * .76), QPointF(s * .5, s * .26))
    p.drawLine(QPointF(s * .5, s * .26), QPointF(s * .30, s * .46))
    p.drawLine(QPointF(s * .5, s * .26), QPointF(s * .70, s * .46))
    p.end()
    return QIcon(pm)

def make_icon():
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, 128, 128)
    g.setColorAt(0, QColor("#3b82f6"))
    g.setColorAt(1, QColor("#7c3aed"))
    p.setBrush(QBrush(g))
    p.setPen(Qt.NoPen)
    p.drawEllipse(4, 4, 120, 120)
    p.setBrush(QColor("white"))
    p.drawRoundedRect(QRectF(50, 26, 28, 52), 14, 14)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor("white"), 6, Qt.SolidLine, Qt.RoundCap))
    p.drawArc(QRectF(36, 44, 56, 50), 180 * 16, 180 * 16)
    p.drawLine(QPointF(64, 94), QPointF(64, 104))
    p.drawLine(QPointF(52, 104), QPointF(76, 104))
    p.end()
    return QIcon(pm)

# ---------- живая сфера ----------
def _mix(a, b, k):
    return QColor(int(a.red() + (b.red() - a.red()) * k), int(a.green() + (b.green() - a.green()) * k),
                  int(a.blue() + (b.blue() - a.blue()) * k))

def _al(c, a):
    x = QColor(c)
    x.setAlpha(max(0, min(255, int(a))))
    return x

ORB_STATES = {   # цвет1, цвет2, амплитуда, эффект
    "boot":   ("#f59e0b", "#8b5cf6", 0.03, "arcs"),
    "idle":   ("#6366f1", "#22d3ee", 0.015, ""),
    "listen": ("#10b981", "#22d3ee", 0.06, "rings"),
    "think":  ("#f59e0b", "#a855f7", 0.03, "arcs"),
    "speak":  ("#22d3ee", "#6366f1", 0.11, "rings"),
    "error":  ("#ef4444", "#f97316", 0.02, ""),
}

def state_for(text):
    t = text.lower()
    if "ошибка" in t or "error" in t:
        return "error"
    if "говорю" in t or "speaking" in t:
        return "speak"
    if "говорите" in t or "speak your" in t:
        return "listen"
    if "слушаю" in t or "listening" in t:
        return "idle"
    return "think"

class Orb(QWidget):
    def __init__(self, min_h=280):
        super().__init__()
        self.setMinimumHeight(min_h)
        self.t = 0.0
        self.mode, self.amp_target = "arcs", 0.03
        self.c1, self.c2 = QColor("#f59e0b"), QColor("#8b5cf6")
        self.t1, self.t2 = QColor(self.c1), QColor(self.c2)
        self.amp = 0.03
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

    def set_state(self, name):
        a, b, amp, mode = ORB_STATES[name]
        self.t1, self.t2, self.amp_target, self.mode = QColor(a), QColor(b), amp, mode

    def tick(self):
        if not self.isVisible():
            return
        self.t += 0.016
        self.c1 = _mix(self.c1, self.t1, 0.07)
        self.c2 = _mix(self.c2, self.t2, 0.07)
        self.amp += (self.amp_target - self.amp) * 0.08
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h, t = self.width(), self.height(), self.t
        cx, cy = w / 2, h / 2
        R = min(w, h) * 0.26
        voice = abs(math.sin(t * 7.3) * math.sin(t * 3.1 + 1.0))
        r = R * (1 + 0.03 * math.sin(t * 1.7) + self.amp * (0.35 + 0.65 * voice))
        c1, c2 = self.c1, self.c2
        p.setPen(Qt.NoPen)
        # свечение
        gr = min(w, h) / 2 - 2
        g = QRadialGradient(cx, cy, gr)
        g.setColorAt(0.0, _al(c1, 120))
        g.setColorAt(0.5, _al(c2, 38))
        g.setColorAt(1.0, _al(c2, 0))
        p.setBrush(g)
        p.drawEllipse(QPointF(cx, cy), gr, gr)
        # кольца
        if self.mode == "rings":
            p.setBrush(Qt.NoBrush)
            for i in range(3):
                ph = (t * 0.55 + i / 3) % 1
                p.setPen(QPen(_al(c2, (1 - ph) * 120), 1.6))
                rr = r * (1.05 + ph * 0.85)
                p.drawEllipse(QPointF(cx, cy), rr, rr)
        # тело сферы
        path = QPainterPath()
        path.addEllipse(QPointF(cx, cy), r, r)
        p.setClipPath(path)
        p.setPen(Qt.NoPen)
        p.setBrush(_mix(c1, QColor("#04050b"), 0.62))
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.setCompositionMode(QPainter.CompositionMode_Plus)
        for i in range(3):
            ang = t * (0.5 + 0.23 * i) + i * 2.094
            ox, oy = math.cos(ang) * r * 0.40, math.sin(ang * 1.1) * r * 0.40
            col = c1 if i % 2 == 0 else c2
            bg = QRadialGradient(cx + ox, cy + oy, r * 0.95)
            bg.setColorAt(0, _al(col, 210))
            bg.setColorAt(1, _al(col, 0))
            p.setBrush(bg)
            p.drawEllipse(QPointF(cx + ox, cy + oy), r * 0.95, r * 0.95)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        hl = QRadialGradient(cx - r * 0.35, cy - r * 0.48, r * 0.95)
        hl.setColorAt(0, QColor(255, 255, 255, 95))
        hl.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(hl)
        p.drawEllipse(QPointF(cx, cy), r, r)
        ed = QRadialGradient(cx, cy, r)
        ed.setColorAt(0.72, QColor(0, 0, 0, 0))
        ed.setColorAt(1.0, QColor(0, 0, 0, 110))
        p.setBrush(ed)
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.setClipping(False)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 55), 1.2))
        p.drawEllipse(QPointF(cx, cy), r, r)
        # дуги «думаю»
        if self.mode == "arcs":
            rr = r * 1.2
            rect = QRectF(cx - rr, cy - rr, 2 * rr, 2 * rr)
            p.setPen(QPen(_al(c2, 230), 3, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, int((-t * 210) % 360 * 16), 95 * 16)
            p.setPen(QPen(_al(c1, 200), 3, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, int((-t * 210 + 180) % 360 * 16), 95 * 16)

# ---------- мастер первого запуска ----------
class Wizard(QDialog):
    def __init__(self, cfg):
        super().__init__()
        import psutil
        ram = psutil.virtual_memory().total / 1e9
        self._ram = f"{ram:.0f}"
        self.setWindowTitle(t("wizard_title"))
        self.setWindowIcon(make_icon())
        self.setMinimumWidth(460)
        orb = Orb(170)
        orb.set_state("idle")
        title = QLabel(t("wizard_hello"))
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        hint = QLabel(t("wizard_hint"))
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color:#8b93a7")
        self.name = QLineEdit()
        self.name.setObjectName("name")
        self.name.setPlaceholderText(t("wizard_placeholder"))
        mlab = QLabel(t("wizard_model", ram=f"{ram:.0f}"))
        mlab.setWordWrap(True)
        mlab.setStyleSheet("color:#8b93a7")
        self.model = QComboBox()
        self.model.addItems(["qwen2.5:7b", "qwen2.5:3b", "llama3.1:8b"])
        self.model.setCurrentIndex(0 if ram >= 15 else 1)
        ilab = QLabel("Язык интерфейса / Interface language")
        ilab.setStyleSheet("color:#8b93a7")
        self.ui_lang = QComboBox()
        self.ui_lang.addItem("Русский", "ru")
        self.ui_lang.addItem("English", "en")
        self.ui_lang.setCurrentIndex(max(self.ui_lang.findData(cfg.get("app_language", "ru")), 0))
        self.ui_lang.currentIndexChanged.connect(lambda: (i18n.set_lang(self.ui_lang.currentData()), self.retranslate()))
        ok = QPushButton(t("wizard_next"))
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept_it)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 26)
        lay.setSpacing(10)
        for w in (orb, title, hint, self.name, mlab, self.model, ilab, self.ui_lang):
            lay.addWidget(w)
        lay.addSpacing(8)
        lay.addWidget(ok)
        self._w = dict(title=title, hint=hint, mlab=mlab, ok=ok)
        self.result_cfg = {}

    def retranslate(self):
        w = self._w
        self.setWindowTitle(t("wizard_title"))
        w["title"].setText(t("wizard_hello"))
        w["hint"].setText(t("wizard_hint"))
        self.name.setPlaceholderText(t("wizard_placeholder"))
        w["mlab"].setText(t("wizard_model", ram=self._ram))
        w["ok"].setText(t("wizard_next"))

    def accept_it(self):
        n = self.name.text().strip()
        if not n:
            self.name.setFocus()
            return
        self.result_cfg = {"assistant_name": n, "llm_model": self.model.currentText(),
                           "app_language": self.ui_lang.currentData()}
        self.accept()

class SettingsDialog(QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        import sounddevice as sd
        from PySide6.QtWidgets import QCheckBox, QSlider, QFormLayout
        self.cfg = cfg
        self.setWindowTitle(t("tip_settings"))
        self.setWindowIcon(make_icon())
        self.setMinimumWidth(460)
        def devs(kind):
            c = QComboBox()
            c.addItem("По умолчанию", None)
            try:
                for i, d in enumerate(sd.query_devices()):
                    if d[kind] > 0:
                        c.addItem(f"{i}: {d['name'][:40]}", i)
            except Exception:
                pass
            return c
        self.mic, self.spk = devs("max_input_channels"), devs("max_output_channels")
        for combo, key in ((self.mic, "input_device"), (self.spk, "output_device")):
            ix = combo.findData(cfg.get(key))
            combo.setCurrentIndex(max(ix, 0))
        self.name = QLineEdit(cfg["assistant_name"])
        self.name.setObjectName("name")
        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.addItems(["qwen2.5:7b", "qwen2.5:3b", "qwen2.5:14b", "llama3.1:8b"])
        self.model.setCurrentText(cfg["llm_model"])
        self.ui_lang = QComboBox()
        self.ui_lang.addItem("Русский", "ru")
        self.ui_lang.addItem("English", "en")
        self.ui_lang.setCurrentIndex(max(self.ui_lang.findData(cfg.get("app_language", "ru")), 0))
        self.lang = QComboBox()
        for lbl, v in (("Авто (RU/EN)", "auto"), ("Русский", "ru"), ("English", "en")):
            self.lang.addItem(lbl, v)
        self.lang.setCurrentIndex(max(self.lang.findData(cfg.get("language", "auto")), 0))
        self.vad = QSlider(Qt.Horizontal)
        self.vad.setRange(3, 60)
        self.vad.setValue(int(cfg["vad_threshold"] * 1000))
        self.vad_l = QLabel()
        self.vad.valueChanged.connect(lambda v: self.vad_l.setText(f"{v/1000:.3f}  " + t("set_sens_hint")))
        self.vad_l.setText(f"{cfg['vad_threshold']:.3f}  " + t("set_sens_hint"))
        self.auto = QCheckBox(t("set_autostart"))
        self.auto.setChecked(bool(cfg.get("autostart")))
        self.stealth = QCheckBox(t("set_stealth"))
        self.stealth.setChecked(bool(cfg.get("stealth")))
        self.barge = QCheckBox(t("set_barge"))
        self.barge.setChecked(bool(cfg.get("barge_in")))
        self.hk = {}
        form = QFormLayout()
        form.setSpacing(10)
        form.addRow(t("set_name"), self.name)
        form.addRow(t("set_mic"), self.mic)
        form.addRow(t("set_speakers"), self.spk)
        form.addRow(t("set_model"), self.model)
        form.addRow(t("set_ui_lang"), self.ui_lang)
        form.addRow(t("set_stt_lang"), self.lang)
        form.addRow(t("set_sens"), self.vad)
        form.addRow("", self.vad_l)
        for key, label in (("hotkey_ptt", t("set_hk_talk")), ("hotkey_stop", t("set_hk_stop")),
                           ("hotkey_show", t("set_hk_show")), ("hotkey_quit", t("set_hk_quit"))):
            e = QLineEdit(cfg[key])
            e.setObjectName("name")
            self.hk[key] = e
            form.addRow(label, e)
        ok = QPushButton(t("set_save"))
        ok.setObjectName("primary")
        ok.clicked.connect(self.save)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 22, 26, 22)
        lay.setSpacing(12)
        _ttl = QLabel(t("tip_settings"))
        _ttl.setObjectName("title")
        lay.addWidget(_ttl)
        lay.addLayout(form)
        for w in (self.auto, self.stealth, self.barge):
            lay.addWidget(w)
        lay.addWidget(ok)

    def save(self):
        c = self.cfg
        c["assistant_name"] = self.name.text().strip() or c["assistant_name"]
        c["input_device"], c["output_device"] = self.mic.currentData(), self.spk.currentData()
        c["llm_model"], c["language"] = self.model.currentText().strip(), self.lang.currentData()
        c["app_language"] = self.ui_lang.currentData()
        c["vad_threshold"] = self.vad.value() / 1000
        c["autostart"], c["stealth"], c["barge_in"] = self.auto.isChecked(), self.stealth.isChecked(), self.barge.isChecked()
        for k, e in self.hk.items():
            c[k] = e.text().strip() or c[k]
        self.accept()

# ---------- диалог ----------
class ChatView(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.viewport().setAutoFillBackground(False)
        inner = QWidget()
        self.lay = QVBoxLayout(inner)
        self.lay.setContentsMargins(4, 4, 10, 4)
        self.lay.setSpacing(8)
        self.lay.addStretch()
        self.setWidget(inner)

    def add(self, who, text):
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        lab = QLabel(text)
        lab.setWordWrap(True)
        lab.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if who == "user":
            lab.setMaximumWidth(380)
            lab.setStyleSheet("background:rgba(255,255,255,0.09);border:1px solid rgba(255,255,255,0.12);"
                              "border-radius:18px;padding:10px 16px;color:#f4f6fc;")
            h.addStretch()
            h.addWidget(lab)
        elif who == "assistant":
            lab.setMaximumWidth(380)
            lab.setStyleSheet("background:rgba(99,102,241,0.16);border:1px solid rgba(129,140,248,0.35);"
                              "border-radius:18px;padding:10px 16px;color:#f4f6fc;")
            h.addWidget(lab)
            h.addStretch()
        else:
            lab.setStyleSheet("color:#5b6482;font-size:12px;padding:0 6px;")
            lab.setAlignment(Qt.AlignCenter)
            h.addWidget(lab)
        self.lay.insertWidget(self.lay.count() - 1, row)
        QTimer.singleShot(40, lambda: self.verticalScrollBar().setValue(self.verticalScrollBar().maximum()))

# ---------- главное окно ----------
class MainWindow(QWidget):
    def __init__(self, bus, asst, cfg):
        super().__init__()
        self.asst, self.name = asst, cfg["assistant_name"]
        self.setWindowTitle(self.name)
        self.setWindowIcon(make_icon())
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(420, 620)
        scr = QApplication.primaryScreen().availableGeometry()
        self.resize(470, min(800, scr.height() - 60))

        # шапка
        dot = QLabel()
        dot.setPixmap(make_icon().pixmap(26, 26))
        title = QLabel(self.name.upper())
        f = QFont("Segoe UI", 10, QFont.DemiBold)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 3)
        title.setFont(f)
        title.setStyleSheet("color:#c7cde0")
        gear = QPushButton("⚙")
        gear.setObjectName("win")
        gear.setToolTip(t("tip_settings"))
        gear.clicked.connect(self.open_settings)
        mini, close = QPushButton("–"), QPushButton("✕")
        mini.setObjectName("win")
        close.setObjectName("winclose")
        mini.setToolTip(t("tip_minimize"))
        mini.clicked.connect(self.showMinimized)
        close.clicked.connect(self.hide)
        close.setToolTip(t("tip_close"))
        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(dot)
        head.addWidget(title)
        head.addStretch()
        head.addWidget(gear)
        head.addWidget(mini)
        head.addWidget(close)

        # сфера и статус
        self.orb = Orb(270)
        self.orb.set_state("think")
        self.status = QLabel(t("status_start"))
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setFont(QFont("Segoe UI Light", 22))
        self.status.setStyleSheet("color:white")
        self.sub = QLabel("")
        self.sub.setAlignment(Qt.AlignCenter)
        self.sub.setStyleSheet("color:#8b93a7;font-size:13px")

        self.chat = ChatView()
        self.chat.add("system", t("chat_empty"))

        # подтверждение
        self.conf = QFrame()
        self.conf.setObjectName("confirm")
        cl = QHBoxLayout(self.conf)
        cl.setContentsMargins(18, 12, 14, 12)
        q = QLabel(t("confirm_text"))
        q.setStyleSheet("color:#fcd34d;font-weight:600")
        yes, no = QPushButton(t("yes")), QPushButton(t("no"))
        yes.setObjectName("yes")
        no.setObjectName("no")
        yes.clicked.connect(lambda: asst.answer_confirm(True))
        no.clicked.connect(lambda: asst.answer_confirm(False))
        cl.addWidget(q)
        cl.addStretch()
        cl.addWidget(yes)
        cl.addWidget(no)
        self.conf.hide()

        # панель ввода
        bar = QFrame()
        bar.setObjectName("bar")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(8, 6, 8, 6)
        bl.setSpacing(6)
        mic = QPushButton()
        mic.setObjectName("mic")
        mic.setIcon(icon_mic())
        mic.setIconSize(QSize(22, 22))
        mic.setToolTip(t("tip_mic"))
        mic.clicked.connect(asst.ptt)
        self.inp = QLineEdit()
        self.inp.setObjectName("input")
        self.inp.setPlaceholderText(t("input_placeholder"))
        self.inp.returnPressed.connect(self.send)
        send = QPushButton()
        send.setObjectName("send")
        send.setIcon(icon_send())
        send.setIconSize(QSize(18, 18))
        send.clicked.connect(self.send)
        stop = QPushButton(t("stop"))
        stop.setObjectName("stop")
        stop.setToolTip(t("tip_stop"))
        stop.clicked.connect(asst.stop)
        bl.addWidget(mic)
        bl.addWidget(self.inp, 1)
        bl.addWidget(send)
        bl.addWidget(stop)

        hint = QLabel(t("hint_keys"))
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color:#4b5470;font-size:11px")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 16, 22, 14)
        lay.setSpacing(8)
        lay.addLayout(head)
        lay.addWidget(self.orb)
        lay.addWidget(self.status)
        lay.addWidget(self.sub)
        lay.addWidget(self.chat, 1)
        lay.addWidget(self.conf)
        lay.addWidget(bar)
        lay.addWidget(hint)

        self.grip = QSizeGrip(self)
        bus.log.connect(self.chat.add)
        bus.status.connect(self.set_state)
        bus.confirm_show.connect(self.conf.setVisible)
        bus.show_window.connect(self.bring_up)
        bus.quit_app.connect(self.quit_all)
        bus.notify.connect(self._notify)
        self.cfg = cfg
        self.set_state(t("st_loading"))

        self.repaint_timer = QTimer(self)
        self.repaint_timer.timeout.connect(self.update)
        self.repaint_timer.start(70)

        self.tray = QSystemTrayIcon(make_icon(), self)
        menu = QMenu()
        a1, a2 = QAction(t("tray_show"), self), QAction(t("tray_quit"), self)
        a1.triggered.connect(self.showNormal)
        a2.triggered.connect(self.quit_all)
        menu.addAction(a1)
        menu.addAction(a2)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda r: self.showNormal() if r == QSystemTrayIcon.Trigger else None)
        if not cfg.get("stealth"):
            self.tray.show()

        self.fade = QPropertyAnimation(self, b"windowOpacity")
        self.fade.setDuration(500)
        self.fade.setStartValue(0.0)
        self.fade.setEndValue(1.0)

    def showEvent(self, e):
        super().showEvent(e)
        self.fade.start()

    def set_state(self, text):
        st = state_for(text)
        self.orb.set_state(st)
        main, _, extra = text.partition(":")
        main = main.rstrip("… ").strip()
        if st == "idle" and main.lower() in ("слушаю", "listening"):
            main = i18n.t("st_listening")
        self.status.setText(main)
        if st == "idle":
            self.sub.setText(t("say_listen", name=self.name))
        else:
            self.sub.setText(extra.strip())

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 28, 28)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor("#10173a"))
        g.setColorAt(1, QColor("#070a15"))
        p.fillPath(path, g)
        p.setClipPath(path)
        glow = QRadialGradient(self.width() / 2, 190, self.width() * 0.8)
        glow.setColorAt(0, _al(self.orb.c1, 60))
        glow.setColorAt(1, _al(self.orb.c1, 0))
        p.fillRect(self.rect(), glow)
        p.setClipping(False)
        p.setPen(QPen(QColor(255, 255, 255, 30), 1))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.grip.move(self.width() - 24, self.height() - 24)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.position().y() < 56 and self.windowHandle():
            self.windowHandle().startSystemMove()

    def _notify(self, title, text):
        try:
            self.tray.showMessage(title, text, make_icon(), 8000)
        except Exception:
            pass

    def bring_up(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def open_settings(self):
        from . import config, system
        d = SettingsDialog(self.cfg, self)
        if d.exec() == QDialog.Accepted:
            config.save(self.cfg)
            try:
                system.set_autostart(bool(self.cfg.get("autostart")))
            except Exception as e:
                self.chat.add("system", t("sys_autostart_fail", e=e))
            self.name = self.cfg["assistant_name"]
            i18n.set_lang(self.cfg.get("app_language", "ru"))
            self.chat.add("system", t("settings_saved"))

    def send(self):
        t = self.inp.text().strip()
        if t:
            self.inp.clear()
            self.asst.submit_text(t)

    def quit_all(self):
        self.asst.shutdown()
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, e):
        e.ignore()
        self.hide()
