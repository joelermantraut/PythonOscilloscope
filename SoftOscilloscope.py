import serial, socket, sys
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np

class BasePlot(object):
    def __init__(self, app, stream, **kwargs):
        self.app = app
        self.stream = stream
        self.kwargs = kwargs

        self.layout = pg.GraphicsLayoutWidget()
        self.layout.showMaximized()
        self.layout.setWindowTitle('Software Oscilloscope')
        self.layout.closeEvent = self.close
        self.scatter_plot_list = list()
        self.plots = dict()

        self.SAVE_RESPONSE = 20
        self.SIMPLE = 0
        self.A_PLUS_B = 1
        self.A_MINUS_B = 2
        self.A_X_B = 3
        self.A_DIV_B = 4

        self.timer = None # Para parar el muestreo
        self.samples = 500
        self.inverted = False
        self.pointsSize = 7
        self.curve_width_sensibility = 10
        self.fft_mode = False
        self.grid = False
        self.last_name = ""
        self.point_color_index = 0
        self.limit_scatter_points = 10
        self.mode = self.SIMPLE
        self.tolerance = 1

    def _translate_range(self, value, in_min, in_max, out_min, out_max):
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def _range_compare(self, value1, value2, tol=self.tolerance):
        if abs(value1 - value2) > tol:
            return False
        else:
            return True

    def get_samples(self):
        return self.samples

    def set_options(self, plot, **kwargs):
        options = kwargs.keys()

        # if "xlim" in options:
        #     self.change_amplitude(kwargs["xlim"])
        # else:
        #     self.change_amplitude(1.25)

        # if "ylim" in options:
        #     self.change_time(kwargs["ylim"])
        # else:
        #     self.change_time(1.25)

        if "setMouseEnabled" in options:
            plot.setMouseEnabled(True, True)

        if "hideButtons" in options:
            plot.hideButtons()

        if "setMenuEnabled" in options:
            plot.setMenuEnabled()

        if "showGrid" in options:
            self.toggle_grid(list(self.plots.values()).index(plot))

        if "curveClickable" in options:
            plotDataItems = plot.listDataItems()[0]
            # scatterDataItems = plot.listDataItems()[2]
            plotDataItems.setCurveClickable(True, self.curve_width_sensibility)
            plotDataItems.sigClicked.connect(self.curve_clicked)

    def open_stream(self):
        print("Opening Stream")
        self.stream.open()

    def close_stream(self):
        try:
            if hasattr(self.stream, 'flushInput'):
                self.stream.flushInput()
            if hasattr(self.stream, 'flushOutput'):
                self.stream.flushOutput()
        except serial.serialutil.PortNotOpenError as e:
            print(e)

        self.stream.close()
        print("Stream closed")

    def validate(self, data):
        return data

    def decode(self, data):
        return data

    def read_stream(self):
        stream_data = self.stream.readline().decode('utf-8').rstrip().split(',')
        # TODO: Confirmar la informacion recibida

        stream_data = self.validate(stream_data)
        stream_data = self.decode(stream_data)

        return stream_data

    def write_stream(self, text):
        self.stream.write(text)

    def change_amplitude(self, index, band):
        plot = list(self.plots.values())[index]
        plot.setYRange(-band / 2, band / 2)

    def change_time(self, band):
        for plot in self.plots.values():
            plot.setXRange(0, band)

    def autorange(self):
        for plot in self.plots.values():
            plot.autoRange()

    def invert_Y(self, index):
        self.inverted = not self.inverted

        plot = list(self.plots.values())[index]
        plot.invertY(self.inverted)

    def on_mode_change(self, text):
        if text == "Simple":
            self.mode = self.SIMPLE
        elif text == "A + B":
            self.mode = self.A_PLUS_B
        elif text == "A - B":
            self.mode = self.A_MINUS_B
        elif text == "A * B":
            self.mode = self.A_X_B
        elif text == "A / B":
            self.mode = self.A_DIV_B
        else:
            print("Fallo widget de seleccion de modo")

    def toggle_grid(self, index):
        self.grid = not self.grid

        plot = list(self.plots.values())[index]
        plot.showGrid(self.grid, self.grid)

    def delete_all(self, index):
        plot = list(self.plots.values())[index]
        for item in self.scatter_plot_list[index]:
            plot.removeItem(item)

    def apply_fft(self):
        self.fft_mode = not self.fft_mode

        for plot in self.plots.values():
            curve = plot.listDataItems()[0]
            curve.setFftMode(self.fft_mode)

    def get_plot_info(self, plot):
        geo = plot.viewGeometry()

        bottom = plot.getAxis('bottom')
        left = plot.getAxis('left')

        new_dict = {
            "x": bottom.x(),
            "y": left.y(),
            "width": bottom.size().width(),
            "height": left.size().height(),
            "x_range": bottom.range,
            "y_range": left.range
        }

        return new_dict

    def verify_point_click(self, plot_index, x, y):
        for point in self.scatter_plot_list[plot_index]:
            coords = point.getData()
            point_x = coords[0][0]
            point_y = coords[1][0]

            if x == point_x and y == point_y:
                return True

        return False

    def on_plot_click(self, event):
        if self.last_name == "":
            return
        name = self.last_name
        self.last_name = ""

        point = event.pos()
        new_x = point.x()
        new_y = point.y()
        # Obtiene el punto clickeado

        plot = self.plots[name]
        plot_index = list(self.plots.keys()).index(name)
        plot_dict = self.get_plot_info(plot)
        # Obtiene informacion de la grafica clickeada

        if self.verify_point_click(plot_index, new_x, new_y):
            return

        if len(self.scatter_plot_list[plot_index]) > self.limit_scatter_points:
            return
        # Evita que se sigan agregando puntos si ya hay demasiados

        self.point_color_index = (self.point_color_index + 1) % 10 # Elige un color
        scatterplot = pg.ScatterPlotItem(
            [new_x],
            [new_y],
            symbol='s', # 's' symbol is a square
            brush=pg.intColor(self.point_color_index),
            size=self.pointsSize
        )
        self.scatter_plot_list[plot_index].append(scatterplot)
        plot.addItem(scatterplot)
        # Añade un punto a la grafica

    def curve_clicked(self, event):
        name = event.name()
        self.last_name = name

    def plot_init(self):
        for i in range(self.SAVE_RESPONSE):
            self.read_stream()
        # Descarta una cierta cantidad de muestras
        # para asegurar que los primeros datos no 
        # influyan en la lectura

        trial_data = self.read_stream()

        for i in range(len(trial_data)):
            self.plots[f"plot_{i}"] = self.layout.addPlot()
            new_plot = self.plots[f"plot_{i}"]
            new_plot.plot(np.zeros(self.samples), name=f"plot_{i}")
            new_plot.scene().sigMouseClicked.connect(self.on_plot_click)
            self.set_options(
                new_plot,
                **self.kwargs,
                setMouseEnabled=True,
                setMenuEnabled=True,
                hideButtons=True,
                curveClickable=True,
                showGrid=True
            )
            self.layout.nextRow()
            self.scatter_plot_list.append(list())

    def update_widget(self, plot, data):
        plot = plot.listDataItems()[0]

        yData = plot.yData
        yData[-1] = data

        plot.informViewBoundsChanged()
        plot.setData(
            x=np.arange(len(plot.yData)),
            y=np.roll(yData, -1),
        )
        plot.updateItems()
        plot.sigPlotChanged.emit(plot)

    def update(self):
        stream_data = self.read_stream()

        if self.mode == self.SIMPLE:
            for data, plot in zip(stream_data, self.plots.values()):
                self.update_widget(plot, data)

        elif self.mode == self.A_PLUS_B:
            self.update_widget(
                list(self.plots.values())[0],
                str(float(stream_data[0]) + float(stream_data[1]))
            )

        elif self.mode == self.A_MINUS_B:
            self.update_widget(
                list(self.plots.values())[0],
                str(float(stream_data[0]) - float(stream_data[1]))
            )

        elif self.mode == self.A_X_B:
            self.update_widget(
                list(self.plots.values())[0],
                str(float(stream_data[0]) * float(stream_data[1]))
            )

        elif self.mode == self.A_DIV_B:
            self.update_widget(
                list(self.plots.values())[0],
                str(float(stream_data[0]) / float(stream_data[1]))
            )

        else:
            print("Fail on ComboBox")

    def start(self):
        self.open_stream()
        self.plot_init()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1 / self.samples)

        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            self.app.exec_()

    def stop_and_run(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.stream.flushInput() # Descarto todo el contenido acumulado
            self.timer.start()

    def close(self, event=None):
        self.timer.stop()
        self.close_stream()
        self.app.exit()

class SerialPlot(BasePlot):
    def __init__(self, app, com_port, baud_rate, **kwargs):
        self.serial_port = serial.Serial()
        self.serial_port.baudrate = baud_rate
        self.serial_port.port = com_port
        self.serial_port.bytesize = serial.EIGHTBITS
        self.serial_port.parity = serial.PARITY_EVEN
        self.serial_port.stopbits = serial.STOPBITS_ONE
        super(SerialPlot, self).__init__(app, self.serial_port, **kwargs)
