import sys
from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, \
    QCheckBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton

from .identity_resolver import ResolvedIdentity


class ResolverUI(QWidget):
    COL_COUNT: int = 6

    def __init__(self, resolutions: List[ResolvedIdentity]):
        super().__init__()
        self.resolutions = resolutions
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
        self.table_widget = QTableWidget(self)
        self.table_widget.setColumnCount(self.COL_COUNT)
        self.table_widget.setHorizontalHeaderLabels(
            ['Equal', 'Score', 'Rule', 'Class', 'Identity1', 'Identity2'])
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
        self.toUI()

    def filter_table(self, text):
        for row in range(self.table_widget.rowCount()):
            match = False
            for col in range(1, self.COL_COUNT):
                item = self.table_widget.item(row, col)
                cell_text = item.text().lower() if item else None
                if item and text.lower() in cell_text:
                    match = True
                    break
            self.table_widget.setRowHidden(row, not match)

    def toggle_checkboxes(self, column):
        if column == 0:
            for row in range(self.table_widget.rowCount()):
                # Check if the row is visible before toggling the checkbox
                if not self.table_widget.isRowHidden(row):
                    checkbox = self.table_widget.cellWidget(row, 0)
                    match checkbox.checkState():
                        case Qt.CheckState.PartiallyChecked:
                            checkbox.setCheckState(Qt.CheckState.Checked)
                        case Qt.CheckState.Checked:
                            checkbox.setCheckState(Qt.CheckState.Unchecked)
                        case Qt.CheckState.Unchecked:
                            checkbox.setCheckState(Qt.CheckState.PartiallyChecked)

    def toUI(self):
        # Add items with checkboxes and labels
        i = 0
        self.table_widget.setRowCount(len(self.resolutions))
        for resolved_id in self.resolutions:  # Checkbox
            column = 0
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setTristate(True)
            match resolved_id.resolver_result.manual_verification:
                case True:
                    checkbox.setCheckState(Qt.CheckState.Checked)
                case False:
                    checkbox.setCheckState(Qt.CheckState.Unchecked)
                case _:
                    checkbox.setCheckState(Qt.CheckState.PartiallyChecked)

            self.table_widget.setCellWidget(i, column, checkbox)
            column += 1
            # Score
            score = QTableWidgetItem(f'{resolved_id.resolver_result.score}')
            self.table_widget.setItem(i, column, score)
            column += 1
            # Equals rule
            rule = QTableWidgetItem(f'{resolved_id.resolver_result.rule}')
            self.table_widget.setItem(i, column, rule)
            column += 1
            # Class
            classification = QTableWidgetItem(f'{resolved_id.identity1.classification}')
            self.table_widget.setItem(i, column, classification)
            column += 1
            # Identity 1 label
            id1_label = QTableWidgetItem(f'{resolved_id.identity1.name}')
            id1_label.setToolTip(f"{resolved_id.identity1.description}")
            self.table_widget.setItem(i, column, id1_label)
            column += 1
            # Identity 2 label
            id2_label = QTableWidgetItem(f'{resolved_id.identity2.name}')
            id2_label.setToolTip(f"{resolved_id.identity2.description}")
            self.table_widget.setItem(i, column, id2_label)
            column += 1
            i += 1

    def fromUI(self):
        for row in range(self.table_widget.rowCount()):
            # Check if the row is visible before toggling the checkbox
            checkbox = self.table_widget.cellWidget(row, 0)
            if checkbox:
                match checkbox.checkState():
                    case Qt.CheckState.PartiallyChecked:
                        self.resolutions[
                            row].resolver_result.manual_verification = None
                    case Qt.CheckState.Checked:
                        self.resolutions[
                            row].resolver_result.manual_verification = True
                    case Qt.CheckState.Unchecked:
                        self.resolutions[
                            row].resolver_result.manual_verification = False

    def save_data(self):
        # Implement the save logic here
        self.fromUI()
        self.close()
        self.ok = True


def do_show_resolve_ui(resolved_ids: List[ResolvedIdentity]) -> bool:
    # Initialize and run the application
    app = QApplication(sys.argv)
    widget = ResolverUI(resolved_ids)
    widget.show()
    app.exec()
    return widget.ok
