from PyQt5.QtWidgets import (QWidget, QPushButton, QDial,
                             QComboBox, QGroupBox, QVBoxLayout,
                             QGridLayout, QLabel, QLineEdit, QSlider)
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import pyqtSlot, Qt
import numpy as np
from math import sqrt

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
        self.dials_labels = []
        self.visible = True
        self.memory_mode = False
        self.plotWidget.set_button_panel(self)
        self.AMP_RANGES, self.AMP_BAND, self.AMP_TEXTS = self.plotWidget.get_amp_ranges()
        self.TIME_RANGES, self.TIME_BAND, self.TIME_TEXTS = self.plotWidget.get_time_ranges()
        self.init_UI(2)
        self.plotWidget.start()

    def return_value(self, value):
        def returner():
            return value
        return returner

    def addLabel(self, title, color=None):
        label = QLabel(self)
        label.setText(title)
        label.setAlignment(Qt.AlignCenter)

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
        dial.setValue(range_end)
        # Centers dial
        dial.valueChanged[int].connect(lambda: function(dial))

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

    def addLineEdit(self, callback):
        textbox = QLineEdit(self)
        textbox.setAlignment(Qt.AlignCenter)
        textbox.setValidator(QIntValidator(0, 999, self))
        textbox.returnPressed.connect(callback)
        return textbox

    def addSlider(self, min, max, callback):
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min)
        slider.setMaximum(max)
        slider.setValue(min)
        slider.setTickInterval(100)
        slider.valueChanged.connect(callback)

        return slider

    def init_UI(self, canals_len):
        self.setWindowTitle(self.title)

        components = list()

        components.append(self.addButton('Stop/Run', 'Este boton frena o corre la medicion', self.stop_and_run))
        components.append(self.addButton('AutoRange', 'Ajusta automaticamente los parametros para la señal de entrada', self.autorange))
        components.append(self.addButton('FFT', 'Aplicar FFT en tiempo real', self.apply_fft))
        # Button Panels
        components.append(self.addComboBox(["Simple", "A + B", "A - B", "A * B", "A / B"], self.on_mode_change))
        # ComboBoxes
        components.append(self.addDial(self.TIME_RANGES[0], self.TIME_RANGES[-1], self.change_time)) # De 10us a 10000us (o 10ms)
        # Dials
        self.dials_labels.append(self.addLabel(self.TIME_TEXTS[-1]))
        components.append(self.dials_labels[-1])

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
        # Canales

        label_tension = self.addLabel("Vpico\nVpp\nVrms")
        grid.addWidget(label_tension, 1, 0)
        label_frecuencia = self.addLabel("Frecuencia")
        grid.addWidget(label_frecuencia, 2, 0)

        label_tension.setStyleSheet("border-top: 1px solid black;padding: .25em 0")
        label_frecuencia.setStyleSheet("border-top: 1px solid black;padding: .25em 0")

        self.indicador_tension_canal_A = self.addLabel("0V")
        self.indicador_tension_canal_B = self.addLabel("0V")
        self.indicador_frecuencia_canal_A = self.addLabel("0Hz")
        self.indicador_frecuencia_canal_B = self.addLabel("0Hz")

        grid.addWidget(self.indicador_tension_canal_A, 1, 1)
        grid.addWidget(self.indicador_tension_canal_B, 1, 2)
        grid.addWidget(self.indicador_frecuencia_canal_A, 2, 1)
        grid.addWidget(self.indicador_frecuencia_canal_B, 2, 2)

        self.indicador_tension_canal_A.setStyleSheet("border-top: 1px solid black;padding: .25em 0")
        self.indicador_tension_canal_B.setStyleSheet("border-top: 1px solid black;padding: .25em 0")
        self.indicador_frecuencia_canal_A.setStyleSheet("border-top: 1px solid black;padding: .25em 0")
        self.indicador_frecuencia_canal_B.setStyleSheet("border-top: 1px solid black;padding: .25em 0")
        # Indicadores de frecuencia y tension
        
        grid.addWidget(self.addLabel('Modo memoria'), 3, 0)
        self.max_time_line_edit = self.addLineEdit(self.change_max_time_line_edit)
        grid.addWidget(self.max_time_line_edit, 5, 0)
        self.init_memory_mode_btn = self.addButton('Comenzar', 'Este boton comienza con el modo memoria', self.start_memory_mode)
        grid.addWidget(self.init_memory_mode_btn, 5, 1)
        # Modo memoria

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
        components.append(self.addDial(self.AMP_RANGES[0], self.AMP_RANGES[-1], self.callbacks[index][3]))
        # TODO: Cambiar los limites a valores de 0 a 100 porcentual respecto a los limites de entrada
        # Dials
        self.dials_labels.append(self.addLabel(self.AMP_TEXTS[-1]))
        components.append(self.dials_labels[-1])
        # Agrego el componente a una lista para modificarlo despues
        
        points_list_label = self.addLabel('Lista de puntos')
        points_list_label.setStyleSheet("border-top: 1px solid black;padding: .25em 0")
        components.append(points_list_label)

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

    @pyqtSlot()
    def start_memory_mode(self):
        time = self.max_time_line_edit.text()

        if len(time) == 0:
            return

        time = int(time)

        self.memory_mode = not self.memory_mode

        if self.memory_mode:
            self.init_memory_mode_btn.setStyleSheet("background-color: green; color: white")
        else:
            self.init_memory_mode_btn.setStyleSheet("background-color: lightgrey")

        self.plotWidget.start_memory_mode(self.memory_mode, time)

    @pyqtSlot()
    def change_max_time_line_edit(self):
        self.start_memory_mode()
        # Se dispara cuando se presiona ENTER en el LineEdit

    @pyqtSlot()
    def slider_change_value(self):
        value = int(np.log(self.trigger_slider.value()))
        self.plotWidget.change_trigger_freq(value)

    # Dials Callbacks

    def constrain_value(self, value, ranges):
        for index in range(len(ranges) - 1):
            mid_value = (ranges[index + 1] - ranges[index]) / 2 + ranges[index]
            if value >= ranges[index] and value <= mid_value:
                value = ranges[index]
                break
            elif value > mid_value and value < ranges[index + 1]:
                value = ranges[index + 1]
                break

        return value

    def change_time(self, dial):
        value = dial.value()
        value = self.constrain_value(value, self.TIME_RANGES)

        dial.setValue(value)
        # Esta instruccion junto con constrain_value permiten que el
        # dial tenga un comportamiento discreto

        self.dials_labels[0].setText(str(self.TIME_TEXTS[self.TIME_RANGES.index(value)]))
        self.plotWidget.change_time(value)

    def change_amplitude_0(self, dial):
        value = dial.value()
        value = self.constrain_value(value, self.AMP_RANGES)

        dial.setValue(value)
        # Esta instruccion junto con constrain_value permiten que el
        # dial tenga un comportamiento discreto

        self.dials_labels[1].setText(str(self.AMP_TEXTS[self.AMP_RANGES.index(value)]))
        self.plotWidget.change_amplitude(0, value)

    def change_amplitude_1(self, dial):
        value = dial.value()
        value = self.constrain_value(value, self.AMP_RANGES)

        dial.setValue(value)
        # Esta instruccion junto con constrain_value permiten que el
        # dial tenga un comportamiento discreto

        self.dials_labels[2].setText(str(self.AMP_TEXTS[self.AMP_RANGES.index(value)]))
        self.plotWidget.change_amplitude(1, value)
        
    def update_peaks(self, peaks_lists):
        vp0 = round(peaks_lists[0], 2)
        vpp0 = round(vp0 * 2, 2)
        vrms0 = round(vp0 / sqrt(2), 2)

        vp1 = round(peaks_lists[1], 2)
        vpp1 = round(vp1 * 2, 2)
        vrms1 = round(vp1 / sqrt(2), 2)

        self.indicador_tension_canal_A.setText(str(vp0) + " Vp\n" + str(vpp0) + " Vpp\n" + str(vrms0) + " Vrms")
        self.indicador_tension_canal_B.setText(str(vp1) + " Vp\n" + str(vpp1) + " Vpp\n" + str(vrms1) + " Vrms")

    def update_freqs(self, freqs_lists):
        freqs_lists[0] = abs(round(freqs_lists[0] * 10000, 2))
        freqs_lists[1] = abs(round(freqs_lists[1] * 10000, 2))
        # Se multiplica por 10000 por el calculo da en 1/10 MHz
        self.indicador_frecuencia_canal_A.setText(str(freqs_lists[0]) + " Hz")
        self.indicador_frecuencia_canal_B.setText(str(freqs_lists[1]) + " Hz")

    # ComboBoxes Callbacks

    def on_mode_change(self, text):
        self.plotWidget.on_mode_change(text)

    # Others Events

    def disable_memory_mode(self):
        self.memory_mode = False
        self.init_memory_mode_btn.setStyleSheet("background-color: lightgrey")

    def closeEvent(self, event):
        event.accept()
        self.plotWidget._close()