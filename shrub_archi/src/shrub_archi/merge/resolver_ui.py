import sys
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, \
    QCheckBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton

from identity_resolver import ResolvedIdentity


class ResolverUI(QWidget):
    COL_COUNT: int = 5

    def __init__(self, resolved_ids: List[ResolvedIdentity]):
        super().__init__()
        self.resolved_ids = resolved_ids
        self.initUI()

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
            ['Equal[score]', 'Rule', 'Class', 'Identity1', 'Identity2'])
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
                if item and text.lower() in item.text().lower():
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
                        case Qt.PartiallyChecked:
                            checkbox.setCheckState(Qt.Checked)
                        case Qt.Checked:
                            checkbox.setCheckState(Qt.Unchecked)
                        case Qt.Unchecked:
                            checkbox.setCheckState(Qt.PartiallyChecked)

    def toUI(self):
        # Add items with checkboxes and labels
        i = 0
        self.table_widget.setRowCount(len(self.resolved_ids))
        for resolved_id in self.resolved_ids:  # Checkbox
            column = 0
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setText(f"{resolved_id.resolver_result.score}")
            checkbox.setTristate(True)
            match resolved_id.resolver_result.manual_verification:
                case True:
                    checkbox.setCheckState(Qt.Checked)
                case False:
                    checkbox.setCheckState(Qt.Unchecked)
                case _:
                    checkbox.setCheckState(Qt.PartiallyChecked)

            self.table_widget.setCellWidget(i, column, checkbox)
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
                    case Qt.PartiallyChecked:
                        self.resolved_ids[
                            row].resolver_result.manual_verification = None
                    case Qt.Checked:
                        self.resolved_ids[
                            row].resolver_result.manual_verification = True
                    case Qt.Unchecked:
                        self.resolved_ids[
                            row].resolver_result.manual_verification = False

    def save_data(self):
        # Implement the save logic here
        self.fromUI()
        self.close()


def do_show_resolve_ui(resolved_ids: List[ResolvedIdentity]):
    # Initialize and run the application
    app = QApplication(sys.argv)
    widget = ResolverUI(resolved_ids)
    widget.show()
    app.exec_()
