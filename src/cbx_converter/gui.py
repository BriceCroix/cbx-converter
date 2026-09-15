try:
    from PySide6 import QtCore, QtWidgets

    _has_pyside = True
except ImportError():
    _has_pyside = False


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.text = QtWidgets.QLabel("Hello world", alignment=QtCore.Qt.AlignCenter)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
