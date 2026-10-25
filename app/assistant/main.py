import sys, os, traceback
# в EXE без консоли stdout/stderr отсутствуют — подставляем заглушку, иначе падают загрузчики моделей
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from app import config, i18n
from app.gui import Bus, MainWindow, Wizard, STYLE, make_icon

def main():
    # одиночный экземпляр: иначе два процесса спорят за микрофон и настройки
    from PySide6.QtNetwork import QLocalSocket, QLocalServer
    _SINGLE = "PKAssistantSingleInstance"
    probe = QLocalSocket(); probe.connectToName(_SINGLE)
    if probe.waitForConnected(200):
        probe.write(b"show"); probe.flush(); probe.waitForBytesWritten(500); probe.disconnectFromServer()
        return
    app = QApplication(sys.argv)
    server = QLocalServer(); server.removeServer(_SINGLE); server.listen(_SINGLE)
    win = None
    def _wakeup():
        c = server.nextPendingConnection()
        if c:
            c.deleteLater()
        if win is not None:
            win.bring_up()
    server.newConnection.connect(_wakeup)
    app.setStyleSheet(STYLE)
    app.setWindowIcon(make_icon())
    app.setQuitOnLastWindowClosed(False)
    cfg = config.load()
    i18n.set_lang(cfg.get("app_language", "ru"))
    if not cfg["first_run_done"]:
        w = Wizard(cfg)
        if w.exec() != QDialog.Accepted:
            return
        cfg.update(w.result_cfg)
        cfg["first_run_done"] = True
        config.save(cfg)
    from app.assistant import Assistant
    bus = Bus()
    asst = Assistant(cfg, bus)
    win = MainWindow(bus, asst, cfg)   # noqa: F841 (используется в _wakeup)
    if not cfg.get("stealth"):
        win.show()
    asst.start()
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        try:
            with open(os.path.join(config.DATA, "error.log"), "w", encoding="utf-8") as f:
                f.write(err)
            QMessageBox.critical(None, "Ошибка", "Программа упала. Подробности в файле data\\error.log\n\n" + err[-600:])
        except Exception:
            pass
