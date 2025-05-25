# Bla Repository

This repository contains the source code for the Bla application.

## Setup

To run this application, you need to set an environment variable. This variable is crucial for the application's functionality and should be kept confidential if it contains sensitive information (e.g., API keys).

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
