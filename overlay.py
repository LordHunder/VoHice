import sys
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from ai_engine import AIEngine

class OverlayBadge(QWidget):
    update_signal = pyqtSignal(str, str)
    volume_signal = pyqtSignal(float)
    clipboard_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.ai_engine = AIEngine()
        self.translation_mode = False
        
        self.initUI()
        self.update_signal.connect(self._update_status_gui)
        self.volume_signal.connect(self._update_volume_gui)
        self.clipboard_signal.connect(self._copy_to_clipboard)
        
    def initUI(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Main Layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # Panel (glassmorphism vertical effect)
        self.panel = QFrame()
        self.panel.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 240); 
                border-radius: 20px; 
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        self.panel_layout = QVBoxLayout()
        self.panel_layout.setContentsMargins(20, 20, 20, 20)
        self.panel_layout.setSpacing(10)
        self.panel.setLayout(self.panel_layout)
        
        # Load custom font
        font_path = r"C:\Users\Pietro\OneDrive\Desktop\Glaido clone\Fonts\drunk_fonts\DRUNKFONTS-Regular.otf"
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.custom_font = QFont(font_family, 22)
        else:
            self.custom_font = QFont("Arial", 22, QFont.Weight.Bold)

        # 1. Title
        self.header = QLabel("VoHice")
        self.header.setFont(self.custom_font)
        self.header.setStyleSheet("color: white; border: none; background: transparent;")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.panel_layout.addWidget(self.header)
        
        # 2. Volume Bar
        self.volume_bar = QProgressBar()
        self.volume_bar.setTextVisible(False)
        self.volume_bar.setFixedHeight(4)
        self.volume_bar.setRange(0, 100)
        self.volume_bar.setValue(0)
        self.volume_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 2px;
            }
        """)
        self.panel_layout.addWidget(self.volume_bar)
        
        # 3. Status messages (normal font)
        self.status_label = QLabel("Pronto")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet("color: #aaaaaa; border: none; background: transparent; font-weight: 500;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.panel_layout.addWidget(self.status_label)
        
        # 4. Buttons Layout
        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(15)
        self.btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Shared glass button base styles imitating the React snippet
        self.btn_style_off = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 25px;
                color: #888888;
                font-family: 'Segoe MDL2 Assets';
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
            }
        """
        
        self.btn_style_on = """
            QPushButton {
                background-color: rgba(46, 204, 113, 0.15);
                border: 1px solid rgba(46, 204, 113, 0.5);
                border-radius: 25px;
                color: #2ecc71;
                font-family: 'Segoe MDL2 Assets';
                font-size: 22px;
            }
        """

        # Translation Toggle (Globe Icon: \uE12B in MDL2)
        self.toggle_btn = QPushButton("\uE12B")
        self.toggle_btn.setFixedSize(50, 50)
        self.toggle_btn.setStyleSheet(self.btn_style_off)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_translation)
        self.btn_layout.addWidget(self.toggle_btn)

        # Dictation Toggle (Microphone Icon: \uE1D6 in MDL2)
        self.rec_btn = QPushButton("\uE1D6")
        self.rec_btn.setFixedSize(50, 50)
        self.rec_btn.setStyleSheet(self.btn_style_off)
        self.rec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rec_btn.clicked.connect(self.toggle_recording)
        self.btn_layout.addWidget(self.rec_btn)

        self.panel_layout.addLayout(self.btn_layout)
        self.layout.addWidget(self.panel)
        self.old_pos = None

    def toggle_translation(self):
        self.translation_mode = not self.translation_mode
        self.ai_engine.translate_to_english = self.translation_mode
        
        if self.translation_mode:
            self.toggle_btn.setStyleSheet(self.btn_style_on)
        else:
            self.toggle_btn.setStyleSheet(self.btn_style_off)

    def toggle_recording(self):
        is_now_listening = self.ai_engine.toggle_listening(
            self.translation_mode, 
            self.update_status_threadsafe,
            self.update_volume_threadsafe,
            self.clipboard_signal.emit
        )
        
        if is_now_listening:
            self.rec_btn.setStyleSheet(self.btn_style_on)
        else:
            self.rec_btn.setStyleSheet(self.btn_style_off)

    def update_status_threadsafe(self, color, label_text):
        self.update_signal.emit(color, label_text)

    def update_volume_threadsafe(self, volume):
        self.volume_signal.emit(volume)

    def _copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)

    def _update_status_gui(self, color, label_text):
        # Update normal font text below volume bar
        self.status_label.setText(label_text)

    def _update_volume_gui(self, volume):
        # Update progress bar
        val_ui = int(min(volume * 800, 100))
        self.volume_bar.setValue(val_ui)
        
        # Pulse animation on the microphone button
        if hasattr(self, 'ai_engine') and self.ai_engine.is_listening:
            size = 22 + (val_ui / 100) * 8
            pulse_style = self.btn_style_on.replace("font-size: 22px;", f"font-size: {int(size)}px;")
            self.rec_btn.setStyleSheet(pulse_style)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = OverlayBadge()
    overlay.show()
    screen = app.primaryScreen().geometry()
    overlay.move(screen.width() - overlay.width() - 50, 50)
    sys.exit(app.exec())
