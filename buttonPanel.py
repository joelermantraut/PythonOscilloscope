import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QDial,
                             QMessageBox, QComboBox, QGroupBox, QVBoxLayout,
                             QGridLayout)
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
        self.init_UI()
        self.plotWidget.start()

    def addButton(self, title, tooltip, x, y, function):
        button = QPushButton(title, self)
        button.setToolTip(tooltip)
        button.clicked.connect(function)

        return button

    def addDial(self, x, y, range_start, range_end, function):
        dial = QDial(self)
        dial.setRange(range_start, range_end)
        dial.setValue((range_end - range_start) / 2)
        # Centers dial
        dial.valueChanged[int].connect(function)

        return dial

    def addComboBox(self, x, y, items, function):
        combo = QComboBox(self)
        for item in items:
            combo.addItem(item)
        combo.activated[str].connect(function)

        return combo

    def addGroupBox(self, title, objects_list):
        groupBox = QGroupBox(title)
        vbox = QVBoxLayout()

        for element in objects_list:
            vbox.addWidget(element)

        groupBox.setLayout(vbox)

        return groupBox

    def init_UI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        components = list()

        components.append(self.addButton('Stop/Run', 'Este boton frena o corre la medicion', 10, 10, self.stop_and_run))
        components.append(self.addButton('AutoRange', 'Ajusta automaticamente los parametros para la señal de entrada', 100, 10, self.autorange))
        # Button Panels
        components.append(self.addComboBox(280, 50, ["Simple", "A+B", "A-B"], self.on_mode_change))
        # ComboBoxes
        components.append(self.addDial(100, 50, 1, self.plotWidget.get_samples(), self.change_time))
        # Dials

        main_group = self.addGroupBox("Controles comunes", components)

        # Controles globales

        group2 = self.add_panel("Canal A")

        grid = QGridLayout()
        grid.addWidget(main_group, 0, 0)
        grid.addWidget(group2, 0, 1)
        self.setLayout(grid)

        self.show()

    def add_panel(self, title):
        """
        Se agregan un conjunto de controles (panel) por canal.
        """
        components = list()
        components.append(self.addButton('Invertir Y', 'Invierte para todas las graficas el eje Y', 190, 10, self.invert_Y))
        components.append(self.addButton('Grilla', 'Muestra u oculta la grilla', 280, 10, self.toggle_grid))
        components.append(self.addButton('Borrar puntos', 'Borra todos los puntos manuales en la grafica', 370, 10, self.delete_all))
        components.append(self.addButton('FFT', 'Aplicar FFT en tiempo real', 460, 10, self.apply_fft))
        # Button Panels
        components.append(self.addDial(10, 50, 1, 250, self.change_amplitude))
        # Dials

        return self.addGroupBox(title, [invert_button, grid_button, delete_button, fft_button, amp_dial])

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
    def toggle_grid(self):
        self.plotWidget.toggle_grid()

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
