import sys
import json
import numpy as np
import sounddevice as sd
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QWidget, QSystemTrayIcon, QMenu, 
                             QAction, QDialog, QVBoxLayout, QLabel, QSlider, 
                             QComboBox, QPushButton, QCheckBox, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QIcon, QPixmap

APP_NAME = "AudioVisualizer"
APP_VERSION = "1.0.0"

def get_config_path():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / "config.json"
    return Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "bars": 16,
    "sensitivity": 150,
    "smoothing": 0.7,
    "gradient": ["#59cc33", "#cccc33", "#cc3333"],
    "bar_width": 3,
    "bar_spacing": 1,
    "height": 30,
    "device_index": None,
    "start_minimized": False
}

def load_config():
    path = get_config_path()
    if path.exists():
        try:
            with open(path) as f:
                cfg = DEFAULT_CONFIG.copy()
                cfg.update(json.load(f))
                return cfg
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(get_config_path(), "w") as f:
        json.dump(config, f, indent=2)

def set_autostart(enable):
    if sys.platform == "win32":
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                            r"Software\Microsoft\Windows\CurrentVersion\Run", 
                            0, winreg.KEY_SET_VALUE)
        if enable:
            path = f'"{sys.executable}" "{__file__}"' if not getattr(sys, 'frozen', False) else sys.executable
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, path)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except:
                pass
        winreg.CloseKey(key)

def is_autostart_enabled():
    if sys.platform == "win32":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Run",
                                0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except:
            return False
    return False

def create_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    colors = ["#59cc33", "#80cc33", "#a6cc33", "#cccc33", "#cc8033", "#cc3333"]
    heights = [0.4, 0.8, 0.6, 1.0, 0.5, 0.7]
    bar_w = 8
    spacing = 2
    for i, (c, h) in enumerate(zip(colors, heights)):
        x = i * (bar_w + spacing) + 4
        bar_h = int(h * 50)
        grad = QLinearGradient(0, 64, 0, 64 - bar_h)
        grad.setColorAt(0, QColor(c))
        grad.setColorAt(1, QColor(c).lighter(150))
        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(x, 64 - bar_h - 4, bar_w, bar_h, 2, 2)
    painter.end()
    return QIcon(pixmap)

class AudioCapture(QThread):
    data_ready = pyqtSignal(np.ndarray)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True
        
    def run(self):
        chunk = 1024
        device = self.config.get("device_index")
        
        def callback(indata, frames, time, status):
            if self.running:
                data = indata[:, 0]
                fft = np.abs(np.fft.rfft(data))[:self.config["bars"]]
                fft = fft / (chunk / 2) * self.config["sensitivity"]
                self.data_ready.emit(fft)
        
        try:
            with sd.InputStream(device=device, channels=1, callback=callback,
                              blocksize=chunk, samplerate=44100):
                while self.running:
                    sd.sleep(100)
        except Exception as e:
            print(f"Audio error: {e}")
    
    def stop(self):
        self.running = False
        self.wait()

class VisualizerWidget(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.bars_data = np.zeros(config["bars"])
        self.smoothed = np.zeros(config["bars"])
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.dragging = False
        self.offset = None
        self.update_geometry()
        
    def update_geometry(self):
        screen = QApplication.primaryScreen().geometry()
        w = self.config["bars"] * (self.config["bar_width"] + self.config["bar_spacing"])
        self.setFixedSize(w, self.config["height"])
        self.move(screen.width() - w - 120, screen.height() - 40)
        self.smoothed = np.zeros(self.config["bars"])
        self.bars_data = np.zeros(self.config["bars"])
        
    def update_bars(self, data):
        s = self.config["smoothing"]
        if len(data) != len(self.smoothed):
            self.smoothed = np.zeros(len(data))
        self.smoothed = self.smoothed * s + data * (1 - s)
        self.bars_data = np.clip(self.smoothed, 0, 1)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        colors = self.config["gradient"]
        bw, bs, h = self.config["bar_width"], self.config["bar_spacing"], self.config["height"]
        
        for i, val in enumerate(self.bars_data):
            bar_h = max(int(val * h), 2)
            x = i * (bw + bs)
            grad = QLinearGradient(0, h, 0, h - bar_h)
            grad.setColorAt(0, QColor(colors[0]))
            if len(colors) > 1:
                grad.setColorAt(0.5, QColor(colors[len(colors)//2]))
            grad.setColorAt(1, QColor(colors[-1]))
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, h - bar_h, bw, bar_h, 1, 1)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToGlobal(event.pos() - self.offset))
    
    def mouseReleaseEvent(self, event):
        self.dragging = False

class SettingsDialog(QDialog):
    def __init__(self, config, audio_devices, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(f"{APP_NAME} Settings")
        self.setWindowIcon(create_icon())
        self.setMinimumWidth(350)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Audio Device:"))
        self.device_combo = QComboBox()
        for idx, name in audio_devices:
            self.device_combo.addItem(name, idx)
            if idx == config.get("device_index"):
                self.device_combo.setCurrentIndex(self.device_combo.count() - 1)
        layout.addWidget(self.device_combo)
        
        self.sliders = {}
        for label, key, min_v, max_v, scale in [
            ("Bars", "bars", 8, 64, 1),
            ("Sensitivity", "sensitivity", 10, 500, 1),
            ("Smoothing (%)", "smoothing", 0, 95, 100),
            ("Bar Width", "bar_width", 1, 10, 1),
            ("Height", "height", 20, 100, 1),
        ]:
            val = int(config[key] * scale)
            lbl = QLabel(f"{label}: {val}")
            layout.addWidget(lbl)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_v, max_v)
            slider.setValue(val)
            slider.valueChanged.connect(lambda v, l=lbl, n=label: l.setText(f"{n}: {v}"))
            self.sliders[key] = (slider, scale)
            layout.addWidget(slider)
        
        self.autostart_cb = QCheckBox("Start with Windows")
        self.autostart_cb.setChecked(is_autostart_enabled())
        layout.addWidget(self.autostart_cb)
        
        self.minimized_cb = QCheckBox("Start minimized")
        self.minimized_cb.setChecked(config.get("start_minimized", False))
        layout.addWidget(self.minimized_cb)
        
        btn = QPushButton("Save")
        btn.clicked.connect(self.save)
        layout.addWidget(btn)
        
    def save(self):
        for key, (slider, scale) in self.sliders.items():
            self.config[key] = slider.value() / scale
        self.config["device_index"] = self.device_combo.currentData()
        self.config["start_minimized"] = self.minimized_cb.isChecked()
        set_autostart(self.autostart_cb.isChecked())
        save_config(self.config)
        self.accept()

def get_audio_devices():
    devices = []
    for i, d in enumerate(sd.query_devices()):
        if d['max_input_channels'] > 0:
            devices.append((i, d['name']))
    return devices

class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName(APP_NAME)
        
        self.config = load_config()
        self.widget = VisualizerWidget(self.config)
        self.audio = None
        self.setup_tray()
        self.start_audio()
        
        if not self.config.get("start_minimized"):
            self.widget.show()
    
    def setup_tray(self):
        self.tray = QSystemTrayIcon(create_icon(), self.app)
        self.tray.setToolTip(f"{APP_NAME} v{APP_VERSION}")
        
        menu = QMenu()
        
        show_action = QAction("Show/Hide")
        show_action.triggered.connect(self.toggle_widget)
        menu.addAction(show_action)
        
        settings_action = QAction("Settings")
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        about_action = QAction("About")
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        
        quit_action = QAction("Quit")
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)
        
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda r: self.toggle_widget() if r == QSystemTrayIcon.DoubleClick else None)
        self.tray.show()
    
    def toggle_widget(self):
        self.widget.setVisible(not self.widget.isVisible())
    
    def start_audio(self):
        if self.audio:
            self.audio.stop()
        self.audio = AudioCapture(self.config)
        self.audio.data_ready.connect(self.widget.update_bars)
        self.audio.start()
    
    def open_settings(self):
        dlg = SettingsDialog(self.config, get_audio_devices())
        if dlg.exec_():
            self.widget.config = self.config
            self.widget.update_geometry()
            self.start_audio()
    
    def show_about(self):
        QMessageBox.about(None, f"About {APP_NAME}",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "Audio visualizer for Windows taskbar.\n\n"
            "github.com/yourusername/audio-visualizer")
    
    def quit(self):
        if self.audio:
            self.audio.stop()
        self.app.quit()
    
    def run(self):
        return self.app.exec_()

if __name__ == "__main__":
    app = App()
    sys.exit(app.run())
