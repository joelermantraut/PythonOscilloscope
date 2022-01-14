import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QDial
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, Qt

class ButtonPanel(QWidget):

    def __init__(self, plotWidget):
        super().__init__()
        self.title = 'Oscilloscope Tools'
        self.left = 10
        self.top = 10
        self.width = 320
        self.height = 200
        self.plotWidget = plotWidget
        self.initUI()
        self.plotWidget.start()

    def addButton(self, title, tooltip, x, y, function):
        button = QPushButton(title, self)
        button.setToolTip(tooltip)
        button.move(x, y)
        button.clicked.connect(function)

    def addDial(self, x, y, function):
        dial = QDial(self)
        dial.move(x, y)
        dial.setRange(0, 250)
        dial.valueChanged[int].connect(function)
        dial.setValue(125)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.addButton('Stop/Run', 'Este boton frena o corre la medicion', 10, 10, self.stop_and_run)
        self.addDial(10, 50, self.change_amplitude)

        self.show()

    @pyqtSlot()
    def stop_and_run(self):
        self.plotWidget.stop_and_run()

    def change_amplitude(self, value):
        self.plotWidget.change_amplitude(value / 100)
        # Lo divido por 100 porque el rango va de 0 a 100

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ButtonPanel(None)
    sys.exit(app.exec_())
