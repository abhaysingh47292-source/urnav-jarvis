import math
import random
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QRadialGradient, QLinearGradient, QPainterPath

class Particle:
    def __init__(self, width: float, height: float):
        self.reset(width, height)
        self.y = random.uniform(0, max(height, 10))

    def reset(self, width: float, height: float):
        self.x = random.uniform(0, max(width, 10))
        self.y = random.uniform(height * 0.4, height + 5)
        self.radius = random.uniform(2.0, 5.5)
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = random.uniform(-0.8, -0.2)
        self.alpha = random.uniform(0.35, 0.9)
        self.phase = random.uniform(0, math.pi * 2)
        self.phase_speed = random.uniform(0.04, 0.09)
        # Gemini vibrant solar orange & pure white palette
        palette = [
            QColor(255, 107, 0),    # Vibrant Solar Orange
            QColor(255, 140, 0),    # Dark Orange / Amber
            QColor(255, 180, 50),   # Warm Gold
            QColor(255, 255, 255),  # Pure White Star
            QColor(255, 75, 0),     # Deep Electric Orange
        ]
        self.color = random.choice(palette)

    def update(self, width: float, height: float, intensity: float = 1.0):
        self.phase += self.phase_speed * intensity
        self.x += (self.vx + math.sin(self.phase) * 0.4) * intensity
        self.y += self.vy * intensity

        # Wrap around or reset
        if self.y < -10 or self.x < -20 or self.x > width + 20:
            self.reset(width, height)
            self.y = height + random.uniform(0, 10)

class GeminiParticleWave(QWidget):
    """
    High-fidelity Google Gemini-style animated particle aura and light wave.
    Provides living energy feedback in Solar Orange & Pure White.
    Supports states: 'idle', 'listening', 'thinking', 'speaking'.
    """
    def __init__(self, parent=None, height: int = 50, particle_count: int = 36):
        super().__init__(parent)
        self.setFixedHeight(height)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.particle_count = particle_count
        self.particles = []
        self.state = "idle"  # idle, listening, thinking, speaking
        self.state_intensity = 1.0
        self.wave_phase = 0.0

        # Colors
        self.color_primary = QColor(255, 107, 0)     # #FF6B00
        self.color_secondary = QColor(255, 165, 0)   # #FFA500
        self.color_highlight = QColor(255, 255, 255) # White

        # Initialize particles
        for _ in range(self.particle_count):
            self.particles.append(Particle(700, height))

        # 40 FPS render loop (~25ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(25)

    def set_state(self, state: str):
        self.state = state
        if state == "listening":
            self.state_intensity = 2.4
        elif state == "thinking":
            self.state_intensity = 1.8
        elif state == "speaking":
            self.state_intensity = 2.0
        else:
            self.state_intensity = 1.0

    def set_accent_color(self, hex_color: str):
        try:
            self.color_primary = QColor(hex_color)
            self.color_secondary = self.color_primary.lighter(130)
        except Exception:
            pass

    def _tick(self):
        w = max(self.width(), 100)
        h = max(self.height(), 20)

        # Ensure correct particle count for size
        if len(self.particles) < self.particle_count:
            self.particles.append(Particle(w, h))

        self.wave_phase += 0.05 * self.state_intensity

        for p in self.particles:
            p.update(w, h, intensity=self.state_intensity)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Base ambient bottom glow
        glow_grad = QLinearGradient(0, h, 0, 0)
        glow_color = QColor(self.color_primary)
        alpha_base = 50 if self.state == "idle" else 110
        glow_color.setAlpha(alpha_base)
        glow_grad.setColorAt(0.0, glow_color)
        glow_color_faded = QColor(self.color_secondary)
        glow_color_faded.setAlpha(0)
        glow_grad.setColorAt(1.0, glow_color_faded)

        painter.fillRect(0, 0, w, h, glow_grad)

        # 2. Fluid Wave Ribbon (Gemini Assistant Wave)
        wave_path = QPainterPath()
        wave_path.moveTo(0, h)

        steps = 30
        step_x = w / steps
        amplitude = 6.0 if self.state == "idle" else 14.0
        freq = 3.0

        for i in range(steps + 1):
            px = i * step_x
            norm_x = i / steps
            # Bell curve envelope so edges stay subtle
            envelope = math.sin(norm_x * math.pi)
            py = (h * 0.65) + math.sin(self.wave_phase + (norm_x * math.pi * freq)) * (amplitude * envelope)
            wave_path.lineTo(px, py)

        wave_path.lineTo(w, h)
        wave_path.closeSubpath()

        ribbon_brush = QLinearGradient(0, 0, w, 0)
        c1 = QColor(self.color_primary)
        c1.setAlpha(70 if self.state == "idle" else 140)
        c2 = QColor(self.color_highlight)
        c2.setAlpha(120 if self.state == "idle" else 200)
        c3 = QColor(self.color_secondary)
        c3.setAlpha(70 if self.state == "idle" else 140)

        ribbon_brush.setColorAt(0.0, c1)
        ribbon_brush.setColorAt(0.5, c2)
        ribbon_brush.setColorAt(1.0, c3)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(ribbon_brush)
        painter.drawPath(wave_path)

        # 3. Floating Glowing Particles
        for p in self.particles:
            rad = p.radius * (1.2 if self.state in ["listening", "speaking"] else 1.0)
            grad = QRadialGradient(p.x, p.y, rad * 2.2)

            # Core
            core_c = QColor(p.color)
            core_c.setAlpha(int(255 * p.alpha))
            grad.setColorAt(0.0, core_c)

            # Corona
            mid_c = QColor(p.color)
            mid_c.setAlpha(int(100 * p.alpha))
            grad.setColorAt(0.5, mid_c)

            # Halo fadeout
            fade_c = QColor(p.color)
            fade_c.setAlpha(0)
            grad.setColorAt(1.0, fade_c)

            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(p.x, p.y), rad * 2.2, rad * 2.2)

        painter.end()
