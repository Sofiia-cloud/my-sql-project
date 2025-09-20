
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from database import fetch_data

class PostgreSQLTableModel(QAbstractTableModel):
    def __init__(self, conn, table_name: str, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.table_name = table_name
        self.columns = []
        self.rows = []
        self.refresh()

    def refresh(self):
        self.beginResetModel()
        self.columns, self.rows = fetch_data(self.conn, self.table_name)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.columns)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        return str(self.rows[index.row()][index.column()])

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        return self.columns[section] if orientation == Qt.Horizontal else str(section + 1)