# Bla Repository

## Application Overview

This repository contains the source code for a Python application designed to facilitate quick speech-to-text transcription. The application runs silently in the system tray (currently optimized for Windows) and allows users to record audio by simply holding down the spacebar. Once the spacebar is released, the recorded audio is sent to the OpenAI Whisper API for transcription. The resulting text is then automatically copied to the user's clipboard, making it easy to paste into any document or application.

Key features include:
*   **System Tray Integration:** Operates discreetly from the system tray, providing quick access to its functions.
*   **Spacebar-Activated Recording:** Intuitive recording control by pressing and holding the spacebar.
*   **OpenAI Whisper Transcription:** Leverages the powerful Whisper API for accurate speech-to-text conversion.
*   **Automatic Clipboard Copy:** Transcribed text is immediately available for pasting.
*   **Real-time Status Window:** A small pop-up window provides feedback on the application's status (e.g., recording, processing, copied).
*   **Dynamic Firefly Background:** The status window now features a subtle, animated background with pulsating fireflies that change color based on the application's state (orange for idle, red for recording, green for processing/success).
*   **Windows Autostart Option:** Includes functionality to automatically start with Windows.
*   **Audio Feedback:** Provides distinct beeps for recording start and stop events.

## Setup

To run this application, you need to provide your OpenAI API key. This application uses a `.env` file to securely load your API key as an environment variable.

### 1. Create a `.env` file

Create a file named `.env` in the root directory of the project (where `tray_sprachtool.py` is located). Add your OpenAI API key to this file in the following format:

```
OPENAI_API_KEY="your_openai_api_key_here"
```
Replace `"your_openai_api_key_here"` with your actual OpenAI API key.

### 2. Install Dependencies

This project uses `python-dotenv` to load environment variables and other Python libraries. You can install them using pip:

```bash
pip install python-dotenv sounddevice numpy scipy openai pyperclip PyQt5
```
It's recommended to use a virtual environment for dependency management.

## Usage

To start the application, simply run the Python script:

```bash
python tray_sprachtool.py
```

The application will appear in your system tray. Press and hold the spacebar to record, and release to transcribe. The status window will show the current state and the fireflies will change color accordingly.
