import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QGraphicsOpacityEffect

class StatusWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        # Remove native title bar
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground) # Allow for custom shapes/shadows if needed

        self.setGeometry(100, 100, 320, 90)

        # Custom Title Bar
        self.title_bar = QtWidgets.QWidget(self)
        self.title_bar.setFixedHeight(30) # Height of the title bar
        self.title_bar.setStyleSheet("background-color: #1a1a1a; color: white;") # Darker background for title bar

        self.title_label = QtWidgets.QLabel("🎤 Sprachaufnahme", self.title_bar)
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet("color: white; font-weight: bold;")

        title_bar_layout = QtWidgets.QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar_layout.addWidget(self.title_label)

        # Make title bar draggable
        self.old_pos = None
        self.title_bar.mousePressEvent = self.title_bar_mouse_press
        self.title_bar.mouseMoveEvent = self.title_bar_mouse_move
        self.title_bar.mouseReleaseEvent = self.title_bar_mouse_release

        # Main layout for the window
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # Remove margins for the main layout
        main_layout.setSpacing(0) # Remove spacing between widgets

        main_layout.addWidget(self.title_bar) # Add custom title bar at the top

        # Existing content layout
        content_layout = QtWidgets.QVBoxLayout()
        content_layout.setContentsMargins(5, 5, 5, 5) # Add some padding for content

        self.label = QtWidgets.QLabel("Bereit", self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: Consolas, monospace;
                font-size: 10pt;
            }
        """)
        content_layout.addWidget(self.label)

        self.eleven_labs_button = QtWidgets.QPushButton("👂", self)
        self.eleven_labs_button.setFixedSize(35, 35)
        self.eleven_labs_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ff9800; /* Orange border */
                color: white;
                font-size: 16pt;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 152, 0, 0.2);
            }
        """)

        self.record_button = QtWidgets.QPushButton("🎙️", self)
        self.record_button.setFixedSize(35, 35)
        self.record_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ff9800; /* Orange border */
                color: white;
                font-size: 16pt;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 152, 0, 0.2);
            }
        """)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.record_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.eleven_labs_button)
        content_layout.addLayout(button_layout)

        main_layout.addLayout(content_layout) # Add content below title bar

        # Animation properties (existing firefly code)
        self.animation_phase = 0.0
        self.animation_speed = 0.005 # Reduced for slower overall animation
        self.num_fireflies = 50
        self.fireflies = []
        for i in range(self.num_fireflies):
            self.fireflies.append({
                'x': np.random.uniform(0, self.width()),
                'y': np.random.uniform(0, self.height()),
                'size': np.random.uniform(2, 8),
                'color_offset': np.random.uniform(0, 1),
                'phase_offset': np.random.uniform(0, 2 * np.pi),
                'speed_factor': np.random.uniform(0.5, 1.5)
            })

        self.current_firefly_color = QtGui.QColor(255, 165, 0)
        self.target_firefly_color = QtGui.QColor(255, 165, 0)
        self.color_transition_timer = QtCore.QTimer(self)
        self.color_transition_timer.timeout.connect(self.update_firefly_color)
        self.color_transition_speed = 5

        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.timeout.connect(self.animate_background)
        self.animation_timer.start(20) # Reverted interval to 20ms for balanced smoothness and speed

    # Mouse events for dragging the custom title bar
    def title_bar_mouse_press(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.old_pos = event.globalPos()

    def title_bar_mouse_move(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def title_bar_mouse_release(self, event):
        self.old_pos = None

    @QtCore.pyqtSlot(str)
    def set_status(self, text):
        self.label.setText(text)
        # Ensure label is fully visible before starting fade
        if not hasattr(self.label, 'opacity_effect'):
            self.label.opacity_effect = QGraphicsOpacityEffect(self.label)
            self.label.setGraphicsEffect(self.label.opacity_effect)
        self.label.opacity_effect.setOpacity(1.0) # Reset opacity to full

        # Create and start the fade-out animation
        self.fade_animation = QtCore.QPropertyAnimation(self.label.opacity_effect, b"opacity")
        self.fade_animation.setDuration(3000)  # Fade out over 3 seconds
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QtCore.QEasingCurve.OutQuad) # Smooth fade out

        # Connect a slot to reset the label after animation finishes
        self.fade_animation.finished.connect(lambda: self.label.setText(""))

        # Start the animation after 20 seconds
        QtCore.QTimer.singleShot(20000, self.fade_animation.start)

    @QtCore.pyqtSlot()
    def _activate_window(self):
        self.activateWindow()

    @QtCore.pyqtSlot(QtGui.QColor)
    def set_firefly_color(self, color):
        self.target_firefly_color = color
        self.color_transition_timer.start(20)

    def update_firefly_color(self):
        r = self.current_firefly_color.red()
        g = self.current_firefly_color.green()
        b = self.current_firefly_color.blue()

        target_r = self.target_firefly_color.red()
        target_g = self.target_firefly_color.green()
        target_b = self.target_firefly_color.blue()

        r += (target_r - r) / self.color_transition_speed
        g += (target_g - g) / self.color_transition_speed
        b += (target_b - b) / self.color_transition_speed

        self.current_firefly_color = QtGui.QColor(int(r), int(g), int(b))
        self.update()

        if abs(r - target_r) < 1 and abs(g - target_g) < 1 and abs(b - target_b) < 1:
            self.color_transition_timer.stop()
            self.current_firefly_color = self.target_firefly_color

    def animate_background(self):
        self.animation_phase += self.animation_speed
        if self.animation_phase > 2 * np.pi:
            self.animation_phase -= 2 * np.pi

        for firefly in self.fireflies:
            firefly['x'] += np.sin(self.animation_phase * firefly['speed_factor'] * 0.1) * 0.1 # Further reduced movement per frame
            firefly['y'] += np.cos(self.animation_phase * firefly['speed_factor'] * 0.125) * 0.125 # Further reduced movement per frame

            if firefly['x'] < -firefly['size']: firefly['x'] = self.width() + firefly['size']
            if firefly['x'] > self.width() + firefly['size']: firefly['x'] = -firefly['size']
            if firefly['y'] < -firefly['size']: firefly['y'] = self.height() + firefly['size']
            if firefly['y'] > self.height() + firefly['size']: firefly['y'] = -firefly['size']

        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Draw black background with a darker gradient for the main content area
        # This will now draw *below* the title bar
        gradient = QtGui.QRadialGradient(self.width() / 2, self.height() / 2, max(self.width(), self.height()) / 2)
        gradient.setColorAt(0, QtGui.QColor(0, 0, 0))
        gradient.setColorAt(1, QtGui.QColor(10, 10, 10))
        
        # Only paint the area below the title bar
        content_rect = self.rect().adjusted(0, self.title_bar.height(), 0, 0)
        painter.fillRect(content_rect, gradient)

        # Draw fireflies only in the content area
        painter.setClipRect(content_rect) # Clip fireflies to content area
        for firefly in self.fireflies:
            pulse_factor = (np.sin(self.animation_phase * firefly['speed_factor'] + firefly['phase_offset']) + 1) / 2.0

            # Introduce more nuanced orange variations using HSV
            h, s, v, a = self.current_firefly_color.getHsv()

            # Vary saturation and value based on color_offset
            # color_offset is between 0 and 1
            # Let's make saturation vary from 0.5 to 1.0 of original (wider range)
            # Let's make value vary from 0.6 to 1.0 of original (wider range)
            new_s = int(s * (0.5 + firefly['color_offset'] * 0.5)) # Increased range
            new_v = int(v * (0.6 + firefly['color_offset'] * 0.4)) # Increased range

            # Ensure values are within valid HSV ranges (0-255 for s, v)
            new_s = max(0, min(255, new_s))
            new_v = max(0, min(255, new_v))

            firefly_color = QtGui.QColor.fromHsv(h, new_s, new_v, int(255 * (0.3 + pulse_factor * 0.7)))

            painter.setBrush(QtGui.QBrush(firefly_color))
            painter.setPen(QtCore.Qt.NoPen)

            current_size = firefly['size'] * (0.5 + pulse_factor * 0.5)
            painter.drawEllipse(int(firefly['x'] - current_size / 2), int(firefly['y'] - current_size / 2), int(current_size), int(current_size))
        painter.setClipRect(self.rect()) # Reset clip rect
