from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from dialectics_studio.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Historical Dialectics Studio")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
