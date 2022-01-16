import serial, socket, sys
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import signal

class BasePlot(object):
    def __init__(self, stream, **kwargs):
        self.stream = stream
        self.kwargs = kwargs

        try:
            self.app = QtGui.QApplication([])
        except RuntimeError:
            self.app = QtGui.QApplication.instance()

        self.layout = pg.GraphicsWindow()
        self.layout.showMaximized()
        self.layout.setWindowTitle('Software Oscilloscope')
        self.layout.closeEvent = self.handle_close_event
        self.plot_list = list()
        self.scatter_plot_list = list()

        self.timer = None
        self.samples = 500
        self.inverted = False

    def _translate_range(self, value, in_min, in_max, out_min, out_max):
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def get_samples(self):
        return self.samples

    def set_options(self, plot, **kwargs):
        options = kwargs.keys()

        if "xlim" in options:
            self.change_amplitude(kwargs["xlim"])
        else:
            self.change_amplitude(1.25)

        if "ylim" in options:
            self.change_time(kwargs["ylim"])
        else:
            self.change_time(1.25)

        if "setMouseEnabled" in options:
            plot.setMouseEnabled(True, True)

        if "hideButtons" in options:
            plot.hideButtons()

        if "setMenuEnabled" in options:
            plot.setMenuEnabled()

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

    def read_stream(self):
        stream_data = self.stream.readline().decode('utf-8').rstrip().split(',')

        return stream_data

    def change_amplitude(self, band):
        for plot in self.plot_list:
            plot.setYRange(-band / 2, band / 2)

    def change_time(self, band):
        for plot in self.plot_list:
            plot.setXRange(0, band)

    def autorange(self):
        for plot in self.plot_list:
            plot.autoRange()

    def invert_Y(self):
        self.inverted = not self.inverted

        for plot in self.plot_list:
            plot.invertY(self.inverted)

    def on_mode_change(self, text):
        if text == "Simple":
            pass
        elif text == "A+B":
            pass
        elif text == "A-B":
            pass
        else:
            pass

    def show_grid(self):
        for plot in plot_list:
            plot.showGrid(True, True)

    def mouse_clicked(self, event):
        point = event.pos()
        plot = self.plot_list[0]

        x_range = plot.getAxis('bottom').range
        y_range = plot.getAxis('left').range
        widget_width = plot.getAxis('bottom').size().width()
        widget_height = plot.getAxis('left').size().height()
        new_x = self._translate_range(point.x(), 0, widget_width, x_range[0], x_range[1])
        new_y = self._translate_range(point.y(), widget_height, 0, y_range[0], y_range[1])

        scatterplot = pg.ScatterPlotItem([new_x], [new_y], symbol='+', color = 'b')
        self.scatter_plot_list.append(scatterplot)
        plot.addItem(scatterplot)

    def delete_all(self):
        for plot in self.plot_list:
            for item in self.scatter_plot_list:
                plot.removeItem(item)

    def plot_init(self):
        trial_data = self.read_stream()

        for i in range(len(trial_data)):
            new_plot = self.layout.addPlot()
            new_plot.plot(np.zeros(self.samples))
            new_plot.scene().sigMouseClicked.connect(self.mouse_clicked)
            self.set_options(
                new_plot,
                **self.kwargs,
                setMouseEnabled=True,
                setMenuEnabled=True,
                hideButtons=True
            )
            self.plot_list.append(new_plot)
            self.layout.nextRow()

    def update(self):
        stream_data = self.read_stream()

        for data, line in zip(stream_data, self.plot_list):
            line = line.listDataItems()[0]

            yData = line.yData
            yData[-1] = data

            line.informViewBoundsChanged()
            line.setData(
                x=np.arange(len(line.yData)),
                y=np.roll(yData, -1),
                xClean=None,
                yClean=None,
                xDisp=None,
                yDisp=None
            )
            line.updateItems()
            line.sigPlotChanged.emit(line)

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

    def close(self):
        self.handle_close_event()

    def handle_close_event(self, event=None):
        self.timer.stop()
        self.close_stream()
        self.app.exit()

class SerialPlot(BasePlot):
    def __init__(self, com_port, baud_rate, **kwargs):
        self.serial_port = serial.Serial()
        self.serial_port.baudrate = baud_rate
        self.serial_port.port = com_port
        super(SerialPlot, self).__init__(self.serial_port, **kwargs)
