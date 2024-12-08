import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

class CalWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.pickColorButton = QPushButton('①拾取色标(必选)', self)
        self.pickThemeButton = QPushButton('②拾取主体(必选)', self)
        self.pickSpecialButton = QPushButton('导入图片', self)
        layout.addWidget(self.pickSpecialButton)
        layout.addWidget(self.pickColorButton)
        layout.addWidget(self.pickThemeButton)
        

        self.graphicsView = QGraphicsView(self)
        self.scene = QGraphicsScene(self)
        self.graphicsView.setScene(self.scene)

        layout.addWidget(self.graphicsView)

        self.setLayout(layout)
        self.setWindowTitle('计算波及区域')
        self.setGeometry(100, 100, 800, 600)

        font = QFont()
        font.setPointSize(11)  # Set the desired font size
        self.pickColorButton.setFont(font)
        self.pickThemeButton.setFont(font)
        self.pickSpecialButton.setFont(font)
        

        # Example to load a PNG image
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = CalWindow()
    mainWindow.show()
    sys.exit(app.exec_())