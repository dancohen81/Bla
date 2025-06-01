@echo off
echo Virtuelle Umgebung wird erstellt...
python -m venv venv

echo Virtuelle Umgebung wird aktiviert...
call venv\Scripts\activate.bat

echo Notwendige Bibliotheken werden installiert...
uv pip install -r src/requirements.txt

rem Spezialfall für PyAudio auf Windows:
rem Falls 'pip install pyaudio' fehlschlägt, könntest du versuchen, ein Wheel zu installieren.
rem Die untenstehende Zeile ist auskommentiert, da sie oft nicht nötig ist und das Wheel
rem von der Python-Version abhängt. Wenn pyaudio fehlt, musst du manuell suchen:
rem https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
rem Beispiel für PyAudio wheel (ersetze mit dem passenden Namen für deine Python-Version):
rem pip install PyAudio-0.2.11-cp310-cp310-win_amd64.whl

echo Installation abgeschlossen.
echo Um die Umgebung zu aktivieren, tippe: call venv\Scripts\activate.bat
echo Um das Skript zu starten, tippe: python -m src.tray_sprachtool
pause
