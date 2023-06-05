from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex, QVariant
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QListView

class CheckableItemModel(QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole:
            item = self.itemFromIndex(index)
            if item is not None:
                item.setCheckState(value)
                return True
        return super().setData(index, value, role)

    def flags(self, index):
        return super().flags(index) | Qt.ItemIsUserCheckable

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.CheckStateRole:
            item = self.itemFromIndex(index)
            if item is not None:
                return item.checkState()
        return super().data(index, role)

if __name__ == "__main__":
    app = QApplication([])
    mylist = QListView()

    # 创建一个模型并设置为 ListView 的模型
    model = CheckableItemModel()
    for i in range(4):
        item = QStandardItem(f"item{i}")
        item.setCheckState(Qt.Unchecked)
        model.appendRow(item)
    mylist.setModel(model)

    mylist.show()
    app.exec_()
