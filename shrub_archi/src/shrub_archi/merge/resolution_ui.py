import sys
from typing import List, Optional

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, \
    QHBoxLayout, QPushButton, QTableView

from .identity_resolver import ResolvedIdentity
from abc import abstractmethod


class FilterSelectModel(QAbstractTableModel):
    COL_COUNT: int = ...
    HEADER_LABELS: List[str] = ...

    def __init__(self, data: List):
        super(FilterSelectModel, self).__init__()
        self._data = data
        self._filtered_data = data

    def rowCount(self, parent=None):
        return len(self._filtered_data)

    def columnCount(self, parent=None):
        return self.COL_COUNT  # Number of columns (checkbox, label1, label2)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return [*self.HEADER_LABELS][
                    section]
            elif orientation == Qt.Orientation.Vertical:
                return section + 1

    def flags(self, index):
        flags = super(FilterSelectModel, self).flags(index)
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
        # selection_model = self.table_view.selectionModel()
        # indexes = selection_model.selectedRows()
        # for index in indexes:
        #     row = index.row()
        #     print(f"Selected Row: {row}, Data: {self.model._filtered_data[row]}")

        for row in [index.row() for index in selected_indexes]:
            res_id = self._filtered_data[row]
            match res_id.resolver_result.manual_verification:
                case True:
                    self.toggle_row(res_id, False)
                case False:
                    self.toggle_row(res_id, None)
                case _:
                    self.toggle_row(res_id, True)
        self.layoutChanged.emit()

    def data(self, index: QModelIndex, role: int = ...):
        if not index.isValid() or index.row() >= len(self._filtered_data):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self.get_column_value_for(self._filtered_data[index.row()],
                                             index.column())
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 0:
            match self.is_selected(self._filtered_data[index.row()]):
                case True:
                    return Qt.CheckState.Checked
                case False:
                    return Qt.CheckState.Unchecked
                case _:
                    return Qt.CheckState.PartiallyChecked

        return None

    @abstractmethod
    def hit_row(self, row, search_text: str):
        ...

    @abstractmethod
    def toggle_row(self, row, search_text):
        ...

    @abstractmethod
    def get_column_value_for(self, row, column: int):
        ...

    @abstractmethod
    def is_selected(self, row: ResolvedIdentity) -> Optional[bool]:
        ...


class FilterSelectUI(QWidget):
    def __init__(self, model: FilterSelectModel):
        super().__init__()
        self.model: FilterSelectModel = model
        self.initUI()
        self.ok = False

    def initUI(self, title: str = None):
        # Set window title
        window_title = title if title else "Press SPACE or T to mark selected rows"
        self.setWindowTitle(window_title)

        # Create vertical layout
        layout = QVBoxLayout(self)

        # Create search box
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText('Search...')
        layout.addWidget(self.search_box)

        class FilterTableView(QTableView):
            def __init__(self, parent, outer: FilterSelectUI):
                super().__init__(parent)
                self.outer: FilterSelectUI = outer

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
        self.save_button = QPushButton('Save')
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


class ResolutionTableModel(FilterSelectModel):
    COL_COUNT: int = 6
    HEADER_LABELS: List[str] = ['Equal', 'Score', 'Rule', 'Class', 'Identity1',
                                'Identity2']

    def __init__(self, data: List[ResolvedIdentity]):
        super().__init__(data=data)

    def get_column_value_for(self, row: ResolvedIdentity, column: int):
        match column:
            case 0:
                return ''  # Checkbox column
            case 1:
                return row.resolver_result.score
            case 2:
                return row.resolver_result.rule
            case 3:
                return row.identity1.classification
            case 4:
                return row.identity1.name
            case 5:
                return row.identity2.name
            case _:
                return "?"

    def is_selected(self, row: ResolvedIdentity) -> Optional[bool]:
        return row.resolver_result.manual_verification

    def hit_row(self, row: ResolvedIdentity, search_text: str):
        def hit_identity(identity):
            return (
                    identity.name and search_text in identity.name.lower()) or (
                    identity.description and search_text in identity.description.lower()) or (
                    identity.classification and search_text in identity.classification.lower())

        def hit_resolve_result(res):
            return search_text in str(res.score) or search_text in str(
                res.rule.lower())

        result = hit_identity(row.identity1) or hit_identity(
            row.identity2) or hit_resolve_result(row.resolver_result)
        return result

    def toggle_row(self, row: ResolvedIdentity, status):
        row.resolver_result.manual_verification = status


def do_show_resolve_ui(resolved_ids: List[ResolvedIdentity]) -> bool:
    # Initialize and run the application
    app = QApplication(sys.argv)
    widget = FilterSelectUI(model=ResolutionTableModel(resolved_ids))
    widget.show()
    app.exec()
    return widget.ok
