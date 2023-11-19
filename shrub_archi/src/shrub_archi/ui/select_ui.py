import sys
from abc import abstractmethod
from typing import List, Optional, Dict, Any

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QHBoxLayout, QPushButton, \
    QTableView, QApplication


class SelectModel(QAbstractTableModel):
    COL_COUNT: int = ...
    HEADER_LABELS: List[str] = ...

    def __init__(self, data: List):
        super(SelectModel, self).__init__()
        self._data = data
        self._filtered_data = data
        self._selection = {self.row_hash(row): False for row in data}

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
        flags = super(SelectModel, self).flags(index)
        if index.column() == 0:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def filter_data(self, search_text):
        if not search_text:
            self._filtered_data = self._data
        else:
            search_text_lower = search_text.lower()
            self._filtered_data = [row for row in self._data if
                                   self.hit_row(row, search_text_lower)]
        self.layoutChanged.emit()

    def toggle_rows(self, selected_indexes: List):
        for row in [index.row() for index in selected_indexes]:
            match self._selection[self.row_hash(self._filtered_data[row])]:
                case True:
                    new_value = None
                case False:
                    new_value = True
                case _:
                    new_value = False
            self._toggle_row(self._filtered_data[row], new_value)
        self.layoutChanged.emit()

    def data(self, index: QModelIndex, role: int = ...):
        if not index.isValid() or index.row() >= len(self._filtered_data):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self.column_value_for(self._filtered_data[index.row()],
                                         index.column())
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 0:
            match self._is_selected(self._filtered_data[index.row()]):
                case True:
                    return Qt.CheckState.Checked
                case False:
                    return Qt.CheckState.Unchecked
                case _:
                    return Qt.CheckState.PartiallyChecked

        return None

    def _toggle_row(self, row, status):
        self._selection[self.row_hash(row)] = status

    def _is_selected(self, row) -> Optional[bool]:
        return self._selection[self.row_hash(row)]

    def set_selected(self, row, selected: Optional[bool]):
        self._selection[self.row_hash(row)] = selected

    @abstractmethod
    def hit_row(self, row, search_text: str):
        ...

    @abstractmethod
    def column_value_for(self, row, column: int):
        ...

    def row_hash(self, row):
        return row


class SelectUI(QWidget):
    def __init__(self, model: SelectModel, ok_text: str, title: str):
        super().__init__()
        self.model: SelectModel = model
        self.ok_text = ok_text
        self.title = title
        self.initUI()
        self.ok = False

    def initUI(self):
        # Set window title
        window_title = self.title if self.title else "Press SPACE or T to mark selected rows"
        self.setWindowTitle(window_title)

        # Create vertical layout
        layout = QVBoxLayout(self)

        # Create search box
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText('Search...')
        layout.addWidget(self.search_box)

        class FilterTableView(QTableView):
            def __init__(self, parent, outer: SelectUI):
                super().__init__(parent)
                self.outer: SelectUI = outer

            def keyPressEvent(self, event):
                super().keyPressEvent(event)
                if event.key() == Qt.Key.Key_T or event.key() == Qt.Key.Key_Space:
                    self.outer.toggle_checkboxes(0)

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
        self.cancel_button = QPushButton('Cancel')
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


def do_show_select_ui(model: SelectModel, ok_text: str = None, title: str = None) -> \
        Dict[Any, Optional[bool]]:
    # Initialize and run the application
    app = QApplication(sys.argv)
    widget = SelectUI(model=model, ok_text=ok_text, title=title)
    widget.show()
    app.exec()
    if widget.ok:
        return {row: selected for row, selected in model._selection.items()}
    else:
        return {}


def do_show_select_furniture_test():
    class FurnitureSelectModel(SelectModel):
        COL_COUNT = 4  # Number of columns including checkbox
        HEADER_LABELS = ["", "Name", "Type", "Material"]  # Headers for your columns

        def column_value_for(self, row, column: int):
            if column == 0:  # Assuming the first column is for checkbox
                return ""
            elif column == 1:
                return row['name']
            elif column == 2:
                return row['type']
            elif column == 3:
                return row['material']  # Add more columns if needed

        def hit_row(self, row, search_text: str):
            return search_text in row['name'].lower() or search_text in row[
                'type'].lower() or search_text in row['material'].lower()

        def row_hash(self, row):
            return row["name"]

    furniture_data = [
        {"name": "Chair", "type": "Seating", "material": "Wood", "color": "Brown"},
        {"name": "Sofa", "type": "Seating", "material": "Fabric", "color": "Grey"},
        # Add more furniture items here
    ]

    # Initializing the UI
    model = FurnitureSelectModel(furniture_data)
    do_show_select_ui(model, ok_text="Select", title="Select Furniture")
