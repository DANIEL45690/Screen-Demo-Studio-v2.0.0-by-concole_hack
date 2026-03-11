#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Screen Demo Studio - Профессиональный софт для демонстрации экрана
Разработано @concole_hack
Версия 2.0.0
"""

import sys
import os
import time
import json
import threading
import queue
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from PIL import ImageGrab, Image
import numpy as np

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *

# Константы приложения
APP_NAME = "Screen Demo Studio"
APP_VERSION = "2.0.0"
APP_AUTHOR = "@concole_hack"
SETTINGS_FILE = "screen_demo_settings.json"
OUTPUT_DIR = "screen_records"

# Цветовая схема - Современная темная тема
COLORS = {
    'bg_dark': '#1a1e24',
    'bg_medium': '#252a33',
    'bg_light': '#2f3540',
    'accent': '#7c3aed',
    'accent_hover': '#8b5cf6',
    'accent_pressed': '#6d28d9',
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'text_primary': '#f3f4f6',
    'text_secondary': '#9ca3af',
    'border': '#374151'
}

# Стили CSS для современного интерфейса
STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}

QWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Arial', sans-serif;
}}

QMenuBar {{
    background-color: {COLORS['bg_medium']};
    padding: 4px;
    border-bottom: 1px solid {COLORS['border']};
}}

QMenuBar::item {{
    padding: 6px 12px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['accent']};
}}

QMenu {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['accent']};
}}

QPushButton {{
    background-color: {COLORS['accent']};
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 13px;
}}

QPushButton:hover {{
    background-color: {COLORS['accent_hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['accent_pressed']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_secondary']};
}}

QToolButton {{
    background-color: transparent;
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px;
}}

QToolButton:hover {{
    background-color: {COLORS['bg_light']};
}}

QLineEdit, QTextEdit, QSpinBox, QComboBox {{
    background-color: {COLORS['bg_light']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
    color: {COLORS['text_primary']};
}}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {COLORS['accent']};
}}

QListWidget, QTreeWidget, QTableWidget {{
    background-color: {COLORS['bg_light']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    outline: none;
}}

QListWidget::item, QTreeWidget::item, QTableWidget::item {{
    padding: 8px;
    border-radius: 4px;
}}

QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {{
    background-color: {COLORS['accent']};
}}

QScrollBar:vertical {{
    background-color: {COLORS['bg_dark']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['bg_light']};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['accent']};
}}

QSlider::groove:horizontal {{
    height: 6px;
    background: {COLORS['bg_light']};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: {COLORS['accent']};
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}}

QSlider::handle:horizontal:hover {{
    background: {COLORS['accent_hover']};
    width: 20px;
    height: 20px;
    margin: -7px 0;
    border-radius: 10px;
}}

QProgressBar {{
    border: none;
    border-radius: 4px;
    background-color: {COLORS['bg_light']};
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 4px;
}}

QLabel {{
    color: {COLORS['text_primary']};
}}

QGroupBox {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 10px;
    color: {COLORS['text_secondary']};
}}

QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['bg_dark']};
}}

QTabBar::tab {{
    background-color: {COLORS['bg_medium']};
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['accent']};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['bg_light']};
}}
"""

class RecordingThread(QThread):
    """Поток для записи экрана"""
    frame_captured = pyqtSignal(np.ndarray)
    recording_stopped = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.is_paused = False
        self.frames = []
        self.start_time = None
        self.pause_start_time = None
        self.total_paused_time = 0
        self.output_path = None
        self.fps = 30
        self.quality = 85
        self.include_mouse = True
        self.capture_area = None  # None = весь экран
        
    def start_recording(self, output_path, fps=30, quality=85, 
                       include_mouse=True, capture_area=None):
        """Начать запись"""
        self.is_recording = True
        self.is_paused = False
        self.frames = []
        self.output_path = output_path
        self.fps = fps
        self.quality = quality
        self.include_mouse = include_mouse
        self.capture_area = capture_area
        self.start_time = time.time()
        self.total_paused_time = 0
        self.start()
        
    def pause_recording(self):
        """Пауза записи"""
        if self.is_recording and not self.is_paused:
            self.is_paused = True
            self.pause_start_time = time.time()
            
    def resume_recording(self):
        """Продолжить запись"""
        if self.is_recording and self.is_paused:
            self.is_paused = False
            if self.pause_start_time:
                self.total_paused_time += time.time() - self.pause_start_time
                self.pause_start_time = None
                
    def stop_recording(self):
        """Остановить запись"""
        self.is_recording = False
        self.is_paused = False
        
    def run(self):
        """Основной цикл записи"""
        try:
            frame_interval = 1.0 / self.fps
            last_capture_time = 0
            
            while self.is_recording:
                current_time = time.time()
                
                if not self.is_paused and (current_time - last_capture_time) >= frame_interval:
                    try:
                        # Захват экрана
                        if self.capture_area:
                            bbox = self.capture_area
                        else:
                            bbox = None  # весь экран
                            
                        screenshot = ImageGrab.grab(bbox=bbox, 
                                                   include_layered_windows=True,
                                                   all_screens=True)
                        
                        # Конвертация в numpy array
                        frame = np.array(screenshot)
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        
                        self.frames.append(frame)
                        self.frame_captured.emit(frame)
                        last_capture_time = current_time
                        
                    except Exception as e:
                        self.error_occurred.emit(f"Ошибка захвата кадра: {str(e)}")
                        
                QThread.msleep(1)  # Небольшая задержка для снижения нагрузки на CPU
                
            # Сохранение видео после остановки
            if self.frames:
                self.save_video()
                
        except Exception as e:
            self.error_occurred.emit(f"Критическая ошибка записи: {str(e)}")
            
    def save_video(self):
        """Сохранить записанные кадры в видеофайл"""
        try:
            if not self.frames:
                return
                
            height, width = self.frames[0].shape[:2]
            
            # Кодек для MP4
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(self.output_path, fourcc, self.fps, (width, height))
            
            for frame in self.frames:
                out.write(frame)
                
            out.release()
            
            # Оптимизация размера файла
            self.optimize_video(self.output_path)
            
            duration = time.time() - self.start_time - self.total_paused_time
            self.recording_stopped.emit(f"Видео сохранено: {self.output_path}\n"
                                       f"Длительность: {self.format_time(duration)}\n"
                                       f"Кадров: {len(self.frames)}\n"
                                       f"Размер: {self.get_file_size(self.output_path)}")
            
        except Exception as e:
            self.error_occurred.emit(f"Ошибка сохранения видео: {str(e)}")
            
    def optimize_video(self, video_path):
        """Оптимизация размера видеофайла"""
        try:
            import subprocess
            temp_path = video_path + ".temp.mp4"
            
            # FFmpeg оптимизация
            cmd = [
                'ffmpeg', '-i', video_path,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', str(int(51 - (self.quality * 0.51))),  # Конвертация quality в CRF
                '-movflags', '+faststart',
                '-y', temp_path
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            os.replace(temp_path, video_path)
            
        except Exception as e:
            print(f"Оптимизация видео не удалась: {e}")
            
    @staticmethod
    def format_time(seconds):
        """Форматирование времени"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
            
    @staticmethod
    def get_file_size(file_path):
        """Получить размер файла в человекочитаемом формате"""
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

class ScreenCaptureWidget(QWidget):
    """Виджет для предпросмотра захвата экрана"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 240)
        self.current_frame = None
        self.is_recording = False
        self.recording_indicator = False
        self.indicator_timer = QTimer()
        self.indicator_timer.timeout.connect(self.toggle_indicator)
        self.indicator_timer.start(500)
        
    def set_frame(self, frame):
        """Установить текущий кадр для отображения"""
        self.current_frame = frame
        self.update()
        
    def set_recording(self, recording):
        """Установить состояние записи"""
        self.is_recording = recording
        self.update()
        
    def toggle_indicator(self):
        """Переключение индикатора записи"""
        if self.is_recording:
            self.recording_indicator = not self.recording_indicator
            self.update()
        
    def paintEvent(self, event):
        """Отрисовка виджета"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Заливка фона
        painter.fillRect(self.rect(), QColor(COLORS['bg_medium']))
        
        if self.current_frame is not None:
            # Конвертация numpy array в QImage
            height, width, channel = self.current_frame.shape
            bytes_per_line = 3 * width
            qimage = QImage(self.current_frame.data, width, height, 
                          bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            
            # Масштабирование с сохранением пропорций
            scaled_pixmap = QPixmap.fromImage(qimage).scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            # Центрирование
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            # Текст "Нет видео"
            painter.setPen(QColor(COLORS['text_secondary']))
            painter.setFont(QFont('Segoe UI', 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "Предпросмотр недоступен")
            
        # Индикатор записи
        if self.is_recording and self.recording_indicator:
            painter.setBrush(QColor(COLORS['error']))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(20, 20, 12, 12)
            
            painter.setPen(QColor(COLORS['text_primary']))
            painter.setFont(QFont('Segoe UI', 10, QFont.Bold))
            painter.drawText(40, 30, "REC")
            
        # Рамка области захвата
        if hasattr(self.parent(), 'selection_widget') and self.parent().selection_widget:
            painter.setPen(QPen(QColor(COLORS['accent']), 2, Qt.DashLine))
            painter.drawRect(self.parent().selection_widget.geometry())

class RecordingManager:
    """Менеджер записей для управления файлами"""
    def __init__(self):
        self.recordings_dir = Path(OUTPUT_DIR)
        self.recordings_dir.mkdir(exist_ok=True)
        self.recordings = []
        self.load_recordings()
        
    def get_new_filename(self, prefix="screen_recording"):
        """Сгенерировать новое имя файла"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(self.recordings_dir / f"{prefix}_{timestamp}.mp4")
        
    def add_recording(self, filepath):
        """Добавить запись в список"""
        if os.path.exists(filepath):
            recording = {
                'path': filepath,
                'name': os.path.basename(filepath),
                'size': os.path.getsize(filepath),
                'created': datetime.fromtimestamp(os.path.getctime(filepath)),
                'modified': datetime.fromtimestamp(os.path.getmtime(filepath))
            }
            self.recordings.append(recording)
            self.save_recordings()
            return recording
        return None
        
    def load_recordings(self):
        """Загрузить список записей"""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                    self.recordings = data.get('recordings', [])
        except Exception as e:
            print(f"Ошибка загрузки записей: {e}")
            
    def save_recordings(self):
        """Сохранить список записей"""
        try:
            data = {
                'recordings': self.recordings,
                'last_updated': datetime.now().isoformat()
            }
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Ошибка сохранения записей: {e}")
            
    def delete_recording(self, index):
        """Удалить запись"""
        if 0 <= index < len(self.recordings):
            recording = self.recordings[index]
            try:
                if os.path.exists(recording['path']):
                    os.remove(recording['path'])
                del self.recordings[index]
                self.save_recordings()
                return True
            except Exception as e:
                print(f"Ошибка удаления записи: {e}")
        return False

class AreaSelector(QWidget):
    """Виджет для выбора области экрана"""
    area_selected = pyqtSignal(tuple)
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 100);")
        self.setMouseTracking(True)
        
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        
        # Затемнение всего экрана
        desktop = QApplication.desktop()
        self.setGeometry(desktop.screenGeometry(desktop.primaryScreen()))
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.is_selecting = True
            self.update()
            
    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_pos = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            if self.start_pos and self.end_pos:
                x1 = min(self.start_pos.x(), self.end_pos.x())
                y1 = min(self.start_pos.y(), self.end_pos.y())
                x2 = max(self.start_pos.x(), self.end_pos.x())
                y2 = max(self.start_pos.y(), self.end_pos.y())
                
                # Проверка минимального размера
                if (x2 - x1) > 50 and (y2 - y1) > 50:
                    self.area_selected.emit((x1, y1, x2, y2))
                    
            self.close()
            
    def paintEvent(self, event):
        if self.is_selecting and self.start_pos and self.end_pos:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(COLORS['accent']), 2, Qt.SolidLine))
            painter.setBrush(QColor(COLORS['accent'], 50))
            
            x = min(self.start_pos.x(), self.end_pos.x())
            y = min(self.start_pos.y(), self.end_pos.y())
            w = abs(self.start_pos.x() - self.end_pos.x())
            h = abs(self.start_pos.y() - self.end_pos.y())
            
            painter.drawRect(x, y, w, h)
            
            # Информация о размере
            painter.setPen(QColor(COLORS['text_primary']))
            painter.setFont(QFont('Segoe UI', 10, QFont.Bold))
            painter.drawText(x + 5, y - 10, f"{w}x{h}")

class ScreenDemoStudio(QMainWindow):
    """Главное окно приложения"""
    def __init__(self):
        super().__init__()
        self.recording_thread = None
        self.recording_manager = RecordingManager()
        self.current_recording_path = None
        self.settings = self.load_settings()
        self.selection_widget = None
        self.capture_area = None
        self.init_ui()
        self.setup_shortcuts()
        self.check_requirements()
        
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION} - by {APP_AUTHOR}")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # ========== Левая панель ==========
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(20)
        
        # Виджет предпросмотра
        preview_group = QGroupBox("Предпросмотр")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_widget = ScreenCaptureWidget(self)
        preview_layout.addWidget(self.preview_widget)
        
        # Информационная панель предпросмотра
        preview_info = QWidget()
        preview_info_layout = QHBoxLayout(preview_info)
        preview_info_layout.setContentsMargins(0, 10, 0, 0)
        
        self.recording_time_label = QLabel("00:00")
        self.recording_time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px; font-weight: bold;")
        preview_info_layout.addWidget(self.recording_time_label)
        
        self.frame_counter_label = QLabel("0 кадров")
        self.frame_counter_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        preview_info_layout.addWidget(self.frame_counter_label)
        
        preview_info_layout.addStretch()
        
        self.recording_status_label = QLabel("Готов к записи")
        self.recording_status_label.setStyleSheet(f"color: {COLORS['success']};")
        preview_info_layout.addWidget(self.recording_status_label)
        
        preview_layout.addWidget(preview_info)
        left_layout.addWidget(preview_group, 2)
        
        # Панель управления записью
        controls_group = QGroupBox("Управление записью")
        controls_layout = QVBoxLayout(controls_group)
        
        # Кнопки управления
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setSpacing(15)
        
        self.record_btn = QPushButton("● Начать запись")
        self.record_btn.setMinimumHeight(50)
        self.record_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['error']};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #dc2626;
            }}
        """)
        self.record_btn.clicked.connect(self.toggle_recording)
        buttons_layout.addWidget(self.record_btn)
        
        self.pause_btn = QPushButton("⏸ Пауза")
        self.pause_btn.setMinimumHeight(50)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause)
        buttons_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("■ Стоп")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_light']};
            }}
        """)
        self.stop_btn.clicked.connect(self.stop_recording)
        buttons_layout.addWidget(self.stop_btn)
        
        controls_layout.addWidget(buttons_widget)
        
        # Настройки записи
        settings_widget = QWidget()
        settings_layout = QGridLayout(settings_widget)
        settings_layout.setVerticalSpacing(15)
        settings_layout.setHorizontalSpacing(20)
        
        # FPS
        settings_layout.addWidget(QLabel("FPS:"), 0, 0)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(self.settings.get('fps', 30))
        self.fps_spin.setSuffix(" кадров/с")
        settings_layout.addWidget(self.fps_spin, 0, 1)
        
        # Качество
        settings_layout.addWidget(QLabel("Качество:"), 0, 2)
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(self.settings.get('quality', 85))
        self.quality_spin.setSuffix("%")
        settings_layout.addWidget(self.quality_spin, 0, 3)
        
        # Область захвата
        settings_layout.addWidget(QLabel("Область:"), 1, 0)
        self.area_combo = QComboBox()
        self.area_combo.addItems(["Весь экран", "Выбрать область"])
        self.area_combo.currentTextChanged.connect(self.on_area_changed)
        settings_layout.addWidget(self.area_combo, 1, 1, 1, 2)
        
        # Дополнительные опции
        self.mouse_check = QCheckBox("Записывать курсор")
        self.mouse_check.setChecked(self.settings.get('include_mouse', True))
        settings_layout.addWidget(self.mouse_check, 2, 0, 1, 2)
        
        self.audio_check = QCheckBox("Запись звука")
        self.audio_check.setChecked(self.settings.get('include_audio', False))
        self.audio_check.setEnabled(False)  # Временно отключено
        settings_layout.addWidget(self.audio_check, 2, 2, 1, 2)
        
        controls_layout.addWidget(settings_widget)
        left_layout.addWidget(controls_group)
        
        main_layout.addWidget(left_panel, 3)
        
        # ========== Правая панель ==========
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(20)
        
        # Таб-виджет для записей и статистики
        tabs = QTabWidget()
        
        # Вкладка "Записи"
        recordings_tab = QWidget()
        recordings_layout = QVBoxLayout(recordings_tab)
        
        # Поиск и фильтры
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск записей...")
        self.search_input.textChanged.connect(self.filter_recordings)
        search_layout.addWidget(self.search_input)
        
        self.refresh_btn = QToolButton()
        self.refresh_btn.setText("↻")
        self.refresh_btn.setToolTip("Обновить список")
        self.refresh_btn.clicked.connect(self.load_recordings_list)
        search_layout.addWidget(self.refresh_btn)
        
        recordings_layout.addWidget(search_widget)
        
        # Список записей
        self.recordings_list = QListWidget()
        self.recordings_list.setIconSize(QSize(120, 68))
        self.recordings_list.itemDoubleClicked.connect(self.play_recording)
        self.recordings_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.recordings_list.customContextMenuRequested.connect(self.show_recording_context_menu)
        recordings_layout.addWidget(self.recordings_list)
        
        # Информация о записи
        self.recording_info_label = QLabel("Выберите запись для просмотра информации")
        self.recording_info_label.setWordWrap(True)
        self.recording_info_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_light']};
                padding: 15px;
                border-radius: 8px;
                color: {COLORS['text_secondary']};
            }}
        """)
        recordings_layout.addWidget(self.recording_info_label)
        
        tabs.addTab(recordings_tab, "📁 Записи")
        
        # Вкладка "Статистика"
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        # Статистика
        self.stats_widget = QWidget()
        stats_form = QFormLayout(self.stats_widget)
        stats_form.setSpacing(15)
        
        self.total_recordings_label = QLabel("0")
        self.total_recordings_label.setStyleSheet(f"color: {COLORS['accent']}; font-size: 24px; font-weight: bold;")
        stats_form.addRow("Всего записей:", self.total_recordings_label)
        
        self.total_size_label = QLabel("0 MB")
        self.total_size_label.setStyleSheet(f"color: {COLORS['accent']}; font-size: 24px; font-weight: bold;")
        stats_form.addRow("Общий размер:", self.total_size_label)
        
        self.total_duration_label = QLabel("0 мин")
        self.total_duration_label.setStyleSheet(f"color: {COLORS['accent']}; font-size: 24px; font-weight: bold;")
        stats_form.addRow("Общая длительность:", self.total_duration_label)
        
        self.last_recording_label = QLabel("Нет записей")
        stats_form.addRow("Последняя запись:", self.last_recording_label)
        
        stats_layout.addWidget(self.stats_widget)
        stats_layout.addStretch()
        
        tabs.addTab(stats_tab, "📊 Статистика")
        
        # Вкладка "Настройки"
        settings_tab = QWidget()
        settings_layout_main = QVBoxLayout(settings_tab)
        
        # Общие настройки
        general_group = QGroupBox("Общие настройки")
        general_layout = QFormLayout(general_group)
        
        self.save_path_edit = QLineEdit(str(self.recording_manager.recordings_dir))
        self.save_path_edit.setReadOnly(True)
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self.browse_save_path)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.save_path_edit)
        path_layout.addWidget(browse_btn)
        general_layout.addRow("Папка сохранения:", path_layout)
        
        self.auto_open_check = QCheckBox("Автоматически открывать папку после записи")
        self.auto_open_check.setChecked(self.settings.get('auto_open_folder', False))
        general_layout.addRow("", self.auto_open_check)
        
        settings_layout_main.addWidget(general_group)
        
        # Горячие клавиши
        shortcuts_group = QGroupBox("Горячие клавиши")
        shortcuts_layout = QFormLayout(shortcuts_group)
        
        self.start_shortcut_edit = QLineEdit("Ctrl+R")
        self.start_shortcut_edit.setReadOnly(True)
        shortcuts_layout.addRow("Начать запись:", self.start_shortcut_edit)
        
        self.pause_shortcut_edit = QLineEdit("Ctrl+P")
        self.pause_shortcut_edit.setReadOnly(True)
        shortcuts_layout.addRow("Пауза/Продолжить:", self.pause_shortcut_edit)
        
        self.stop_shortcut_edit = QLineEdit("Ctrl+S")
        self.stop_shortcut_edit.setReadOnly(True)
        shortcuts_layout.addRow("Остановить запись:", self.stop_shortcut_edit)
        
        settings_layout_main.addWidget(shortcuts_group)
        settings_layout_main.addStretch()
        
        tabs.addTab(settings_tab, "⚙ Настройки")
        
        right_layout.addWidget(tabs)
        
        main_layout.addWidget(right_panel, 2)
        
        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Прогресс бар в статус баре
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Метка версии
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.status_bar.addPermanentWidget(version_label)
        
        # Применение стилей
        self.setStyleSheet(STYLESHEET)
        
        # Загрузка записей
        self.load_recordings_list()
        self.update_statistics()
        
    def setup_shortcuts(self):
        """Настройка горячих клавиш"""
        self.start_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.start_shortcut.activated.connect(self.toggle_recording)
        
        self.pause_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.pause_shortcut.activated.connect(self.toggle_pause)
        
        self.stop_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.stop_shortcut.activated.connect(self.stop_recording)
        
    def check_requirements(self):
        """Проверка необходимых зависимостей"""
        try:
            import cv2
        except ImportError:
            QMessageBox.warning(self, "Предупреждение", 
                "OpenCV (cv2) не установлен. Некоторые функции могут быть недоступны.\n"
                "Установите: pip install opencv-python")
                
    def load_settings(self):
        """Загрузить настройки"""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
        return {}
        
    def save_settings(self):
        """Сохранить настройки"""
        try:
            settings = {
                'fps': self.fps_spin.value(),
                'quality': self.quality_spin.value(),
                'include_mouse': self.mouse_check.isChecked(),
                'include_audio': self.audio_check.isChecked(),
                'auto_open_folder': self.auto_open_check.isChecked(),
                'last_save_path': str(self.recording_manager.recordings_dir)
            }
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            
    def on_area_changed(self, text):
        """Обработчик изменения области захвата"""
        if text == "Выбрать область":
            self.select_capture_area()
        else:
            self.capture_area = None
            
    def select_capture_area(self):
        """Выбор области захвата"""
        self.selection_widget = AreaSelector()
        self.selection_widget.area_selected.connect(self.on_area_selected)
        self.selection_widget.show()
        
    def on_area_selected(self, area):
        """Обработчик выбора области"""
        self.capture_area = area
        self.area_combo.setCurrentText(f"Область: {area[2]-area[0]}x{area[3]-area[1]}")
        self.status_bar.showMessage(f"Выбрана область: {area}", 3000)
        
    def toggle_recording(self):
        """Переключение записи"""
        if self.record_btn.text() == "● Начать запись":
            self.start_recording()
        else:
            # Кнопка сейчас "Остановить"
            pass
            
    def start_recording(self):
        """Начать запись"""
        try:
            # Генерация имени файла
            self.current_recording_path = self.recording_manager.get_new_filename()
            
            # Создание потока записи
            self.recording_thread = RecordingThread()
            self.recording_thread.frame_captured.connect(self.on_frame_captured)
            self.recording_thread.recording_stopped.connect(self.on_recording_stopped)
            self.recording_thread.error_occurred.connect(self.on_recording_error)
            
            # Настройки записи
            self.recording_thread.start_recording(
                output_path=self.current_recording_path,
                fps=self.fps_spin.value(),
                quality=self.quality_spin.value(),
                include_mouse=self.mouse_check.isChecked(),
                capture_area=self.capture_area
            )
            
            # Обновление UI
            self.record_btn.setText("● Запись...")
            self.record_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.preview_widget.set_recording(True)
            
            self.recording_status_label.setText("🔴 Идет запись")
            self.recording_status_label.setStyleSheet(f"color: {COLORS['error']};")
            
            self.status_bar.showMessage("Запись начата", 3000)
            
            # Таймер для отображения времени записи
            self.recording_timer = QTimer()
            self.recording_timer.timeout.connect(self.update_recording_time)
            self.recording_timer.start(1000)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось начать запись: {str(e)}")
            
    def toggle_pause(self):
        """Пауза/продолжение записи"""
        if self.recording_thread and self.recording_thread.is_recording:
            if self.recording_thread.is_paused:
                self.recording_thread.resume_recording()
                self.pause_btn.setText("⏸ Пауза")
                self.recording_status_label.setText("🔴 Идет запись")
                self.status_bar.showMessage("Запись продолжена", 2000)
            else:
                self.recording_thread.pause_recording()
                self.pause_btn.setText("▶ Продолжить")
                self.recording_status_label.setText("⏸ На паузе")
                self.recording_status_label.setStyleSheet(f"color: {COLORS['warning']};")
                self.status_bar.showMessage("Запись на паузе", 2000)
                
    def stop_recording(self):
        """Остановить запись"""
        if self.recording_thread and self.recording_thread.is_recording:
            reply = QMessageBox.question(self, "Подтверждение", 
                                       "Остановить запись?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.recording_thread.stop_recording()
                
                # Обновление UI
                self.record_btn.setText("● Начать запись")
                self.record_btn.setEnabled(True)
                self.pause_btn.setEnabled(False)
                self.stop_btn.setEnabled(False)
                self.preview_widget.set_recording(False)
                
                self.recording_status_label.setText("⏹ Сохранение...")
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)  # Бесконечная анимация
                
                if hasattr(self, 'recording_timer'):
                    self.recording_timer.stop()
                    
    def on_frame_captured(self, frame):
        """Обработчик захваченного кадра"""
        self.preview_widget.set_frame(frame)
        
        # Обновление счетчика кадров
        if self.recording_thread:
            self.frame_counter_label.setText(f"{len(self.recording_thread.frames)} кадров")
            
    def on_recording_stopped(self, message):
        """Обработчик остановки записи"""
        self.progress_bar.setVisible(False)
        self.recording_status_label.setText("✅ Готов к записи")
        self.recording_status_label.setStyleSheet(f"color: {COLORS['success']};")
        
        # Добавление записи в список
        if self.current_recording_path and os.path.exists(self.current_recording_path):
            self.recording_manager.add_recording(self.current_recording_path)
            self.load_recordings_list()
            self.update_statistics()
            
            # Автоматическое открытие папки
            if self.auto_open_check.isChecked():
                self.open_recordings_folder()
                
        QMessageBox.information(self, "Запись завершена", message)
        self.status_bar.showMessage("Запись сохранена", 3000)
        
    def on_recording_error(self, error_message):
        """Обработчик ошибок записи"""
        self.progress_bar.setVisible(False)
        self.record_btn.setText("● Начать запись")
        self.record_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.preview_widget.set_recording(False)
        
        QMessageBox.critical(self, "Ошибка записи", error_message)
        
    def update_recording_time(self):
        """Обновление времени записи"""
        if self.recording_thread and self.recording_thread.start_time:
            elapsed = time.time() - self.recording_thread.start_time - self.recording_thread.total_paused_time
            self.recording_time_label.setText(RecordingThread.format_time(elapsed))
            
    def load_recordings_list(self):
        """Загрузить список записей в UI"""
        self.recordings_list.clear()
        
        search_text = self.search_input.text().lower()
        
        for recording in self.recording_manager.recordings:
            if search_text and search_text not in recording['name'].lower():
                continue
                
            item = QListWidgetItem()
            
            # Иконка (миниатюра) - заглушка
            pixmap = QPixmap(100, 60)
            pixmap.fill(QColor(COLORS['bg_medium']))
            
            # Текст элемента
            name = recording['name']
            size = self.format_size(recording['size'])
            date = recording['created'].strftime("%d.%m.%Y %H:%M")
            
            item.setText(f"{name}\n{size} • {date}")
            item.setIcon(QIcon(pixmap))
            item.setData(Qt.UserRole, recording)
            
            self.recordings_list.addItem(item)
            
    def filter_recordings(self):
        """Фильтрация записей по поиску"""
        self.load_recordings_list()
        
    def show_recording_context_menu(self, pos):
        """Контекстное меню для записи"""
        item = self.recordings_list.itemAt(pos)
        if not item:
            return
            
        recording = item.data(Qt.UserRole)
        menu = QMenu()
        
        play_action = menu.addAction(QIcon.fromTheme("media-playback-start"), "Воспроизвести")
        menu.addSeparator()
        open_folder_action = menu.addAction("Открыть папку с файлом")
        rename_action = menu.addAction("Переименовать")
        menu.addSeparator()
        delete_action = menu.addAction(QIcon.fromTheme("edit-delete"), "Удалить")
        delete_action.setStyleSheet(f"color: {COLORS['error']};")
        
        action = menu.exec_(self.recordings_list.mapToGlobal(pos))
        
        if action == play_action:
            self.play_recording(item)
        elif action == open_folder_action:
            self.open_file_location(recording['path'])
        elif action == rename_action:
            self.rename_recording(item, recording)
        elif action == delete_action:
            self.delete_recording(item, recording)
            
    def play_recording(self, item):
        """Воспроизвести запись"""
        recording = item.data(Qt.UserRole)
        if os.path.exists(recording['path']):
            try:
                if sys.platform == 'win32':
                    os.startfile(recording['path'])
                elif sys.platform == 'darwin':
                    subprocess.run(['open', recording['path']])
                else:
                    subprocess.run(['xdg-open', recording['path']])
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось открыть файл: {str(e)}")
                
    def open_file_location(self, filepath):
        """Открыть папку с файлом"""
        try:
            if sys.platform == 'win32':
                subprocess.run(['explorer', '/select,', filepath])
            elif sys.platform == 'darwin':
                subprocess.run(['open', '-R', filepath])
            else:
                subprocess.run(['xdg-open', os.path.dirname(filepath)])
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть папку: {str(e)}")
            
    def rename_recording(self, item, recording):
        """Переименовать запись"""
        new_name, ok = QInputDialog.getText(self, "Переименование", 
                                           "Новое имя файла:",
                                           text=recording['name'])
        if ok and new_name and new_name != recording['name']:
            # Добавляем расширение если его нет
            if not new_name.lower().endswith('.mp4'):
                new_name += '.mp4'
                
            old_path = recording['path']
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            
            try:
                os.rename(old_path, new_path)
                recording['path'] = new_path
                recording['name'] = new_name
                self.recording_manager.save_recordings()
                self.load_recordings_list()
                self.status_bar.showMessage(f"Переименовано в {new_name}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось переименовать: {str(e)}")
                
    def delete_recording(self, item, recording):
        """Удалить запись"""
        reply = QMessageBox.question(self, "Подтверждение", 
                                   f"Удалить запись '{recording['name']}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            index = self.recordings_list.row(item)
            if self.recording_manager.delete_recording(index):
                self.load_recordings_list()
                self.update_statistics()
                self.status_bar.showMessage("Запись удалена", 3000)
                
    def update_statistics(self):
        """Обновить статистику"""
        total_size = 0
        total_duration = 0  # В секундах (приблизительно)
        last_recording = None
        
        for recording in self.recording_manager.recordings:
            total_size += recording.get('size', 0)
            
            if last_recording is None or recording['created'] > last_recording['created']:
                last_recording = recording
                
        # Обновление UI
        self.total_recordings_label.setText(str(len(self.recording_manager.recordings)))
        self.total_size_label.setText(self.format_size(total_size))
        
        if last_recording:
            self.last_recording_label.setText(last_recording['created'].strftime("%d.%m.%Y %H:%M"))
        else:
            self.last_recording_label.setText("Нет записей")
            
    def browse_save_path(self):
        """Выбор папки для сохранения"""
        path = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения",
                                               str(self.recording_manager.recordings_dir))
        if path:
            self.recording_manager.recordings_dir = Path(path)
            self.save_path_edit.setText(path)
            self.recording_manager.recordings_dir.mkdir(exist_ok=True)
            self.save_settings()
            
    def open_recordings_folder(self):
        """Открыть папку с записями"""
        try:
            if sys.platform == 'win32':
                os.startfile(str(self.recording_manager.recordings_dir))
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(self.recording_manager.recordings_dir)])
            else:
                subprocess.run(['xdg-open', str(self.recording_manager.recordings_dir)])
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть папку: {str(e)}")
            
    @staticmethod
    def format_size(size):
        """Форматирование размера файла"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
        
    def closeEvent(self, event):
        """Обработчик закрытия приложения"""
        if self.recording_thread and self.recording_thread.is_recording:
            reply = QMessageBox.question(self, "Подтверждение",
                                       "Запись еще идет. Остановить и выйти?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.recording_thread.stop_recording()
                self.recording_thread.wait(2000)
                self.save_settings()
                event.accept()
            else:
                event.ignore()
        else:
            self.save_settings()
            event.accept()

def main():
    """Точка входа в приложение"""
    # Импортируем OpenCV здесь, чтобы избежать проблем при отсутствии
    global cv2
    try:
        import cv2
    except ImportError:
        cv2 = None
        print("Warning: OpenCV not installed. Video saving will not work.")
        
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("concole_hack")
    
    # Установка иконки приложения
    app.setWindowIcon(QIcon.fromTheme("camera-video"))
    
    # Создание и отображение главного окна
    window = ScreenDemoStudio()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
