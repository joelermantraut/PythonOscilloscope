import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QDial,
                             QMessageBox, QComboBox, QGroupBox, QVBoxLayout,
                             QGridLayout)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, Qt
import copy

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
        self.callbacks = [
            [self.invert_Y_0, self.toggle_grid_0, self.delete_all_0, self.change_amplitude_0],
            [self.invert_Y_1, self.toggle_grid_1, self.delete_all_1, self.change_amplitude_1]
        ]
        self.init_UI(2)
        self.plotWidget.start()

    def return_value(self, value):
        def returner():
            return value
        return returner

    def addButton(self, title, tooltip, function):
        button = QPushButton(title, self)
        button.setToolTip(tooltip)
        button.clicked.connect(function)

        return button

    def addDial(self, range_start, range_end, function):
        dial = QDial(self)
        dial.setRange(range_start, range_end)
        dial.setValue((range_end - range_start) / 2)
        # Centers dial
        dial.valueChanged[int].connect(function)

        return dial

    def addComboBox(self, items, function):
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

    def init_UI(self, canals_len):
        self.setWindowTitle(self.title)

        components = list()

        components.append(self.addButton('Stop/Run', 'Este boton frena o corre la medicion', self.stop_and_run))
        components.append(self.addButton('AutoRange', 'Ajusta automaticamente los parametros para la señal de entrada', self.autorange))
        components.append(self.addButton('FFT', 'Aplicar FFT en tiempo real', self.apply_fft))
        # Button Panels
        components.append(self.addComboBox(["Simple", "A + B", "A - B", "A * B", "A / B"], self.on_mode_change))
        # ComboBoxes
        components.append(self.addDial(1, self.plotWidget.get_samples(), self.change_time))
        # Dials

        main_group = self.addGroupBox("Controles comunes", components)
        # Controles globales

        canals = list()
        for i in range(canals_len):
            canals.append(self.add_panel(f"Canal {chr(65 + i)}", i))
            # El indice del canal se describe con letras mayusculas
        # Genera los paneles

        grid = QGridLayout()

        grid.addWidget(main_group, 0, 0)
        for canal_index in range(len(canals)):
            grid.addWidget(canals[canal_index], 0, canal_index + 1)
        self.setLayout(grid)
        # Agrega los paneles a la grilla

        self.show()

    def add_panel(self, title, index):
        """
        Se agregan un conjunto de controles (panel) por canal.
        """
        components = list()

        components.append(self.addButton('Invertir Y', 'Invierte para todas las graficas el eje Y', self.callbacks[index][0]))
        components.append(self.addButton('Grilla', 'Muestra u oculta la grilla', self.callbacks[index][1]))
        components.append(self.addButton('Borrar puntos', 'Borra todos los puntos manuales en la grafica', self.callbacks[index][2]))
        # Button Panels
        components.append(self.addDial(1, 250, self.callbacks[index][3]))
        # Dials

        return self.addGroupBox(title, components)

    # Buttons Callbacks

    @pyqtSlot()
    def stop_and_run(self):
        self.plotWidget.stop_and_run()

    @pyqtSlot()
    def autorange(self):
        self.plotWidget.autorange()

    @pyqtSlot()
    def invert_Y_0(self):
        self.plotWidget.invert_Y(0)

    @pyqtSlot()
    def invert_Y_1(self):
        self.plotWidget.invert_Y(1)

    @pyqtSlot()
    def toggle_grid_0(self):
        self.plotWidget.toggle_grid(0)

    @pyqtSlot()
    def toggle_grid_1(self):
        self.plotWidget.toggle_grid(1)

    @pyqtSlot()
    def delete_all_0(self):
        self.plotWidget.delete_all(0)

    @pyqtSlot()
    def delete_all_1(self):
        self.plotWidget.delete_all(1)

    @pyqtSlot()
    def apply_fft(self):
        self.plotWidget.apply_fft()

    # Dials Callbacks

    def change_amplitude_0(self, value):
        self.plotWidget.change_amplitude(0, value / 100)
        # Lo divido por 100 porque el rango va de 0 a 250

    def change_amplitude_1(self, value):
        self.plotWidget.change_amplitude(1, value / 100)
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
