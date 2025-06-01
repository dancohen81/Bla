import os
import numpy as np
import sounddevice as sd
import requests
import threading
from PyQt5 import QtWidgets, QtGui, QtCore
import dotenv

dotenv.load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "ZthjuvLPty3kTMaNKVKb")
SAMPLERATE = 16000

class ElevenLabsInputWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Eleven Labs Text-to-Speech")
        self.setGeometry(200, 200, 400, 250)
        self.setStyleSheet("""
            QWidget {
                background-color: #222222; /* Dark background */
                color: #ffffff; /* White text */
            }
        """)

        layout = QtWidgets.QVBoxLayout()

        self.text_input = QtWidgets.QTextEdit(self)
        self.text_input.setPlaceholderText("Geben Sie hier den Text für Eleven Labs ein...")
        self.text_input.setStyleSheet("""
            QTextEdit {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.text_input)

        self.speak_button = QtWidgets.QPushButton("Text vorlesen lassen", self)
        self.speak_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ff9800; /* Orange border */
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 10pt;
                margin: 4px 2px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 152, 0, 0.2); /* Slight orange tint on hover */
            }
        """)
        layout.addWidget(self.speak_button)

        # Add Stop and Resume buttons
        self.stop_button = QtWidgets.QPushButton("Wiedergabe stoppen", self)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ff9800; /* Orange border */
                color: white;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 9pt;
                margin: 4px 2px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 152, 0, 0.2);
            }
        """)
        self.stop_button.setEnabled(False) # Disabled initially
        layout.addWidget(self.stop_button)

        self.resume_button = QtWidgets.QPushButton("Wiedergabe fortsetzen", self)
        self.resume_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ff9800; /* Orange border */
                color: white;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 9pt;
                margin: 4px 2px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 152, 0, 0.2);
            }
        """)
        self.resume_button.setEnabled(False) # Disabled initially
        layout.addWidget(self.resume_button)

        self.status_label = QtWidgets.QTextEdit(self)
        self.status_label.setReadOnly(True)
        self.status_label.setText("Bereit")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QTextEdit {
                color: #ffffff;
                font-size: 9pt;
                background-color: #333333; /* Darker background */
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        self.status_label.setFixedHeight(50) # Give it some height
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.speak_button.clicked.connect(self.send_text_to_eleven_labs)
        self.stop_button.clicked.connect(self.stop_playback)
        self.resume_button.clicked.connect(self.resume_playback)

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

        # Run API calls and playback in a separate thread to keep UI responsive
        threading.Thread(target=self._process_and_play_chunks, args=(text,)).start()

    def _split_text_into_chunks(self, text, max_chars=500):
        """Splits text into chunks, trying to respect sentence boundaries."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += (sentence + " ").strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = (sentence + " ").strip()
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def _process_and_play_chunks(self, full_text):
        chunks = self._split_text_into_chunks(full_text)
        total_chunks = len(chunks)

        try:
            for i, chunk_text in enumerate(chunks):
                QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"Verarbeite Chunk {i+1}/{total_chunks}..."))
                
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": ELEVENLABS_API_KEY
                }
                data = {
                    "text": chunk_text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                }

                response = requests.post(url, headers=headers, json=data, stream=True)
                response.raise_for_status()

                audio_data = b""
                for chunk in response.iter_content(chunk_size=1024):
                    audio_data += chunk

                # Save the audio to a temporary file for pydub to load
                temp_audio_file = "temp_elevenlabs_chunk.mp3"
                with open(temp_audio_file, "wb") as f:
                    f.write(audio_data)

                QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"Spiele Chunk {i+1}/{total_chunks} ab..."))
                self._play_audio_file_chunk(temp_audio_file) # Play this chunk
                os.remove(temp_audio_file) # Clean up temp file

            QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, "Wiedergabe abgeschlossen."))

        except requests.exceptions.RequestException as e:
            QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"Fehler bei Eleven Labs API: {e}"))
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f"Ein unerwarteter Fehler ist aufgetreten: {e}"))
        finally:
            QtCore.QMetaObject.invokeMethod(self.speak_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, True))
            QtCore.QMetaObject.invokeMethod(self.stop_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, False))
            QtCore.QMetaObject.invokeMethod(self.resume_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, False))
            # No need to remove AUDIO_OUTPUT_FILENAME as we use temp_audio_file

    def _play_audio_file_chunk(self, file_path):
        try:
            import shutil
            from pydub import AudioSegment

            if not shutil.which("ffmpeg") and not shutil.which("ffprobe"):
                error_msg = "Fehler: FFmpeg/FFprobe nicht im PATH gefunden. Bitte installieren Sie FFmpeg und fügen Sie es Ihrem System-PATH hinzu."
                print(error_msg)
                QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, error_msg))
                return

            audio = AudioSegment.from_file(file_path)
            self.audio_data_to_play = np.array(audio.set_frame_rate(SAMPLERATE).set_channels(1).set_sample_width(2).get_array_of_samples())
            self.playback_position = 0

            self.playback_stream = sd.OutputStream(samplerate=SAMPLERATE, channels=1, dtype='int16', callback=self._playback_callback)
            self.playback_stream.start()

            QtCore.QMetaObject.invokeMethod(self.stop_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, True))
            QtCore.QMetaObject.invokeMethod(self.resume_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, False))
            # Wait for this chunk to finish playing before returning
            while self.playback_stream.is_active:
                sd.sleep(100) # Sleep briefly to avoid busy-waiting

        except ImportError:
            error_msg = "Fehler: pydub nicht installiert. Bitte 'pip install pydub' ausführen."
            print(error_msg)
            QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Fehler beim Abspielen der Audiodatei: {e}"
            print(error_msg)
            QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, error_msg))
            QtCore.QMetaObject.invokeMethod(self.stop_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, False))
            QtCore.QMetaObject.invokeMethod(self.resume_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, False))

    def _playback_callback(self, outdata, frames, time, status):
        if status:
            print(status)
        chunk_size = frames
        remaining_data = len(self.audio_data_to_play) - self.playback_position
        if remaining_data >= chunk_size:
            outdata[:] = self.audio_data_to_play[self.playback_position:self.playback_position + chunk_size].reshape(-1, 1)
            self.playback_position += chunk_size
        else:
            outdata[:remaining_data] = self.audio_data_to_play[self.playback_position:].reshape(-1, 1)
            outdata[remaining_data:] = 0 # Fill remaining with zeros
            self.playback_position += remaining_data
            # Playback finished for this chunk
            # The main loop in _process_and_play_chunks will handle overall status
            if self.playback_stream:
                self.playback_stream.stop()
                self.playback_stream.close()
                self.playback_stream = None

    def stop_playback(self):
        if self.playback_stream and self.playback_stream.is_active:
            self.playback_stream.stop()
            QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, "Wiedergabe gestoppt."))
            QtCore.QMetaObject.invokeMethod(self.stop_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, False))
            QtCore.QMetaObject.invokeMethod(self.resume_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, True))

    def resume_playback(self):
        if self.playback_stream and not self.playback_stream.is_active:
            if self.playback_position < len(self.audio_data_to_play):
                self.playback_stream = sd.OutputStream(samplerate=SAMPLERATE, channels=1, dtype='int16', callback=self._playback_callback)
                self.playback_stream.start()
                QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, "Wiedergabe fortgesetzt..."))
                QtCore.QMetaObject.invokeMethod(self.stop_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, True))
                QtCore.QMetaObject.invokeMethod(self.resume_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, False))
            else:
                QtCore.QMetaObject.invokeMethod(self, "set_status", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, "Keine weiteren Daten zum Abspielen."))
                QtCore.QMetaObject.invokeMethod(self.stop_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, False))
                QtCore.QMetaObject.invokeMethod(self.resume_button, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, False))
