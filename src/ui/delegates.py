from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QLinearGradient
from PySide6.QtWidgets import QStyledItemDelegate
from src.theme import T

PROG_ROLE = Qt.ItemDataRole.UserRole + 1

class ProgressDelegate(QStyledItemDelegate):
    _COLORS = {
        "running": ("#1d4ed8", "#3b82f6"),
        "done":    ("#15803d", "#22c55e"),
        "error":   ("#b91c1c", "#ef4444"),
        "stopped": ("#334155", "#475569"),
        "waiting": ("#1e293b", "#334155"),
    }

    def paint(self, painter, option, index):
        data = index.data(PROG_ROLE)
        if not isinstance(data, (tuple, list)) or len(data) < 2:
            super().paint(painter, option, index)
            return
        pct, state = data
        r = option.rect.adjusted(8, 10, -8, -10)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(T['bg_raised']))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(r, 3, 3)
        if pct > 0:
            c1, c2 = self._COLORS.get(state, self._COLORS["running"])
            fw = max(6, int(r.width() * min(pct, 100) / 100))
            cr = QRect(r.x(), r.y(), fw, r.height())
            g = QLinearGradient(cr.left(), 0, cr.right(), 0)
            g.setColorAt(0, QColor(c1))
            g.setColorAt(1, QColor(c2))
            painter.setBrush(g)
            painter.drawRoundedRect(cr, 3, 3)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 32)

