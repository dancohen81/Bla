import os
import sys
import pythoncom
from win32com.client import Dispatch

# Global Constants
SAMPLERATE = 16000
FILENAME = "aufnahme.wav"
AUDIO_OUTPUT_FILENAME = "elevenlabs_output.mp3" # For Eleven Labs audio output
MIN_RECORDING_DURATION_SECONDS = 1 # Minimum duration for a recording to be processed by Whisper
SILENCE_THRESHOLD = 200 # Maximum absolute amplitude for audio to be considered silent

ICON_PATH = os.path.join(os.path.dirname(__file__), "..", "mic_icon.png") # Adjusted path

# Autostart-Link (Windows)
def setup_autostart():
    autostart_dir = os.path.join(os.getenv("APPDATA"), "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
    shortcut_path = os.path.join(autostart_dir, "SprachTray.lnk")
    if not os.path.exists(shortcut_path):
        try:
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = sys.executable
            # Adjust path to the main script in src folder
            shortcut.Arguments = f'"{os.path.abspath(os.path.join(os.path.dirname(__file__), "tray_sprachtool.py"))}"'
            shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            shortcut.IconLocation = ICON_PATH
            shortcut.save()
        except Exception as e:
            pass # Removed print statement
