import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore

class StatusWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎤 Sprachaufnahme")
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool |
            QtCore.Qt.WindowMinimizeButtonHint
        )
        self.setGeometry(100, 100, 320, 90)

        # Animation properties
        self.animation_phase = 0.0
        self.animation_speed = 0.01 # Very slow animation speed

        # Firefly properties
        self.num_fireflies = 20 # Number of fireflies
        self.fireflies = []
        for i in range(self.num_fireflies):
            self.fireflies.append({
                'x': np.random.uniform(0, self.width()),
                'y': np.random.uniform(0, self.height()),
                'size': np.random.uniform(2, 8), # Size of firefly
                'color_offset': np.random.uniform(0, 1), # For different orange shades
                'phase_offset': np.random.uniform(0, 2 * np.pi), # For pulsating effect
                'speed_factor': np.random.uniform(0.5, 1.5) # Slightly varied speed
            })

        # Current firefly color
        self.current_firefly_color = QtGui.QColor(255, 165, 0) # Start with orange (normal)
        self.target_firefly_color = QtGui.QColor(255, 165, 0)

        # Animation properties for color transition
        self.color_transition_timer = QtCore.QTimer(self)
        self.color_transition_timer.timeout.connect(self.update_firefly_color)
        self.color_transition_speed = 5 # Adjust for slower/faster transition

        # Set up a timer for animation updates
        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.timeout.connect(self.animate_background)
        self.animation_timer.start(50) # Update every 50ms (20 FPS)

        self.label = QtWidgets.QLabel("Bereit", self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: Consolas, monospace;
                font-size: 10pt;
            }
        """)

        self.eleven_labs_button = QtWidgets.QPushButton("👂", self) # Ear symbol
        self.eleven_labs_button.setFixedSize(35, 35) # Make it slightly smaller
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
        # The connection will be made from TrayRecorder as it manages the new window

        # New recording button
        self.record_button = QtWidgets.QPushButton("🎙️", self) # Microphone symbol
        self.record_button.setFixedSize(35, 35) # Make it square, same size as TTS button
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
        # The connection will be made from TrayRecorder

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        
        # Create a horizontal layout for both buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.record_button) # Add record button to the left
        button_layout.addStretch(1) # Pushes the TTS button to the right
        button_layout.addWidget(self.eleven_labs_button) # Add the TTS button to the right
        
        layout.addLayout(button_layout) # Add the horizontal layout to the main layout
        self.setLayout(layout)


    @QtCore.pyqtSlot(str) # Mark as slot for thread-safe updates
    def set_status(self, text):
        self.label.setText(text)

    @QtCore.pyqtSlot()
    def _activate_window(self):
        self.activateWindow()

    @QtCore.pyqtSlot(QtGui.QColor)
    def set_firefly_color(self, color):
        self.target_firefly_color = color
        self.color_transition_timer.start(20) # Start transition

    def update_firefly_color(self):
        # Smoothly transition current_firefly_color towards target_firefly_color
        r = self.current_firefly_color.red()
        g = self.current_firefly_color.green()
        b = self.current_firefly_color.blue()

        target_r = self.target_firefly_color.red()
        target_g = self.target_firefly_color.green()
        target_b = self.target_firefly_color.blue()

        # Move towards target
        r += (target_r - r) / self.color_transition_speed
        g += (target_g - g) / self.color_transition_speed
        b += (target_b - b) / self.color_transition_speed

        self.current_firefly_color = QtGui.QColor(int(r), int(g), int(b))
        self.update() # Request repaint

        # Stop timer if colors are close enough
        if abs(r - target_r) < 1 and abs(g - target_g) < 1 and abs(b - target_b) < 1:
            self.color_transition_timer.stop()
            self.current_firefly_color = self.target_firefly_color # Ensure exact target color

    def animate_background(self):
        self.animation_phase += self.animation_speed
        if self.animation_phase > 2 * np.pi: # Reset phase after a full cycle
            self.animation_phase -= 2 * np.pi

        # Update firefly positions
        for firefly in self.fireflies:
            firefly['x'] += np.sin(self.animation_phase * firefly['speed_factor'] * 0.5) * 0.5 # Slow horizontal wobble
            firefly['y'] += np.cos(self.animation_phase * firefly['speed_factor'] * 0.6) * 0.5 # Slow vertical wobble

            # Wrap around if firefly goes off screen
            if firefly['x'] < -firefly['size']: firefly['x'] = self.width() + firefly['size']
            if firefly['x'] > self.width() + firefly['size']: firefly['x'] = -firefly['size']
            if firefly['y'] < -firefly['size']: firefly['y'] = self.height() + firefly['size']
            if firefly['y'] > self.height() + firefly['size']: firefly['y'] = -firefly['size']

        self.update() # Request a repaint

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Draw black background with subtle gradient
        gradient = QtGui.QRadialGradient(self.width() / 2, self.height() / 2, max(self.width(), self.height()) / 2)
        gradient.setColorAt(0, QtGui.QColor(0, 0, 0)) # Black center
        gradient.setColorAt(1, QtGui.QColor(20, 20, 20)) # Very dark gray at edges
        painter.fillRect(self.rect(), gradient)

        # Draw fireflies
        for firefly in self.fireflies:
            # Pulsating opacity and size
            pulse_factor = (np.sin(self.animation_phase * firefly['speed_factor'] + firefly['phase_offset']) + 1) / 2.0 # 0 to 1

            # Interpolate firefly color based on current_firefly_color and individual color_offset
            r = int(self.current_firefly_color.red() * (0.7 + firefly['color_offset'] * 0.3))
            g = int(self.current_firefly_color.green() * (0.7 + firefly['color_offset'] * 0.3))
            b = int(self.current_firefly_color.blue() * (0.7 + firefly['color_offset'] * 0.3))
            firefly_color = QtGui.QColor(r, g, b, int(255 * (0.3 + pulse_factor * 0.7))) # Vary opacity

            painter.setBrush(QtGui.QBrush(firefly_color))
            painter.setPen(QtCore.Qt.NoPen)

            current_size = firefly['size'] * (0.5 + pulse_factor * 0.5) # Pulsate size
            painter.drawEllipse(int(firefly['x'] - current_size / 2), int(firefly['y'] - current_size / 2), int(current_size), int(current_size))
