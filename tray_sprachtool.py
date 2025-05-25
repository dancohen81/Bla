import sys
import os
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
import pyperclip
import openai
import winsound
import shutil
from PyQt5 import QtWidgets, QtGui, QtCore

openai.api_key = os.getenv("OPENAI_API_KEY")
SAMPLERATE = 16000
FILENAME = "aufnahme.wav"

ICON_PATH = os.path.join(os.path.dirname(__file__), "mic_icon.png")  # irgendein kleines Icon

# Autostart-Link (Windows)
def setup_autostart():
    autostart_dir = os.path.join(os.getenv("APPDATA"), "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
    shortcut_path = os.path.join(autostart_dir, "SprachTray.lnk")
    if not os.path.exists(shortcut_path):
        try:
            import pythoncom
            from win32com.client import Dispatch
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = sys.executable
            shortcut.Arguments = f'"{os.path.abspath(__file__)}"'
            shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(__file__))
            shortcut.IconLocation = ICON_PATH
            shortcut.save()
        except Exception as e:
            print(f"Autostart konnte nicht gesetzt werden: {e}")

class StatusWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎤 Sprachaufnahme")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setGeometry(100, 100, 320, 90)

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: Consolas, monospace;
                font-size: 10pt;
                border: 1px solid #333;
            }
        """)

        self.label = QtWidgets.QLabel("Bereit", self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.space_pressed = False
        self.grabKeyboard()

    def set_status(self, text):
        self.label.setText(text)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.space_pressed = True

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.space_pressed = False

class TrayRecorder(QtWidgets.QSystemTrayIcon):
    def __init__(self, app):
        super().__init__(QtGui.QIcon(ICON_PATH if os.path.exists(ICON_PATH) else QtGui.QIcon()))
        self.setToolTip("Sprachaufnahme bereit")

        self.menu = QtWidgets.QMenu()
        self.menu.addAction("Fenster anzeigen", self.show_window)
        self.menu.addAction("Autostart aktivieren", setup_autostart)
        self.menu.addSeparator()
        self.menu.addAction("Beenden", QtWidgets.qApp.quit)
        self.setContextMenu(self.menu)

        self.window = StatusWindow()
        self.window.show()

        self.is_recording = False
        self.recording_data = []
        self.stream = None

        self.activated.connect(self.icon_clicked)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_keys)
        self.timer.start(50)

    def icon_clicked(self, reason):
        if reason == self.Trigger:
            self.show_window()

    def show_window(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def check_keys(self):
        if self.window.space_pressed:
            if not self.is_recording:
                self.start_recording()
        else:
            if self.is_recording:
                self.stop_recording()

    def start_recording(self):
        try:
            self.recording_data = []
            self.stream = sd.InputStream(samplerate=SAMPLERATE, channels=1, dtype='int16', callback=self.audio_callback)
            self.stream.start()
            self.is_recording = True
            winsound.Beep(1000, 120)
            self.window.set_status("🎙️ Aufnahme läuft...")
        except Exception as e:
            self.window.set_status(f"❌ Fehler: {e}")

    def stop_recording(self):
        try:
            self.stream.stop()
            self.stream.close()
            self.is_recording = False
            winsound.Beep(800, 100)
            winsound.Beep(600, 100)
            self.window.set_status("🔁 Verarbeite...")
            self.process_audio()
        except Exception as e:
            self.window.set_status(f"❌ Fehler: {e}")

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.recording_data.append(indata.copy())

    def process_audio(self):
        if not self.recording_data:
            self.window.set_status("⚠️ Keine Daten aufgenommen.")
            return
        audio_data = np.concatenate(self.recording_data, axis=0)
        wavfile.write(FILENAME, SAMPLERATE, audio_data)

        try:
            with open(FILENAME, "rb") as f:
                result = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="text",
                    language="de"
                )
            text = result.strip()
            pyperclip.copy(text)
            self.window.set_status(f"✅ Kopiert:\n{text[:60]}{'...' if len(text) > 60 else ''}")
        except Exception as e:
            self.window.set_status(f"❌ Transkriptionsfehler: {e}")
        finally:
            if os.path.exists(FILENAME):
                os.remove(FILENAME)

def run_app():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    recorder = TrayRecorder(app)
    recorder.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()
