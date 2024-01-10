from PyQt6.QtCore import Qt, QAbstractItemModel, QModelIndex
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTreeView, QGridLayout, QWidget, QPushButton
from PyQt6.QtCore import QDataStream, QIODevice, QByteArray, QMimeData


class TreeItem:
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0

    def insertChild(self, position, item):
        self.childItems.insert(position, item)

    def removeChild(self, position):
        del self.childItems[position]

class TreeModel(QAbstractItemModel):
    def __init__(self, data, parent=None):
        super(TreeModel, self).__init__(parent)
        self.rootItem = TreeItem(["Title"])
        self.setupModelData(data.split('\n'), self.rootItem)

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        item = index.internalPointer()
        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.rootItem.data(section)
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        childItem = index.internalPointer()
        parentItem = childItem.parent()
        if parentItem == self.rootItem:
            return QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        return parentItem.childCount()

    def setupModelData(self, lines, parent):
        for line in lines:
            data = [line]
            item = TreeItem(data, parent)
            parent.appendChild(item)

    def insertChild(self, parentIndex, childData):
        if not parentIndex.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parentIndex.internalPointer()

        self.beginInsertRows(parentIndex, parentItem.childCount(), parentItem.childCount())
        childItem = TreeItem([childData], parentItem)
        parentItem.appendChild(childItem)
        self.endInsertRows()
        return True

    def mimeTypes(self):
        return ['application/x-qabstractitemmodeldatalist']

    def mimeData(self, indexes):
        mimeData = QMimeData()
        encodedData = QByteArray()
        stream = QDataStream(encodedData, QIODevice.OpenModeFlag.WriteOnly)

        for index in indexes:
            if index.isValid():
                text = self.data(index, Qt.ItemDataRole.DisplayRole)
                stream << QByteArray(text.encode())

        mimeData.setData('application/x-qabstractitemmodeldatalist', encodedData)
        return mimeData

    def dropMimeData(self, data, action, row, column, parentIndex):
        if action == Qt.DropAction.IgnoreAction:
            return True

        if not data.hasFormat('application/x-qabstractitemmodeldatalist'):
            return False

        if column > 0:
            return False

        beginRow = 0
        if row != -1:
            beginRow = row
        elif parentIndex.isValid():
            beginRow = parentIndex.row()
        else:
            beginRow = self.rootItem.childCount()

        encodedData = data.data('application/x-qabstractitemmodeldatalist')
        stream = QDataStream(encodedData, QIODevice.OpenModeFlag.ReadOnly)

        while not stream.atEnd():
            text = QByteArray()
            stream >> text
            self.insertRows(beginRow, 1, parentIndex)
            self.setData(self.index(beginRow, 0, parentIndex), text, Qt.ItemDataRole.EditRole)
            beginRow += 1

        return True

    def insertRows(self, position, rows, parent=QModelIndex()):
        parentItem = self.getItem(parent)
        self.beginInsertRows(parent, position, position + rows - 1)
        for row in range(rows):
            childItem = TreeItem("New Item", parentItem)
            parentItem.insertChild(position, childItem)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QModelIndex()):
        parentItem = self.getItem(parent)
        self.beginRemoveRows(parent, position, position + rows - 1)
        for row in range(rows):
            success = parentItem.removeChild(position)
        self.endRemoveRows()
        return success

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.rootItem
    def supportedDropActions(self):
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem

def createTableWidget():
    table_widget = QTableWidget(5, 3)  # 5 rows, 3 columns
    table_widget.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])

    for row in range(5):
        for column in range(3):
            item = QTableWidgetItem(f"Item {row},{column}")
            table_widget.setItem(row, column, item)

    return table_widget

# ... [previous code for imports and TreeItem, TreeModel definitions] ...

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create Tree View with Model
        self.tree_view = QTreeView()
        sample_data = "Node 1\nNode 2\nNode 3"
        self.tree_model = TreeModel(sample_data)
        self.tree_view.setDragEnabled(True)
        self.tree_view.setAcceptDrops(True)
        self.tree_view.setDragDropMode(QTreeView.DragDropMode.DragDrop)
        self.tree_view.setModel(self.tree_model)

        # Create Table Widget (Grid)
        self.table_widget = createTableWidget()

        # Create a grid layout and add widgets
        self.grid_layout = QGridLayout(self.central_widget)
        self.grid_layout.addWidget(self.tree_view, 0, 0)
        self.grid_layout.addWidget(self.table_widget, 0, 1)

        self.setWindowTitle("Tree View and Grid Layout Example")
        self.add_child_button = QPushButton("Add Child Node")
        self.add_child_button.clicked.connect(self.addChildNode)

        self.grid_layout.addWidget(self.add_child_button, 1, 0)  # Add button below the tree view
        self.tree_view.selectionModel().selectionChanged.connect(self.onSelectionChanged)

        self.resize(800, 600)

    def addChildNode(self):
        selectedIndexes = self.tree_view.selectedIndexes()
        if not selectedIndexes:
            parentIndex = QModelIndex()
        else:
            parentIndex = selectedIndexes[0]

        childData = "New Node"
        self.tree_model.insertChild(parentIndex, childData)

    def onSelectionChanged(self, selected, deselected):
        # Clear existing data in TableWidget
        self.table_widget.clearContents()
        self.table_widget.setRowCount(0)

        # Get the currently selected item in the TreeView
        indexes = selected.indexes()
        if indexes:
            item = indexes[0].internalPointer()

            # Update the TableWidget based on the selected item
            # This is a simple example; you might want to customize this part
            for row in range(5):
                self.table_widget.insertRow(row)
                for column in range(3):
                    newItem = QTableWidgetItem(f"{item.data(0)}: Row {row}, Col {column}")
                    self.table_widget.setItem(row, column, newItem)
def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
