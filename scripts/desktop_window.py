"""Local Qt window hosting the existing React UI and an owned bridge process."""
import os
import secrets
import socket
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from PySide6.QtCore import QProcess, QProcessEnvironment, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

ROOT = Path(__file__).resolve().parents[1]


class Window(QMainWindow):
    def __init__(self, origin, windows):
        super().__init__()
        self.origin, self.windows = origin, windows
        self.setWindowTitle('四宫辉夜 · 日常聊天（AI 合成语音）')
        self.resize(1100, 800)
        self.view = QWebEngineView(self)
        self.view.setPage(Page(self.view.page().profile(), self.view, self))
        self.view.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        self.view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        self.setCentralWidget(self.view)
        windows.append(self)


class Page(QWebEnginePage):
    def __init__(self, profile, parent, window):
        super().__init__(profile, parent)
        self.window = window

    def createWindow(self, _kind):
        child = Window(self.window.origin, self.window.windows)
        child.show()
        return child.view.page()

    def acceptNavigationRequest(self, url, kind, main_frame):
        if main_frame and url.scheme() in ('http', 'https'):
            origin = QUrl(self.window.origin)
            if url.host() != origin.host() or url.port() != origin.port():
                QDesktopServices.openUrl(url)
                return False
        return super().acceptNavigationRequest(url, kind, main_frame)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('四宫辉夜')
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    token = secrets.token_urlsafe(32)
    process = QProcess(app)
    env = QProcessEnvironment.systemEnvironment()
    env.insert('SHINSEKAI_BRIDGE_AUTH_TOKEN', token)
    process.setProcessEnvironment(env)
    process.setWorkingDirectory(str(ROOT))
    log = ROOT / 'temp/desktop.log'
    log.parent.mkdir(exist_ok=True)
    process.setStandardOutputFile(str(log))
    process.setStandardErrorFile(str(log) + '.errors')
    process.start(sys.executable, [str(ROOT / 'frontend_bridge.py'), '--host', '127.0.0.1', '--port', str(port), '--parent-pid', str(os.getpid())])
    windows = []
    window = Window(origin, windows)
    window.view.setHtml('<h2>正在打开辉夜的聊天窗口…</h2>')
    window.show()
    started = time.monotonic()
    timer = QTimer(app)

    def ready():
        try:
            with urlopen(origin, timeout=0.2) as response:
                if response.status != 200:
                    return
        except Exception:
            if time.monotonic() - started > 60 or process.state() == QProcess.ProcessState.NotRunning:
                timer.stop()
                QMessageBox.critical(window, '启动失败', '请查看项目 temp/desktop.log.errors。')
                app.exit(1)
            return
        timer.stop()
        window.view.load(QUrl(origin + '/?shinsekai_bridge_token=' + token + '#/settings/templates'))
        if '--smoke-test' in sys.argv:
            def loaded(ok):
                print('DESKTOP_PAGE_LOADED=' + str(ok))
                if not ok:
                    app.exit(1)
                    return
                window.view.page().runJavaScript("window.open(location.href, '_blank')")
                def finish():
                    print('DESKTOP_POPUP_CREATED=' + str(len(windows) == 2))
                    app.exit(0 if len(windows) == 2 else 1)
                QTimer.singleShot(2500, finish)
            window.view.loadFinished.connect(loaded)

    def stop():
        process.terminate()
        if not process.waitForFinished(5000):
            process.kill()
            process.waitForFinished(2000)

    app.aboutToQuit.connect(stop)
    timer.timeout.connect(ready)
    timer.start(400)
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
