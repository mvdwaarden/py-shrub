from PySide6.QtWidgets import QFileDialog, QWidget
from shrub_ui.ui.core_ui import get_ui_app
from typing import Optional
from shrub_util.core.config import Config
from shrub_archi.config.consts import ShrubArchi
from typing import List

class FileOpenUI(QWidget):
    def __init__(self):
        super().__init__()
        self.opened_file: Optional[str] = None

    def open_file_dialog(self, title: str = None, path: str = None, is_folder: bool = False) -> "FileOpenUI":
        options = QFileDialog.Options()
        if not Config().get_section(ShrubArchi.CONFIGURATION_SECTION).get_setting("UseNativeFileDialog"):
            options |= QFileDialog.Option.DontUseNativeDialog
        if is_folder:
            options |= QFileDialog.Option.ShowDirsOnly
        if title is None:
            title = "Select Folder" if is_folder else "Open File"
        if is_folder:
            file_path = QFileDialog.getExistingDirectory(self, title, path, options=options)
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, title, path, filter= "All Files (*)", options=options)
        if not file_path:
            return self
        else:
            self.opened_file = file_path

        return self

def do_show_file_open_ui(title: str = None, path: str = None, is_folder: bool = False) -> str:
    get_ui_app()
    widget = FileOpenUI().open_file_dialog(title=title, path=path, is_folder=is_folder)

    return widget.opened_file
    #return path


if __name__ == "__main__":
    print(do_show_file_open_ui())



