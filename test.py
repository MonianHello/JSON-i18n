from PySide2.QtWidgets import QApplication, QMainWindow, QStatusBar

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 创建一个状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # 在状态栏上显示文本信息
        self.statusBar.showMessage("欢迎使用我的应用！")


if __name__ == "__main__":
    app = QApplication([])
    window = MyMainWindow()
    window.show()
    app.exec_()
