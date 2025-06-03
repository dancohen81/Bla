# Add the parent directory of src to sys.path to allow absolute imports
# when running tray_sprachtool.py directly from the src directory.
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import datetime
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
import pyperclip
import openai
import winsound
import threading
from PyQt5 import QtWidgets, QtGui, QtCore
import dotenv
from pynput import keyboard

from src.elevenlabs_window import ElevenLabsInputWindow
from src.status_window import StatusWindow
from src.config import SAMPLERATE, FILENAME, ICON_PATH, MIN_RECORDING_DURATION_SECONDS, SILENCE_THRESHOLD, setup_autostart

dotenv.load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

class TrayRecorder(QtWidgets.QSystemTrayIcon):
    def __init__(self, app):
        self.icon_idle = QtGui.QIcon("mic_idle.png")
        self.icon_active = QtGui.QIcon("mic_active.png")
        super().__init__(self.icon_idle)
        self.setToolTip("Sprachaufnahme bereit")

        self.clipboard_history = ["", ""] # Stores the last two clipboard contents

        # Start global hotkey listener in a separate thread
        self.hotkey_listener_thread = threading.Thread(target=self._start_hotkey_listener, daemon=True)
        self.hotkey_listener_thread.start()

        self.menu = QtWidgets.QMenu()
        self.menu.addAction("Fenster anzeigen", self.show_window)
        self.menu.addAction("Autostart aktivieren", setup_autostart)
        self.menu.addSeparator()
        self.menu.addAction("Beenden", QtWidgets.qApp.quit)
        self.setContextMenu(self.menu)

        self.window = StatusWindow()
        self.window.show()
        QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(255, 165, 0))) # Initial orange

        self.is_recording = False
        self.recording_data = []
        self.stream = None

        self.activated.connect(self.icon_clicked)
        
        # Connect the Eleven Labs button
        self.eleven_labs_input_window = ElevenLabsInputWindow()
        self.window.eleven_labs_button.clicked.connect(self.open_eleven_labs_window)

        # Connect the new record button
        self.window.record_button.clicked.connect(self.toggle_recording_button)

    def _start_hotkey_listener(self):
        # Define the hotkey combination (Ctrl + Shift + V)
        # On Windows, 'ctrl' is typically 'ctrl_l' or 'ctrl_r', 'shift' is 'shift_l' or 'shift_r'
        # We'll use a generic check for 'ctrl' and 'shift'
        COMBINATIONS = [
            {keyboard.Key.ctrl_l, keyboard.Key.shift_l, keyboard.KeyCode.from_char('v')},
            {keyboard.Key.ctrl_r, keyboard.Key.shift_r, keyboard.KeyCode.from_char('v')},
            {keyboard.Key.ctrl_l, keyboard.Key.shift_r, keyboard.KeyCode.from_char('v')},
            {keyboard.Key.ctrl_r, keyboard.Key.shift_l, keyboard.KeyCode.from_char('v')},
        ]

        current_keys = set()

        def on_press(key):
            try:
                current_keys.add(key)
                # Check for F3 to start recording
                if key == keyboard.Key.f3 and not self.is_recording:
                    QtCore.QMetaObject.invokeMethod(self, "start_recording", QtCore.Qt.QueuedConnection)
                # Check for F4 to cancel recording
                elif key == keyboard.Key.f4 and self.is_recording:
                    QtCore.QMetaObject.invokeMethod(self, "cancel_recording", QtCore.Qt.QueuedConnection)

                for combination in COMBINATIONS:
                    if all(k in current_keys for k in combination):
                        # Hotkey detected, trigger the action
                        QtCore.QMetaObject.invokeMethod(self, "_paste_previous_clipboard", QtCore.Qt.QueuedConnection)
                        break # Only trigger once per press
            except AttributeError:
                pass # Special keys like Key.space, Key.esc etc. have no .char attribute

        def on_release(key):
            try:
                if key == keyboard.Key.f3 and self.is_recording:
                    QtCore.QMetaObject.invokeMethod(self, "stop_recording", QtCore.Qt.QueuedConnection)
                if key in current_keys:
                    current_keys.remove(key)
            except KeyError:
                pass # Key not in set, ignore

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

    def _paste_previous_clipboard(self):
        if len(self.clipboard_history) > 1 and self.clipboard_history[-2]:
            text_to_paste = self.clipboard_history[-2]
            pyperclip.copy(text_to_paste)
            QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"📋 Zweitletztes kopiert:\n{text_to_paste[:60]}{'...' if len(text_to_paste) > 60 else ''}"))
            
            # Simulate Ctrl+V to paste the content
            keyboard.Controller().press(keyboard.Key.ctrl_l)
            keyboard.Controller().press(keyboard.KeyCode.from_char('v'))
            keyboard.Controller().release(keyboard.KeyCode.from_char('v'))
            keyboard.Controller().release(keyboard.Key.ctrl_l)
        else:
            QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, "⚠️ Keine frühere Zwischenablage verfügbar."))

    def icon_clicked(self, reason):
        if reason == self.Trigger:
            self.show_window()

    def show_window(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def open_eleven_labs_window(self):
        self.eleven_labs_input_window.show()
        self.eleven_labs_input_window.raise_()
        self.eleven_labs_input_window.activateWindow()

    @QtCore.pyqtSlot()
    def toggle_recording_button(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    @QtCore.pyqtSlot()
    def start_recording(self):
        self.setIcon(self.icon_active)
        QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(255, 0, 0))) # Red for recording
        
        # Update button appearance using QTimer.singleShot for thread-safety
        QtCore.QTimer.singleShot(0, lambda: self.window.record_button.setText("■")) # Stop symbol
        QtCore.QTimer.singleShot(0, lambda: self.window.record_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ff9800; /* Orange border */
                color: white;
                font-size: 16pt;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 152, 0, 0.2);
            }
        """))

        try:
            self.recording_data = []
            self.stream = sd.InputStream(samplerate=SAMPLERATE, channels=1, dtype='int16', callback=self.audio_callback)
            self.stream.start()
            self.is_recording = True
            winsound.Beep(1000, 120)
            QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, "🎙️ Aufnahme läuft..."))
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"❌ Fehler: {e}"))
            QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(255, 165, 0))) # Back to orange on error
            
            QtCore.QTimer.singleShot(0, lambda: self.window.record_button.setText("🎙️")) # Back to mic symbol
            QtCore.QTimer.singleShot(0, lambda: self.window.record_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #ff9800; /* Orange border */
                    color: white;
                    font-size: 16pt;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 152, 0, 0.2);
                }
            """))

    @QtCore.pyqtSlot()
    def cancel_recording(self):
        if self.is_recording:
            try:
                self.stream.stop()
                self.stream.close()
                self.is_recording = False
                self.recording_data = [] # Discard recorded data
                winsound.Beep(400, 100) # Different beep for cancellation
                winsound.Beep(300, 100)
                QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, "🚫 Aufnahme abgebrochen."))
                QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(255, 165, 0))) # Back to orange
            except Exception as e:
                QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"❌ Fehler: {e}"))
                QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(255, 165, 0))) # Back to orange on error
        self.setIcon(self.icon_idle)
        
        QtCore.QTimer.singleShot(0, lambda: self.window.record_button.setText("🎙️")) # Back to mic symbol
        QtCore.QTimer.singleShot(0, lambda: self.window.record_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ff9800; /* Orange border */
                color: white;
                font-size: 16pt;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 152, 0, 0.2);
            }
        """))

    @QtCore.pyqtSlot()
    def stop_recording(self):
        self.setIcon(self.icon_idle)
        QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(0, 255, 0))) # Green for processing
        
        QtCore.QTimer.singleShot(0, lambda: self.window.record_button.setText("🎙️")) # Back to mic symbol
        QtCore.QTimer.singleShot(0, lambda: self.window.record_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ff9800; /* Orange border */
                color: white;
                font-size: 16pt;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 152, 0, 0.2);
            }
        """))

        try:
            self.stream.stop()
            self.stream.close()
            self.is_recording = False
            winsound.Beep(800, 100)
            winsound.Beep(600, 100)
            QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, "🔁 Verarbeite..."))
            # Start processing in a new thread
            processing_thread = threading.Thread(target=self.process_audio)
            processing_thread.start()
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"❌ Fehler: {e}"))
            QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(255, 165, 0))) # Back to orange on error

    def audio_callback(self, indata, frames, time, status):
        if status:
            pass # Removed print(status)
        self.recording_data.append(indata.copy())

    def process_audio(self):
        if not self.recording_data:
            QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, "⚠️ Keine Daten aufgenommen."))
            return
        
        audio_data = np.concatenate(self.recording_data, axis=0)
        
        # Calculate duration of the recording
        duration = len(audio_data) / SAMPLERATE

        if duration < MIN_RECORDING_DURATION_SECONDS:
            QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"⚠️ Aufnahme zu kurz ({duration:.1f}s). Mindestens {MIN_RECORDING_DURATION_SECONDS}s benötigt."))
            QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(255, 165, 0))) # Back to orange
            self.recording_data = [] # Clear data for next recording
            return
        
        # Check if the recording is essentially silent (empty)
        max_amplitude = np.max(np.abs(audio_data))
        if max_amplitude < SILENCE_THRESHOLD:
            QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"⚠️ Aufnahme ist leer (Amplitude: {max_amplitude})."))
            QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(255, 165, 0))) # Back to orange
            self.recording_data = [] # Clear data for next recording
            return

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
            with open("transkript_log.txt", "a", encoding="utf-8") as logf:
                logf.write(f"{datetime.datetime.now()}: {text}\n\n")

            # Update clipboard history
            self.clipboard_history.append(text)
            if len(self.clipboard_history) > 2: # Keep only the last two items
                self.clipboard_history = self.clipboard_history[-2:]
            
            pyperclip.copy(text)
            QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"✅ Kopiert:\n{text[:60]}{'...' if len(text) > 60 else ''}"))
            QtCore.QMetaObject.invokeMethod(self.window, "showNormal", QtCore.Qt.QueuedConnection) # Restore if minimized
            QtCore.QMetaObject.invokeMethod(self.window, "raise", QtCore.Qt.QueuedConnection) # Bring to front
            QtCore.QMetaObject.invokeMethod(self.window, "_activate_window", QtCore.Qt.QueuedConnection) # Activate window
            # Green pulse and fade back to orange
            QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(0, 255, 0))) # Ensure green pulse
            QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(255, 165, 0))) # Fade back to orange
        except Exception as e:
            error_message = f"❌ Transkriptionsfehler: {str(e)}" # Explicitly convert e to string
            QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, error_message))
            QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(255, 165, 0))) # Back to orange on error
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
