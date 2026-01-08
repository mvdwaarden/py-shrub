from PySide6.QtWidgets import QApplication, QWidget
from typing import Optional
import sys


_g_app: Optional[QApplication] = None

class UIWidget(QWidget):
    def show(self):
        get_ui_app()
        super().show()
        do_ui_execute(True)

def get_ui_app(do_execute: bool = False) -> QApplication:
    global _g_app
    if _g_app is None:
        _g_app = QApplication(sys.argv)
    if do_execute:
        do_ui_execute()
    return _g_app


def do_ui_execute(exit_on_leave: bool = False):
    if _g_app is not None:
        if exit_on_leave:
            sys.exit(_g_app.exec())
        else:
            _g_app.exec()