# Audio Visualizer

A lightweight audio visualizer for Windows taskbar, similar to CAVA.

![Preview](preview.png)

## Features

- Real-time audio spectrum visualization
- System tray integration
- Draggable widget
- Customizable settings (bars, sensitivity, colors, etc.)
- Auto-start with Windows
- Portable single EXE file

## Download

Download the latest release from [Releases](https://github.com/yourusername/audio-visualizer/releases).

## Requirements (for running from source)

- Windows 10/11
- Python 3.8+
- Enable "Stereo Mix" in Sound settings OR install [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)

### Enable Stereo Mix

1. Right-click speaker icon → Sound settings
2. Sound Control Panel → Recording tab
3. Right-click → Show Disabled Devices
4. Enable "Stereo Mix"

## Installation

### Portable (Recommended)

1. Download `AudioVisualizer.exe` from Releases
2. Run it - that's it!

### From Source

```bash
git clone https://github.com/yourusername/audio-visualizer.git
cd audio-visualizer
pip install -r requirements.txt
python visualizer.py
```

## Build EXE

```bash
pip install pyinstaller
pyinstaller visualizer.spec
# Output: dist/AudioVisualizer.exe
```

Or run `build.bat` on Windows.

## Usage

- **Double-click tray icon**: Show/Hide visualizer
- **Right-click tray icon**: Menu (Settings, About, Quit)
- **Drag visualizer**: Move to desired position

## Settings

| Option | Description |
|--------|-------------|
| Audio Device | Select input device (Stereo Mix, VB-Cable, etc.) |
| Bars | Number of frequency bars (8-64) |
| Sensitivity | Audio sensitivity (10-500) |
| Smoothing | Animation smoothing (0-95%) |
| Bar Width | Width of each bar |
| Height | Visualizer height |
| Start with Windows | Auto-start on login |
| Start minimized | Start hidden in tray |

## Config

Settings are saved in `config.json` next to the executable.

## License

MIT License

## Credits

Inspired by [CAVA](https://github.com/karlstav/cava)
