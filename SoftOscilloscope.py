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

        self.view = pg.GraphicsView()
        self.layout = pg.GraphicsLayout(border=(100,100,100))
        self.view.closeEvent = self.handle_close_event
        self.layout.closeEvent = self.handle_close_event
        self.view.setCentralItem(self.layout)
        self.view.show()
        self.view.setWindowTitle('Software Oscilloscope')
        self.view.showMaximized()
        self.plot_list = []

        self.timer = None

    def set_options(self, plot, kwargs):
        if "xlim" in kwargs.keys():
            self.change_amplitude(kwargs["xlim"])
        else:
            self.change_amplitude(1.25)

        if "ylim" in kwargs.keys():
            self.change_time(kwargs["ylim"])
        else:
            self.change_time(1.25)

    def open_stream(self):
        print("Opening Stream")
        self.stream.open()

    def close_stream(self):
        if hasattr(self.stream, 'flushInput'):
            self.stream.flushInput()
        if hasattr(self.stream, 'flushOutput'):
            self.stream.flushOutput()
        self.stream.close()
        print("Stream closed")

    def read_stream(self):
        try:
            stream_data = self.stream.readline().rstrip().split(',')
        except TypeError:
            stream_data = self.stream.readline().decode('utf-8').rstrip().split(',')

        return stream_data

    def change_amplitude(self, band):
        for plot in self.plot_list:
            plot.setYRange(-band / 2, band / 2)

    def change_time(self, band):
        for plot in self.plot_list:
            plot.setXRange(0, band)

    def plot_init(self):
        for i in range(20):
            trial_data = self.read_stream()

        for i in range(len(trial_data)):
            new_plot = self.layout.addPlot()
            new_plot.plot(np.zeros(250))
            self.set_options(new_plot, self.kwargs)
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
        self.timer.start(0)

        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            self.app.exec_()

    def stop_and_run(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.stream.flushInput() # Descarto todo el contenido acumulado
            self.timer.start()

    def handle_close_event(self, event):
        self.close_stream()
        self.app.exit()

class SerialPlot(BasePlot):
    def __init__(self, com_port, baud_rate, **kwargs):
        self.serial_port = serial.Serial()
        self.serial_port.baudrate = baud_rate
        self.serial_port.port = com_port
        super(SerialPlot, self).__init__(self.serial_port, **kwargs)

class SocketClientPlot(BasePlot):
    def __init__(self, address, port, **kwargs):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_params = (address, port)
        self.socket.connect((address, port))
        self.stream = self.socket.makefile()
        super(SocketClientPlot, self).__init__(self.stream, **kwargs)

    def open_stream(self):
        pass

    def close_stream(self):
        self.socket.close()
        self.stream.close()

class GenericPlot(BasePlot):
    def __init__(self, stream, **kwargs):
        if hasattr(stream, 'open') \
        and hasattr(stream, 'close') \
        and hasattr(stream, 'readline'):
            super(GenericPlot, self).__init__(stream, **kwargs)
        else:
            raise BadAttributeError("One of the open/close/readline attributes is missing")
