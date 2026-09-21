from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from dialectics_studio.ui.main_window import MainWindow
from dialectics_studio.engine.dossiers import preload_all_dossiers


def main() -> None:
    app = QApplication(sys.argv)
    preload_all_dossiers()  # study all characters, even inactive
    app.setApplicationName("Historical Dialectics Studio")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
