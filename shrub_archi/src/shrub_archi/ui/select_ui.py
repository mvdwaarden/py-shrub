import sys
from abc import abstractmethod
from typing import List, Optional, Dict, Any, Tuple
import os
import yaml

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QHBoxLayout,
    QPushButton,
    QTableView,
    QApplication,
)


class TableSelectModel(QAbstractTableModel):
    COL_COUNT: int = ...
    HEADER_LABELS: List[str] = ...

    def __init__(self, data: List, tristate: bool = True):
        super(TableSelectModel, self).__init__()
        self._data = data
        self._tristate_data = {self.row_hash(row): False for row in data}
        self._filtered_data = data
        # governs if selection is tri state (None, True, False) or dual state (True/False)
        self._tristate = tristate

    def rowCount(self, parent=None):
        return len(self._filtered_data)

    def columnCount(self, parent=None):
        return self.COL_COUNT  # Number of columns (checkbox, label1, label2)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return [*self.HEADER_LABELS][section]
            elif orientation == Qt.Orientation.Vertical:
                return section + 1

    def flags(self, index):
        flags = super(TableSelectModel, self).flags(index)
        if index.column() == 0:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def filter_data(self, search_text):
        if not search_text:
            self._filtered_data = self._data
        else:
            search_text_lower = search_text.lower()
            self._filtered_data = [
                row for row in self._data if self.hit_row(row, search_text_lower)
            ]
        self.layoutChanged.emit()

    def toggle_rows(self, selected_indexes: List):
        for index in selected_indexes:
            self._toggle_row(self._filtered_data[index.row()])
        self.layoutChanged.emit()

    def data(self, index: QModelIndex, role: int = ...):
        if not index.isValid() or index.row() >= len(self._filtered_data):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self.column_value_for(
                self._filtered_data[index.row()], index.column()
            )
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 0:
            match self._is_selected(self._filtered_data[index.row()]):
                case True:
                    return Qt.CheckState.Checked
                case False:
                    return Qt.CheckState.Unchecked
                case _:
                    return Qt.CheckState.PartiallyChecked

        return None

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 0:
            self._toggle_row(self._filtered_data[index.row()])
            return True
        return False

    def _toggle_row(self, row):
        selection_idx = self.row_hash(row)
        if self._tristate:
            match self._tristate_data[selection_idx]:
                case True:
                    new_status = None
                case False:
                    new_status = True
                case _:
                    new_status = False
        else:
            new_status = not self._tristate_data[selection_idx]
        self._tristate_data[selection_idx] = new_status

    def _is_selected(self, row) -> Optional[bool]:
        return self._tristate_data[self.row_hash(row)]

    def set_selected(self, row, selected: Optional[bool]):
        self._tristate_data[self.row_hash(row)] = selected

    @abstractmethod
    def hit_row(self, row, search_text: str):
        ...

    @abstractmethod
    def column_value_for(self, row, column: int):
        ...

    def row_hash(self, row):
        return row


class TableSelectUI(QWidget):
    def __init__(self, model: TableSelectModel, ok_text: str, title: str):
        super().__init__()
        self._screen_data = None
        self.model: TableSelectModel = model
        self.ok_text = ok_text
        self.title = title
        self.initUI()
        self.ok = False

    def initUI(self):
        # Set window title
        window_title = (
            self.title if self.title else "Press SPACE or T to mark selected rows"
        )
        self.setWindowTitle(window_title)
        # read screen data
        self._read_screen_data()
        # set size
        if self._screen_data:
            d = self._screen_data
            self.setGeometry(d["x"], d["y"], d["w"], d["h"])
        # Create vertical layout
        layout = QVBoxLayout(self)

        # Create search box
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Search...")
        layout.addWidget(self.search_box)

        class FilterTableView(QTableView):
            def __init__(self, parent, outer: TableSelectUI):
                super().__init__(parent)
                self.outer: TableSelectUI = outer

            def keyPressEvent(self, event):
                if event.key() == Qt.Key.Key_T or event.key() == Qt.Key.Key_Space:
                    self.outer.toggle_checkboxes(0)
                else:
                    super().keyPressEvent(event)

        # Create table widget
        self.table_widget = FilterTableView(self, self)
        layout.addWidget(self.table_widget)
        # Buttons layout
        buttons_layout = QHBoxLayout()

        # Save button
        self.save_button = QPushButton(self.ok_text if self.ok_text else "OK")
        self.save_button.clicked.connect(self.save_data)
        buttons_layout.addWidget(self.save_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        buttons_layout.addWidget(self.cancel_button)

        # Add buttons layout to the main layout
        layout.addLayout(buttons_layout)

        # Add listeners

        # Connect search box signal to filter function
        self.search_box.textChanged.connect(self.filter_table)

        # Connect header click signal to toggle checkboxes function
        # self.table_widget.horizontalHeader().sectionClicked.connect(
        #     self.toggle_checkboxes)
        self.table_widget.setModel(self.model)

    def filter_table(self, text):
        self.model.filter_data(text)

    def toggle_checkboxes(self, column):
        self.model.toggle_rows(self.table_widget.selectionModel().selectedRows())

    def save_data(self):
        # Implement the save logic here
        self.close()
        self.ok = True

    def closeEvent(self, event):
        if not self._screen_data:
            self._screen_data = {}

        self._screen_data["x"] = self.geometry().x()
        self._screen_data["y"] = self.geometry().y()
        self._screen_data["w"] = self.geometry().width()
        self._screen_data["h"] = self.geometry().height()
        self._write_screen_data()
        super().closeEvent(event)

    def _read_screen_data(self):
        if os.path.exists("./archi_screens.dat"):
            with open("./archi_screens.dat", "r") as asd:
                screens_data = yaml.safe_load(asd.read())
            if screens_data and self.title in screens_data:
                self._screen_data = screens_data[self.title if self.title else "default_screen"]
        if not screens_data:
            screens_data = {}
        return screens_data

    def _write_screen_data(self):
        if self._screen_data:
            screens_data = self._read_screen_data()
            screens_data[self.title if self.title else "default_screen"] = self._screen_data
            with open("./archi_screens.dat", "w") as asd:
                asd.write(yaml.safe_dump(screens_data))


def do_show_select_ui(
    model: TableSelectModel, ok_text: str = None, title: str = None
) -> Tuple[bool, Dict[Any, Optional[bool]]]:
    # Initialize and run the application
    app = QApplication(sys.argv)
    widget = TableSelectUI(model=model, ok_text=ok_text, title=title)
    widget.show()
    app.exec()
    if widget.ok:
        return True, {row: selected for row, selected in model._tristate_data.items()}
    else:
        return False, {}


def do_show_select_furniture_test():
    class FurnitureTableSelectModel(TableSelectModel):
        COL_COUNT = 4  # Number of columns including checkbox
        HEADER_LABELS = ["", "Name", "Type", "Material"]  # Headers for your columns

        def column_value_for(self, row, column: int):
            if column == 0:  # Assuming the first column is for checkbox
                return ""
            elif column == 1:
                return row["name"]
            elif column == 2:
                return row["type"]
            elif column == 3:
                return row["material"]  # Add more columns if needed

        def hit_row(self, row, search_text: str):
            return (
                search_text in row["name"].lower()
                or search_text in row["type"].lower()
                or search_text in row["material"].lower()
            )

        def row_hash(self, row):
            return row["name"]

    furniture_data = [
        {"name": "Chair", "type": "Seating", "material": "Wood", "color": "Brown"},
        {"name": "Sofa", "type": "Seating", "material": "Fabric", "color": "Grey"},
        # Add more furniture items here
    ]

    # Initializing the UI
    model = FurnitureTableSelectModel(furniture_data)
    do_show_select_ui(model, ok_text="Select", title="Select Furniture")
