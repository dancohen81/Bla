import datetime
import sys
import os
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
import pyperclip
import openai
import winsound
import shutil
import threading # Added for background processing
import requests # Added for Eleven Labs API calls
from PyQt5 import QtWidgets, QtGui, QtCore
import dotenv # Added for .env file loading
from pynput import keyboard # Added for global hotkey listening

dotenv.load_dotenv() # Load environment variables from .env file

openai.api_key = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "ZthjuvLPty3kTMaNKVKb") # Default voice ID if not set
# You can find available voice IDs in your Eleven Labs account settings or API documentation.
# For example, a common voice ID for English is "21m00Tzpb8CXL8y4KuD4" or "EXAVITQu4vr4xnSDxMaL"
# For multilingual models, you might need to use a specific voice ID that supports it.

SAMPLERATE = 16000
FILENAME = "aufnahme.wav"
AUDIO_OUTPUT_FILENAME = "elevenlabs_output.mp3" # For Eleven Labs audio output

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

class ElevenLabsInputWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Eleven Labs Text-to-Speech")
        self.setGeometry(200, 200, 400, 250)

        layout = QtWidgets.QVBoxLayout()

        self.text_input = QtWidgets.QTextEdit(self)
        self.text_input.setPlaceholderText("Geben Sie hier den Text für Eleven Labs ein...")
        layout.addWidget(self.text_input)

        self.speak_button = QtWidgets.QPushButton("Text vorlesen lassen", self)
        self.speak_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; /* Blue */
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 10pt;
                margin: 4px 2px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        layout.addWidget(self.speak_button)

        self.status_label = QtWidgets.QTextEdit(self)
        self.status_label.setReadOnly(True)
        self.status_label.setText("Bereit")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QTextEdit {
                color: #555;
                font-size: 9pt;
                background-color: #f0f0f0; /* Light gray background */
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        self.status_label.setFixedHeight(50) # Give it some height
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.speak_button.clicked.connect(self.send_text_to_eleven_labs)

    @QtCore.pyqtSlot(str)
    def set_status(self, text):
        self.status_label.setText(text)
        self.status_label.verticalScrollBar().setValue(self.status_label.verticalScrollBar().minimum()) # Scroll to top

    def send_text_to_eleven_labs(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            self.set_status("Bitte geben Sie Text ein.")
            return

        if not ELEVENLABS_API_KEY:
            self.set_status("Eleven Labs API Key nicht gefunden. Bitte in .env setzen.")
            return

        self.set_status("Sende Text an Eleven Labs...")
        QtCore.QMetaObject.invokeMethod(self.speak_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, False))

        # Run API call in a separate thread to keep UI responsive
        threading.Thread(target=self._call_eleven_labs_api, args=(text,)).start()

    def _call_eleven_labs_api(self, text):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2", # Or "eleven_monolingual_v1" for English only
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        try:
            response = requests.post(url, headers=headers, json=data, stream=True)
            response.raise_for_status() # Raise an exception for HTTP errors

            audio_data = b""
            for chunk in response.iter_content(chunk_size=1024):
                audio_data += chunk

            # Save the audio to a temporary file
            with open(AUDIO_OUTPUT_FILENAME, "wb") as f:
                f.write(audio_data)

            QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, "Spiele Audio ab..."))
            self._play_audio_file(AUDIO_OUTPUT_FILENAME)
            QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, "Wiedergabe abgeschlossen."))

        except requests.exceptions.RequestException as e:
            QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"Fehler bei Eleven Labs API: {e}"))
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"Ein unerwarteter Fehler ist aufgetreten: {e}"))
        finally:
            QtCore.QMetaObject.invokeMethod(self.speak_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, True))
            if os.path.exists(AUDIO_OUTPUT_FILENAME):
                os.remove(AUDIO_OUTPUT_FILENAME)

    def _play_audio_file(self, file_path):
        try:
            import shutil
            from pydub import AudioSegment
            from pydub.playback import play

            # Check if ffmpeg is available
            if not shutil.which("ffmpeg") and not shutil.which("ffprobe"):
                error_msg = "Fehler: FFmpeg/FFprobe nicht im PATH gefunden. Bitte installieren Sie FFmpeg und fügen Sie es Ihrem System-PATH hinzu."
                print(error_msg) # For console debugging
                QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, error_msg))
                return

            # Load the audio file (pydub can handle mp3)
            audio = AudioSegment.from_file(file_path)

            # Convert audio to a NumPy array for sounddevice
            # Ensure the audio is in a format sounddevice can play (e.g., 16-bit PCM)
            audio = audio.set_frame_rate(SAMPLERATE).set_channels(1).set_sample_width(2) # 16-bit PCM
            audio_array = np.array(audio.get_array_of_samples())

            # Play the audio using sounddevice
            sd.play(audio_array, SAMPLERATE)
            sd.wait() # Wait until playback is finished

        except ImportError:
            error_msg = "Fehler: pydub nicht installiert. Bitte 'pip install pydub' ausführen."
            print(error_msg) # For console debugging
            QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Fehler beim Abspielen der Audiodatei: {e}"
            print(error_msg) # For console debugging
            QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, error_msg))

class StatusWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎤 Sprachaufnahme")
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool |
            QtCore.Qt.WindowMinimizeButtonHint
        )
        self.setGeometry(100, 100, 320, 90)

        # Animation properties
        self.animation_phase = 0.0
        self.animation_speed = 0.01 # Very slow animation speed

        # Firefly properties
        self.num_fireflies = 20 # Number of fireflies
        self.fireflies = []
        for i in range(self.num_fireflies):
            self.fireflies.append({
                'x': np.random.uniform(0, self.width()),
                'y': np.random.uniform(0, self.height()),
                'size': np.random.uniform(2, 8), # Size of firefly
                'color_offset': np.random.uniform(0, 1), # For different orange shades
                'phase_offset': np.random.uniform(0, 2 * np.pi), # For pulsating effect
                'speed_factor': np.random.uniform(0.5, 1.5) # Slightly varied speed
            })

        # Current firefly color
        self.current_firefly_color = QtGui.QColor(255, 165, 0) # Start with orange (normal)
        self.target_firefly_color = QtGui.QColor(255, 165, 0)

        # Animation properties for color transition
        self.color_transition_timer = QtCore.QTimer(self)
        self.color_transition_timer.timeout.connect(self.update_firefly_color)
        self.color_transition_speed = 5 # Adjust for slower/faster transition

        # Set up a timer for animation updates
        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.timeout.connect(self.animate_background)
        self.animation_timer.start(50) # Update every 50ms (20 FPS)

        self.label = QtWidgets.QLabel("Bereit", self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: Consolas, monospace;
                font-size: 10pt;
            }
        """)

        self.eleven_labs_button = QtWidgets.QPushButton("Eleven Labs TTS", self)
        self.eleven_labs_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* Green */
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 9pt;
                margin: 4px 2px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        # The connection will be made from TrayRecorder as it manages the new window

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.eleven_labs_button) # Add the new button
        self.setLayout(layout)


    @QtCore.pyqtSlot(str) # Mark as slot for thread-safe updates
    def set_status(self, text):
        self.label.setText(text)

    @QtCore.pyqtSlot()
    def _activate_window(self):
        self.activateWindow()

    @QtCore.pyqtSlot(QtGui.QColor)
    def set_firefly_color(self, color):
        self.target_firefly_color = color
        self.color_transition_timer.start(20) # Start transition

    def update_firefly_color(self):
        # Smoothly transition current_firefly_color towards target_firefly_color
        r = self.current_firefly_color.red()
        g = self.current_firefly_color.green()
        b = self.current_firefly_color.blue()

        target_r = self.target_firefly_color.red()
        target_g = self.target_firefly_color.green()
        target_b = self.target_firefly_color.blue()

        # Move towards target
        r += (target_r - r) / self.color_transition_speed
        g += (target_g - g) / self.color_transition_speed
        b += (target_b - b) / self.color_transition_speed

        self.current_firefly_color = QtGui.QColor(int(r), int(g), int(b))
        self.update() # Request repaint

        # Stop timer if colors are close enough
        if abs(r - target_r) < 1 and abs(g - target_g) < 1 and abs(b - target_b) < 1:
            self.color_transition_timer.stop()
            self.current_firefly_color = self.target_firefly_color # Ensure exact target color

    def animate_background(self):
        self.animation_phase += self.animation_speed
        if self.animation_phase > 2 * np.pi: # Reset phase after a full cycle
            self.animation_phase -= 2 * np.pi

        # Update firefly positions
        for firefly in self.fireflies:
            firefly['x'] += np.sin(self.animation_phase * firefly['speed_factor'] * 0.5) * 0.5 # Slow horizontal wobble
            firefly['y'] += np.cos(self.animation_phase * firefly['speed_factor'] * 0.6) * 0.5 # Slow vertical wobble

            # Wrap around if firefly goes off screen
            if firefly['x'] < -firefly['size']: firefly['x'] = self.width() + firefly['size']
            if firefly['x'] > self.width() + firefly['size']: firefly['x'] = -firefly['size']
            if firefly['y'] < -firefly['size']: firefly['y'] = self.height() + firefly['size']
            if firefly['y'] > self.height() + firefly['size']: firefly['y'] = -firefly['size']

        self.update() # Request a repaint

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Draw black background with subtle gradient
        gradient = QtGui.QRadialGradient(self.width() / 2, self.height() / 2, max(self.width(), self.height()) / 2)
        gradient.setColorAt(0, QtGui.QColor(0, 0, 0)) # Black center
        gradient.setColorAt(1, QtGui.QColor(20, 20, 20)) # Very dark gray at edges
        painter.fillRect(self.rect(), gradient)

        # Draw fireflies
        for firefly in self.fireflies:
            # Pulsating opacity and size
            pulse_factor = (np.sin(self.animation_phase * firefly['speed_factor'] + firefly['phase_offset']) + 1) / 2.0 # 0 to 1

            # Interpolate firefly color based on current_firefly_color and individual color_offset
            r = int(self.current_firefly_color.red() * (0.7 + firefly['color_offset'] * 0.3))
            g = int(self.current_firefly_color.green() * (0.7 + firefly['color_offset'] * 0.3))
            b = int(self.current_firefly_color.blue() * (0.7 + firefly['color_offset'] * 0.3))
            firefly_color = QtGui.QColor(r, g, b, int(255 * (0.3 + pulse_factor * 0.7))) # Vary opacity

            painter.setBrush(QtGui.QBrush(firefly_color))
            painter.setPen(QtCore.Qt.NoPen)

            current_size = firefly['size'] * (0.5 + pulse_factor * 0.5) # Pulsate size
            painter.drawEllipse(int(firefly['x'] - current_size / 2), int(firefly['y'] - current_size / 2), int(current_size), int(current_size))

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
    @QtCore.pyqtSlot()
    def start_recording(self):
        self.setIcon(self.icon_active)
        QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(255, 0, 0))) # Red for recording

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

    @QtCore.pyqtSlot()
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
                QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"❌ Fehler beim Abbrechen: {e}"))
                QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(255, 165, 0))) # Back to orange on error
        self.setIcon(self.icon_idle)

    @QtCore.pyqtSlot()
    def stop_recording(self):
        self.setIcon(self.icon_idle)
        QtCore.QMetaObject.invokeMethod(self.window, "set_firefly_color", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QColor, QtGui.QColor(0, 255, 0))) # Green for processing

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
            print(status)
        self.recording_data.append(indata.copy())

    def process_audio(self):
        if not self.recording_data:
            QtCore.QMetaObject.invokeMethod(self.window, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, "⚠️ Keine Daten aufgenommen."))
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
