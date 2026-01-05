from PySide6.QtWidgets import QFileDialog, QWidget
from shrub_ui.ui.core_ui import get_ui_app
from typing import Optional


class FileOpenUI(QWidget):
    def __init__(self):
        super().__init__()
        self.opened_file: Optional[str] = None

    def open_file_dialog(self, path: str) -> "FileOpenUI":
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", path, filter= "All Files (*)", options=options)
        if not file_path:
            return self
        else:
            self.opened_file = file_path

        return self

def do_show_file_open_ui(path: str = None) -> str:
    get_ui_app()
    widget = FileOpenUI().open_file_dialog(path)

    return widget.opened_file
    #return path


if __name__ == "__main__":
    print(do_show_file_open_ui())



