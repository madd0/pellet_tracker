# Contributing to Pellet Tracker

Thank you for your interest in contributing to Pellet Tracker!

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub.

## Development

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes.
4. Submit a pull request.

## Code Style

Please follow the standard Python code style (PEP 8).

## Development Environment

This project is configured to run inside a VS Code Dev Container. It uses a **Python 3.13 (Bookworm)** image and pre-installs necessary system dependencies (ffmpeg, libturbojpeg, etc.) and the latest version of Home Assistant.

### Running and Debugging

We have provided VS Code configurations to make testing easy.

#### VS Code Tasks (`tasks.json`)

- **Setup Home Assistant Config**: This task prepares a local configuration directory (`.homeassistant/`) and symlinks the `custom_components/pellet_tracker` folder into it. This ensures Home Assistant sees your local changes.
- **Run Home Assistant**: This task runs Home Assistant Core using the local configuration directory. It automatically runs the setup task first.

#### Debugging (`launch.json`)

- **Home Assistant**: This launch configuration allows you to run Home Assistant with the Python debugger attached.
    - It automatically runs the "Setup Home Assistant Config" task before starting.
    - You can set breakpoints in your code (`.py` files) and inspect variables while Home Assistant is running.

### How to Start

1. **To Debug (Recommended)**:
   - Go to the "Run and Debug" view in VS Code (Ctrl+Shift+D).
   - Select "Home Assistant" from the dropdown.
   - Press **F5** (or the Play button).

2. **To Run without Debugger**:
   - Open the Command Palette (Ctrl+Shift+P).
   - Type "Tasks: Run Task" and select "Run Home Assistant".

### Accessing Home Assistant

Once Home Assistant is running, you can access the interface:

- **VS Code Desktop**: Open your browser to [http://localhost:8123](http://localhost:8123).
- **GitHub Codespaces (Web)**:
    - Go to the "Ports" tab in VS Code (usually in the bottom panel).
    - Find port `8123`.
    - Click the "Open in Browser" icon (globe).
    - *Note*: The `configuration.yaml` is automatically set up to trust the Codespaces proxy, preventing "400 Bad Request" errors.

### Mock Sensors

The development configuration (`dev_config/configuration.yaml`) includes mock entities to help you test the integration without a real pellet stove.

- **Input Selects**:
    - `input_select.stove_status`: Simulates the status (Off, Heating, etc.).
    - `input_select.stove_power`: Simulates the power level (1-5).
- **Sensors**:
    - `sensor.stove_status`: Mirrors the input select.
    - `sensor.stove_power`: Mirrors the input select.

You can change these values in the Home Assistant Dashboard to trigger state changes in the Pellet Tracker integration.

