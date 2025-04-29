from PyQt6.QtWidgets import QFileDialog, QWidget, QMessageBox
import requests
from shrub_archi.ui.core_ui import get_ui_app, do_ui_execute, UIWidget
from typing import Optional


class FileOpenUI(QWidget):
    def __init__(self):
        super().__init__()
        self.opened_file: Optional[str] = None

    def open_file_dialog(self, path: str) -> "FileOpenUI":
        file_path, _ = QFileDialog.getOpenFileName(self, caption="Open File", directory=path, filter= "All Files (*)")
        if not file_path:
            return self
        else:
            self.opened_file = file_path

        return self

def do_show_file_open_ui(path: str = None) -> str:
    get_ui_app()
    widget = FileOpenUI().open_file_dialog(path)

    return widget.opened_file



if __name__ == "__main__":
    get_ui_app()
    print(do_show_file_open_ui())



