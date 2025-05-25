# Bla Repository

## Application Overview

This repository contains the source code for a Python application designed to facilitate quick speech-to-text transcription. The application runs silently in the system tray (currently optimized for Windows) and allows users to record audio by simply holding down the spacebar. Once the spacebar is released, the recorded audio is sent to the OpenAI Whisper API for transcription. The resulting text is then automatically copied to the user's clipboard, making it easy to paste into any document or application.

Key features include:
*   **System Tray Integration:** Operates discreetly from the system tray, providing quick access to its functions.
*   **Spacebar-Activated Recording:** Intuitive recording control by pressing and holding the spacebar.
*   **OpenAI Whisper Transcription:** Leverages the powerful Whisper API for accurate speech-to-text conversion.
*   **Automatic Clipboard Copy:** Transcribed text is immediately available for pasting.
*   **Real-time Status Window:** A small pop-up window provides feedback on the application's status (e.g., recording, processing, copied).
*   **Windows Autostart Option:** Includes functionality to automatically start with Windows.
*   **Audio Feedback:** Provides distinct beeps for recording start and stop events.

## Setup

To run this application, you need to set an environment variable. This variable is crucial for the application's functionality and should be kept confidential as it contains your OpenAI API key.

### Setting the Environment Variable

Please set the `MY_API_KEY` environment variable with your respective API key.

#### Windows

You can set the environment variable temporarily in your command prompt:

```bash
set MY_API_KEY=your_api_key_here
```

To set it permanently, you can use the System Properties dialog or the `setx` command:

```bash
setx MY_API_KEY "your_api_key_here"
```

#### Linux/macOS

You can set the environment variable temporarily in your terminal:

```bash
export MY_API_KEY="your_api_key_here"
```

To set it permanently, add the `export` line to your shell's configuration file (e.g., `~/.bashrc`, `~/.zshrc`, or `~/.profile`):

```bash
echo 'export MY_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

Replace `your_api_key_here` with your actual API key.

## Usage

[Further usage instructions can be added here later.]
