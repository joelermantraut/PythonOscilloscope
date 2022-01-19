import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QDial, QMessageBox, QComboBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, Qt

class ButtonPanel(QWidget):

    def __init__(self, plotWidget):
        super().__init__()
        self.title = 'Oscilloscope Tools'
        self.left = 100
        self.top = 100
        self.width = 500
        self.height = 500
        self.offset_amplitude = 50
        self.offset_time = 50
        self.plotWidget = plotWidget
        self.initUI()
        self.plotWidget.start()

    def addButton(self, title, tooltip, x, y, function):
        button = QPushButton(title, self)
        button.setToolTip(tooltip)
        button.move(x, y)
        button.clicked.connect(function)

    def addDial(self, x, y, range_start, range_end, function):
        dial = QDial(self)
        dial.move(x, y)
        dial.setRange(range_start, range_end)
        dial.setValue((range_end - range_start) / 2)
        # Centers dial
        dial.valueChanged[int].connect(function)

    def addComboBox(self, x, y, items, function):
        combo = QComboBox(self)
        combo.move(x, y)
        for item in items:
            combo.addItem(item)
        combo.activated[str].connect(function)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.addButton('Stop/Run', 'Este boton frena o corre la medicion', 10, 10, self.stop_and_run)
        self.addButton('AutoRange', 'Ajusta automaticamente los parametros para la señal de entrada', 100, 10, self.autorange)
        self.addButton('Invertir Y', 'Invierte para todas las graficas el eje Y', 190, 10, self.invert_Y)
        self.addButton('Borrar puntos', 'Borra todos los puntos manuales en la grafica', 280, 10, self.delete_all)
        self.addButton('FFT', 'Aplicar FFT en tiempo real', 370, 10, self.apply_fft)
        # Button Panels
        self.addDial(10, 50, 1, 250, self.change_amplitude)
        self.addDial(100, 50, 1, self.plotWidget.get_samples(), self.change_time)
        # Dials
        self.addComboBox(280, 50, ["Simple", "A+B", "A-B"], self.on_mode_change)

        self.show()

    # Buttons Callbacks

    @pyqtSlot()
    def stop_and_run(self):
        self.plotWidget.stop_and_run()

    @pyqtSlot()
    def autorange(self):
        self.plotWidget.autorange()

    @pyqtSlot()
    def invert_Y(self):
        self.plotWidget.invert_Y()

    @pyqtSlot()
    def delete_all(self):
        self.plotWidget.delete_all()

    @pyqtSlot()
    def apply_fft(self):
        self.plotWidget.apply_fft()

    # Dials Callbacks

    def change_amplitude(self, value):
        self.plotWidget.change_amplitude(value / 100)
        # Lo divido por 100 porque el rango va de 0 a 250 

    def change_time(self, value):
        self.plotWidget.change_time(value)

    # ComboBoxes Callbacks

    def on_mode_change(self, text):
        self.plotWidget.on_mode_change(text)

    # Others Events

    def closeEvent(self, event):
        event.accept()
        self.plotWidget.close()
        # reply = QMessageBox.question(self, '¿Cerrar ventana?', '¿Está seguro que quiere cerrar la ventana?',
        #         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        # if reply == QMessageBox.Yes:
        #     event.accept()
        #     self.plotWidget.close()
        #     print('Oscilloscope Tools closed')
        # else:
        #     event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ButtonPanel(None)
    sys.exit(app.exec_())
