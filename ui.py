import sys
import math
import state
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QBrush,
    QPainterPath, QPixmap, QImage
)

STATE_COLORS = {
    "idle":      QColor(80, 200, 100),
    "listening": QColor(255, 210, 50),
    "thinking":  QColor(50, 160, 210),
    "speaking":  QColor(60, 210, 185),
}

BUBBLE_SIZE = 50
LOGO_PATH = "logo.png"
NUM_POINTS = 128


class OreaonBubble(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(BUBBLE_SIZE * 2 + 40, BUBBLE_SIZE * 2 + 40)

        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20,
                  screen.height() - self.height() - 60)

        self._drag_pos = None
        self._pulse = 0.0
        self._current_color = STATE_COLORS["idle"]
        self._target_color = STATE_COLORS["idle"]
        self._blend = 1.0
        self._last_state = "idle"

        self._logo = self._load_logo_transparent(LOGO_PATH)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

        self._state_timer = QTimer(self)
        self._state_timer.timeout.connect(self._poll_state)
        self._state_timer.start(100)

    def _load_logo_transparent(self, path):
        img = QImage(path)
        if img.isNull():
            return None
        img = img.convertToFormat(QImage.Format_ARGB32)
        for y in range(img.height()):
            for x in range(img.width()):
                px = img.pixel(x, y)
                r = (px >> 16) & 0xFF
                g = (px >> 8) & 0xFF
                b = px & 0xFF
                if r < 40 and g < 40 and b < 40:
                    img.setPixel(x, y, 0x00000000)
        return QPixmap.fromImage(img)

    def _poll_state(self):
        s = getattr(state, "current_state", "idle")
        if s != self._last_state:
            self._current_color = self._blended_color(self._blend)
            self._target_color = STATE_COLORS.get(s, STATE_COLORS["idle"])
            self._blend = 0.0
            self._last_state = s

    def _blended_color(self, t):
        c = self._current_color
        g = self._target_color
        r  = int(c.red()   + (g.red()   - c.red())   * t)
        gv = int(c.green() + (g.green() - c.green()) * t)
        b  = int(c.blue()  + (g.blue()  - c.blue())  * t)
        return QColor(r, gv, b)

    def _tick(self):
        self._pulse += 0.025  # never reset — sine is periodic, flows naturally forever
        if self._blend < 1.0:
            self._blend = min(1.0, self._blend + 0.07)
        self.update()

    def _build_blob_path(self, cx, cy, base_r, t):
        path = QPainterPath()
        points = []
        for i in range(NUM_POINTS):
            angle = (2 * math.pi * i) / NUM_POINTS
            r = base_r
            r += math.sin(angle * 3 + t * 1.1) * 2.5
            r += math.sin(angle * 5 - t * 0.7) * 1.5
            r += math.sin(angle * 7 + t * 1.7) * 1.0
            r += math.sin(angle * 2 - t * 0.5) * 2.0
            points.append(QPointF(cx + r * math.cos(angle),
                                  cy + r * math.sin(angle)))

        path.moveTo(points[0])
        n = len(points)
        for i in range(n):
            p0 = points[(i - 1) % n]
            p1 = points[i]
            p2 = points[(i + 1) % n]
            p3 = points[(i + 2) % n]
            cp1x = p1.x() + (p2.x() - p0.x()) / 6
            cp1y = p1.y() + (p2.y() - p0.y()) / 6
            cp2x = p2.x() - (p3.x() - p1.x()) / 6
            cp2y = p2.y() - (p3.y() - p1.y()) / 6
            path.cubicTo(cp1x, cp1y, cp2x, cp2y, p2.x(), p2.y())

        path.closeSubpath()
        return path

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx = self.width() / 2
        cy = self.height() / 2
        base_r = BUBBLE_SIZE / 2
        color = self._blended_color(self._blend)

        # Outer glow
        glow_color = QColor(color)
        glow_color.setAlpha(45)
        painter.setBrush(QBrush(glow_color))
        painter.setPen(Qt.NoPen)
        painter.drawPath(self._build_blob_path(cx, cy, base_r + 14, self._pulse))

        # Main blob
        grad = QRadialGradient(cx - base_r * 0.2, cy - base_r * 0.25, base_r * 1.3)
        bright = color.lighter(145)
        bright.setAlpha(235)
        dark = color.darker(135)
        dark.setAlpha(225)
        grad.setColorAt(0.0, bright)
        grad.setColorAt(1.0, dark)
        painter.setBrush(QBrush(grad))
        painter.drawPath(self._build_blob_path(cx, cy, base_r, self._pulse))

        # Specular highlight
        hl_r = base_r * 0.25
        hx = cx - base_r * 0.25
        hy = cy - base_r * 0.28
        hl = QRadialGradient(hx, hy, hl_r)
        hl.setColorAt(0.0, QColor(255, 255, 255, 150))
        hl.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(hl))
        painter.drawEllipse(int(hx - hl_r), int(hy - hl_r),
                            int(hl_r * 2), int(hl_r * 2))

        # Logo
        if self._logo and not self._logo.isNull():
            logo_size = int(base_r * 1.6)
            scaled = self._logo.scaled(logo_size, logo_size,
                                       Qt.KeepAspectRatio,
                                       Qt.SmoothTransformation)
            painter.drawPixmap(int(cx - scaled.width() / 2),
                               int(cy - scaled.height() / 2),
                               scaled)

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


def run_ui():
    app = QApplication(sys.argv)
    bubble = OreaonBubble()
    bubble.show()
    app.exec_()


if __name__ == "__main__":
    run_ui()