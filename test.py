from PySide2.QtWidgets import QApplication, QWidget, QHBoxLayout, QFontComboBox, QLabel

class Example(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        hbox = QHBoxLayout(self)
        fontCombo = QFontComboBox(self)
        fontCombo.currentFontChanged.connect(self.setFont)
        hbox.addWidget(fontCombo)
        self.label = QLabel('Hello, world', self)
        hbox.addWidget(self.label)

        self.show()

    def setFont(self, font):
        self.label.setFont(font)
        # 将字体定义到全局变量
        global appFont
        appFont = font

if __name__ == '__main__':
    app = QApplication([])
    ex = Example()
    app.exec_()
