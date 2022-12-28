import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QDial,
                             QMessageBox, QComboBox, QGroupBox, QVBoxLayout,
                             QGridLayout, QLabel)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5 import QtCore

class ButtonPanel(QWidget):

    def __init__(self, plotWidget):
        super().__init__()
        self.title = 'Oscilloscope Tools'
        self.offset_amplitude = 50
        self.offset_time = 50
        self.plotWidget = plotWidget
        self.callbacks = [
            [self.invert_Y_0, self.toggle_grid_0, self.delete_all_0, self.change_amplitude_0],
            [self.invert_Y_1, self.toggle_grid_1, self.delete_all_1, self.change_amplitude_1]
        ]
        self.colors = [
            "255,0,0",
            "255,170,0",
            "170,255,0",
            "0,255,0",
            "0,255,170",
            "0,170,255",
            "0,0,255",
            "170,0,255",
            "255,0,170",
            "255,0,0",
        ]
        self.vbox_panels = list()
        self.labels = [[], []]
        self.visible = True
        self.plotWidget.set_button_panel(self)
        self.init_UI(2)
        self.plotWidget.start()

    def return_value(self, value):
        def returner():
            return value
        return returner

    def addLabel(self, title, color=None):
        label = QLabel(self)
        label.setText(title)

        if color != None:
            label.setStyleSheet(f"background-color: rgb({self.colors[color]})")

        return label

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

        return groupBox, vbox

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

        main_group, _ = self.addGroupBox("Controles comunes", components)
        # Controles globales

        self.canals = list()
        for i in range(canals_len):
            self.canals.append(self.add_panel(f"Canal {chr(65 + i)}", i))
            # El indice del canal se describe con letras mayusculas
        # Genera los paneles

        grid = QGridLayout()

        grid.addWidget(main_group, 0, 0)
        for canal_index in range(len(self.canals)):
            grid.addWidget(self.canals[canal_index], 0, canal_index + 1)
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
        components.append(self.addLabel('Lista de puntos'))

        groupBox, vbox = self.addGroupBox(title, components)

        self.vbox_panels.append(vbox)

        return groupBox

    def addPoint(self, plot_index, x, y, color):
        """
        Agrega un punto a la lista de puntos, mostrando el punto
        y el color utilizando en el indicador sobre la grafica
        """
        self.labels[plot_index].append(self.addLabel(f"x: {round(x, 2)}, y: {round(y, 2)}", color))

        self.vbox_panels[plot_index].addWidget(self.labels[plot_index][-1])

    def is_visible(self):
        return self.visible

    def change_visibility(self):
        if self.visible:
            self.hide()
        else:
            self.show()

        self.visible = not(self.visible)

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
        for label_index in range(len(self.labels[0])):
            label = self.labels[0][label_index]
            label.setParent(None)

        self.labels[0] = []
            
    @pyqtSlot()
    def delete_all_1(self):
        self.plotWidget.delete_all(1)
        for label_index in range(len(self.labels[1])):
            label = self.labels[1][label_index]
            label.setParent(None)

        self.labels[1] = []

    @pyqtSlot()
    def apply_fft(self):
        self.plotWidget.apply_fft()

    # Dials Callbacks

    def change_amplitude_0(self, value):
        self.plotWidget.change_amplitude(0, (-value / 50, value / 50))
        # Lo divido por 100 porque el rango va de 0 a 250

    def change_amplitude_1(self, value):
        self.plotWidget.change_amplitude(1, (-value / 50, value / 50))
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
