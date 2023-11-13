import sys
from typing import List

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, \
    QHBoxLayout, QPushButton, QTableView

from .identity_resolver import ResolvedIdentity


class ResolutionTableModel(QAbstractTableModel):
    def __init__(self, resolutions: List[ResolvedIdentity]):
        super(ResolutionTableModel, self).__init__()
        self.resolutions = resolutions
        self._filtered_data = resolutions

    def rowCount(self, parent=None):
        return len(self._filtered_data)

    def columnCount(self, parent=None):
        return 6  # Number of columns (checkbox, label1, label2)

    def data(self, index: QModelIndex, role: int = ...):
        if not index.isValid() or index.row() >= len(self._filtered_data):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            res_id = self._filtered_data[index.row()]
            match index.column():
                case 0:
                    return ''  # Checkbox column
                case 1:
                    return res_id.resolver_result.score
                case 2:
                    return res_id.resolver_result.rule
                case 3:
                    return res_id.identity1.classification
                case 4:
                    return res_id.identity1.name
                case 5:
                    return res_id.identity2.name
                case _:
                    return "?"
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 0:
            res_id = self._filtered_data[index.row()]
            match res_id.resolver_result.manual_verification:
                case True:
                    return Qt.CheckState.Checked
                case False:
                    return Qt.CheckState.Unchecked
                case _:
                    return Qt.CheckState.PartiallyChecked

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return ['Equal', 'Score', 'Rule', 'Class', 'Identity1', 'Identity2'][
                    section]

    def flags(self, index):
        flags = super(ResolutionTableModel, self).flags(index)
        if index.column() == 0:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def filter_data(self, search_text):
        if not search_text:
            self._filtered_data = self.resolutions
        else:
            search_text_lower = search_text.lower()

            def hit(res_id: ResolvedIdentity):
                def hit_identity(identity):
                    return (
                            identity.name and search_text_lower in identity.name.lower()) or (
                            identity.description and search_text_lower in identity.description.lower()) or (
                            identity.classification and search_text_lower in identity.classification.lower())

                def hit_resolve_result(res):
                    return search_text in str(res.score) or search_text_lower in str(
                        res.rule.lower())

                result = hit_identity(res_id.identity1) or hit_identity(
                    res_id.identity2) or hit_resolve_result(res_id.resolver_result)
                return result

            self._filtered_data = [res_id for res_id in self.resolutions if hit(res_id)]
        self.layoutChanged.emit()

    def toggle_manual_verification(self):
        for res_id in self._filtered_data:
            match res_id.resolver_result.manual_verification:
                case True:
                    res_id.resolver_result.manual_verification = False
                case False:
                    res_id.resolver_result.manual_verification = None
                case _:
                    res_id.resolver_result.manual_verification = True
        self.layoutChanged.emit()


class ResolverUI(QWidget):
    COL_COUNT: int = 6

    def __init__(self, resolutions: List[ResolvedIdentity]):
        super().__init__()
        self.resolutions = resolutions
        self.model = ResolutionTableModel(self.resolutions)
        self.initUI()
        self.ok = False

    def initUI(self):
        # Set window title
        self.setWindowTitle('Tick all identities that should be considered equal')

        # Create vertical layout
        layout = QVBoxLayout(self)

        # Create search box
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText('Search...')
        layout.addWidget(self.search_box)
        # Create list widget
        # Create table widget
        self.table_widget = QTableView(self)
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

        # Connect cell click signal to toggle checkbox function
        # Connect header click signal to toggle checkboxes function
        self.table_widget.horizontalHeader().sectionClicked.connect(
            self.toggle_checkboxes)

        self.table_widget.setModel(self.model)

    def filter_table(self, text):
        self.model.filter_data(text)

    def toggle_checkboxes(self, column):
        self.model.toggle_manual_verification()

    def save_data(self):
        # Implement the save logic here
        self.close()
        self.ok = True


def do_show_resolve_ui(resolved_ids: List[ResolvedIdentity]) -> bool:
    # Initialize and run the application
    app = QApplication(sys.argv)
    widget = ResolverUI(resolved_ids)
    widget.show()
    app.exec()
    return widget.ok
