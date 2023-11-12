from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget, QLineEdit, \
    QCheckBox, QListWidgetItem, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton
from identity_resolver import ResolvedIdentity
from typing import List
import sys

class ResolverUI(QWidget):
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
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(['Verified', 'Rule','Identity1', 'Identity2'])
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
            for col in range(1, 3):
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
                    if checkbox:
                        checkbox.setChecked(not checkbox.isChecked())

    def toUI(self):
        # Add items with checkboxes and labels
        i = 0
        self.table_widget.setRowCount(len(self.resolved_ids))
        for resolved_id in self.resolved_ids:            # Checkbox
            checkbox = QCheckBox()
            checkbox.setText(f"{resolved_id.compare_result.score}")
            checkbox.setChecked(resolved_id.compare_result.verified or resolved_id.compare_result.has_max_score())
            self.table_widget.setCellWidget(i, 0, checkbox)

            # Label 1
            label1 = QTableWidgetItem(f'{resolved_id.compare_result.rule}')
            self.table_widget.setItem(i, 1, label1)

            # Label 2
            label2 = QTableWidgetItem(f'{resolved_id.identity1.name}')
            label2.setToolTip(f"{resolved_id.identity1.description}")
            self.table_widget.setItem(i, 2, label2)

            # Label 3
            label3 = QTableWidgetItem(f'{resolved_id.identity2.name}')
            label3.setToolTip(f"{resolved_id.identity2.description}")
            self.table_widget.setItem(i, 3, label3)
            i += 1

    def fromUI(self):
        for row in range(self.table_widget.rowCount()):
            # Check if the row is visible before toggling the checkbox
            checkbox = self.table_widget.cellWidget(row, 0)
            if checkbox:
                self.resolved_ids[row].compare_result.verified = checkbox.isChecked()

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