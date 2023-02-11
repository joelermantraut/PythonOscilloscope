import serial, sys
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import numpy as np
import numpy.fft as fft

class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return values

class BasePlot(object):
    def __init__(self, app, stream, n_plots, **kwargs):
        pg.setConfigOptions(antialias=True)
        self.app = app
        self.stream = stream
        self.kwargs = kwargs
        self.n_plots = n_plots

        self.scatter_plot_list = list()
        self.plots = dict()

        self.ENCODING = "utf-8"
        self.SPLIT_CHAR = ","
        self.SAVE_RESPONSE = 20
        self.NOISE_BAND = 0.1
        self.SIMPLE = 0
        self.A_PLUS_B = 1
        self.A_MINUS_B = 2
        self.A_X_B = 3
        self.A_DIV_B = 4
        self.IN_MIN = 0
        self.IN_MAX = 4095
        self.OUT_MIN = -3.5
        self.OUT_MAX = 3.5
        self.SAMPLES = 7001
        self.AMP_RANGES = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        self.TIME_RANGES = [10, 1000, 2000, 5000, 6000, 7000]
        self.AMP_BAND = [0.05, 0.1, 0.2, 0.5, 1, 1.5, 2, 3, 4, 5, 6]
        self.TIME_BAND = [3360, 1344, 670, 334, 133, 65]
        self.AMP_TEXTS = ["10mV", "20mV", "100mV", "100mV", "200mV", "200mV", "1V", "1V", "1V", "1V", "2V"]
        self.TIME_TEXTS = ["50ms", "20ms", "10ms", "5ms", "2ms", "1ms"]
        self.CURVE_WIDTH_SENSIBILITY = 5
        self.MAX_POINTS_IN_LIST = 1024

        self.timer = None # Para parar el muestreo
        self.inverted = False
        self.pointsSize = 7
        self.fft_mode = False
        self.grid = False
        self.last_name = ""
        self.point_color_index = -1 # -1 para que el conteo arranque en 0
        self.limit_scatter_points = 10
        self.mode = self.SIMPLE
        self.tolerance = 0.1
        self.buttonPanel = None
        self.verbose = False
        self.memory_mode = False
        self.memory_mode_time = 0
        self.channel_data = list()
        self.xlim = 0
        self.points = [np.zeros(self.MAX_POINTS_IN_LIST)] * self.n_plots
        self.points_pointer = 0
        self.running = True

        self.initUI()

    def initUI(self):
        self.layout = pg.GraphicsLayoutWidget()
        self.layout.showMaximized()
        self.layout.setWindowTitle('Software Oscilloscope')
        self.layout.closeEvent = self._close

    def addControlsButton(self):
        proxy_controls_btn = QtWidgets.QGraphicsProxyWidget()

        button = QtWidgets.QPushButton('Mostrar/Ocultar Controles')
        button.setCheckable(True)
        button.toggle() # Para que inicie pulsado
        button.clicked.connect(self._toggle_controls)

        proxy_controls_btn.setWidget(button)

        proxy_close_btn = QtWidgets.QGraphicsProxyWidget()

        button = QtWidgets.QPushButton('Cerrar Aplicación')
        button.setCheckable(True)
        button.clicked.connect(self._close)

        proxy_close_btn.setWidget(button)

        self.layout.addItem(proxy_controls_btn, row=len(self.plots) + 1, col=0)
        self.layout.addItem(proxy_close_btn, row=len(self.plots) + 1, col=1)

    def _toggle_controls(self):
        self.buttonPanel.change_visibility()

    def _range_compare(self, value1, value2, tol=None):
        """
        Devuelve True si los dos valores pasados como parametros
        estan dentro de la tolerancia definida.
        """
        if tol == None:
            tol = self.tolerance

        if abs(value1 - value2) > tol:
            return False
        else:
            return True

    def set_button_panel(self, buttonPanel):
        """
        Define la propiedad del panel de botones para poder
        acceder a esta interfaz generada por fuera de la clase.
        """
        self.buttonPanel = buttonPanel

    def get_samples(self):
        """
        Devuelve el parametro "samples".
        """
        return self.SAMPLES

    def get_amp_ranges(self):
        return self.AMP_RANGES, self.AMP_BAND, self.AMP_TEXTS
    
    def get_time_ranges(self):
        return self.TIME_RANGES, self.TIME_BAND, self.TIME_TEXTS

    def _set_options(self, plot, **kwargs):
        """
        Configura un conjunto de opciones, algunas definidas
        por defecto, otras recibidas como un parametro en la
        instanciación de la clase.
        """
        options = kwargs.keys()

        if "xlim" in options:
            self.xlim = kwargs["xlim"]
            self.change_time(10) # Escala minima
        else:
            plot.enableAutoRange(axis="x")
        # Recibe un valor y setea los limites en el eje X (tiempo)

        if "ylim" in options:
            self.change_amplitude(list(self.plots.values()).index(plot), kwargs["ylim"])
        else:
            plot.enableAutoRange(axis="y")
        # Recibe una tupla con el limite inferior y superior

        if "setMouseEnabled" in options:
            plot.setMouseEnabled(kwargs["setMouseEnabled"][0], kwargs["setMouseEnabled"][1])

        if "hideButtons" in options:
            plot.hideButtons()

        if "setMenuEnabled" in options:
            plot.setMenuEnabled()

        if "showGrid" in options:
            self.toggle_grid(list(self.plots.values()).index(plot))

        if "curveClickable" in options:
            plotDataItems = plot.listDataItems()[0]
            plotDataItems.setCurveClickable(True, self.CURVE_WIDTH_SENSIBILITY)
            plotDataItems.sigClicked.connect(self._curve_clicked)

        if "verbose" in options:
            self.verbose = kwargs["verbose"]

    def _open_stream(self):
        """
        Abre la comunicacion serie.
        """
        print("Opening Stream")
        self.stream.open()

    def _close_stream(self):
        """
        Cierra la comunicacion serie.
        """
        try:
            if hasattr(self.stream, 'flushInput'):
                self.stream.flushInput()
            if hasattr(self.stream, 'flushOutput'):
                self.stream.flushOutput()
        except serial.serialutil.PortNotOpenError as e:
            print(e)

        self.stream.close()
        print("Stream closed")

    def add_array(self, point):
        for i in range(self.n_plots):
            self.points[i][self.points_pointer] = point[i]

        self.points_pointer = (self.points_pointer + 1) % self.MAX_POINTS_IN_LIST

        peaks_list = list()
        freqs_list = list()
        for i in range(self.n_plots):
            peaks_list.append(self.points[i].max())

            spectrum = fft.fft(self.points[i])
            freq = fft.fftfreq(len(spectrum))
            threshold = 0.5 * max(abs(spectrum))
            mask = abs(spectrum) > threshold
            freqs_list.extend(freq[mask])

        self.buttonPanel.update_peaks(peaks_list)
        self.buttonPanel.update_freqs(freqs_list)

    def _translate(self, data, in_min, in_max, out_min, out_max):
        """
        Los valores recibidos son enteros de entre 0 y 4096, que corresponden
        a mediciones de entre 0 y 2.9V, por lo cual, debo convertirlos.
        """
        for index, value in enumerate(data):
            data[index] = round((int(value) - in_min) * (out_max - out_min) / (in_max - in_min) + out_min, 2)

        return data

    def _validate(self, data):
        """
        Valida el dato recibido. Este metodo se aplica
        porque a mucha velocidad, a veces algunos datos se
        puede perder o corromper.

        De paso, convierte los valores de cadenas a enteros.
        """
        for index, item in enumerate(data):
            try:
                data[index] = int(item)
            except:
                return ""

        return data

    def _read_stream(self):
        """
        Lee desde la comunicacion serie.
        """

        stream_data = self.stream.read(100) # Para leer todos los que esten en el buffer

        if not self.running:
            return

        stream_data_divided = [stream_data[i:i + 2] for i in range(0, len(stream_data), 2)]

        for stream_data in stream_data_divided:
            stream_data = int.from_bytes(stream_data, byteorder='little')

            self.channel_data.append(stream_data)

            if len(self.channel_data) < self.n_plots:
                continue

            stream_data = self.channel_data
            self.channel_data = list()

            # stream_data = self._validate(stream_data)
            stream_data = self._translate(stream_data, self.IN_MIN, self.IN_MAX, self.OUT_MIN, self.OUT_MAX)

            self.add_array(stream_data)

            if self.verbose:
                print(stream_data)

            self._update(stream_data)

    def _write_stream(self, text):
        """
        Escribe sobre la comunicacion serie.
        """
        self.stream.write(text)

    def change_amplitude(self, index, band):
        """
        Cambia la escala Y, para la grafica seleccionada.
        """
        band = self.AMP_BAND[self.AMP_RANGES.index(band)]

        plot = list(self.plots.values())[index]
        plot.setYRange(-band, band)

    def change_time(self, band):
        """
        Cambia la escala X, para todas las graficas.
        """
        band = self.TIME_BAND[self.TIME_RANGES.index(band)]

        for plot in self.plots.values():
            plot.setXRange(self.xlim - band, self.xlim)

    def autorange(self):
        """
        Determina automaticamente las escalas de los ejes, según
        la grafica utilizada.
        """
        for plot in self.plots.values():
            plot.autoRange()

    def invert_Y(self, index):
        """
        Invierte el eje de la grafica seleccionada.
        """
        self.inverted = not self.inverted

        plot = list(self.plots.values())[index]
        plot.invertY(self.inverted)

    def change_trigger_freq(self, value):
        self.timer.setInterval(value)

    def on_mode_change(self, text):
        """
        Permite cambiar el modo empleado. Los modos disponibles
        son:

        "Simple": Modo basica, muestra cada curva segun los puntos
        son recibidos.
        "A + B": Suma las dos primeras graficas.
        "A - B": Resta las dos primeras graficas.
        "A * B": Multiplica las dos primera graficas.
        "A / B": Divide las dos primeras graficas.
        """
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
        """
        Alterna la visibilidad de la grilla.
        """
        self.grid = not self.grid

        plot = list(self.plots.values())[index]
        plot.showGrid(self.grid, self.grid)

    def delete_all(self, index):
        """
        Elimina todos los puntos de la grafica.
        """
        plot = list(self.plots.values())[index]
        for item in self.scatter_plot_list[index]:
            plot.removeItem(item)

    def apply_fft(self):
        """
        Aplica FFT desde la funcion de la misma grafica.
        """
        self.fft_mode = not self.fft_mode

        for plot in self.plots.values():
            curve = plot.listDataItems()[0]
            curve.setFftMode(self.fft_mode)

            if self.fft_mode:
                plot.showAxes((True, False, False, True), showValues=(True, False, False, True))
            else:
                plot.showAxes((True, False, False, True), showValues=(True, False, False, False))
            # Agrega o quita los numeros de los ejes

    def _get_plot_info(self, plot):
        """
        Devuelve informacion basica de una de las graficas.
        """
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

    def _verify_point_click(self, plot, plot_index, x, y):
        """
        Verifica que el punto de la curva clickeado este dentro de
        la tolerancia establecida.
        """
        for point in self.scatter_plot_list[plot_index]:
            coords = point.getData()
            point_x = coords[0][0]
            point_y = coords[1][0]

            if self._range_compare(x, point_x) and self._range_compare(y, point_y):
                plot.removeItem(point)

                return True

        return False

    def _on_plot_click(self, event):
        """
        Funcion invocada cuando una grafica es clickeada, no requiere
        que sea haga click sobre la curva.
        """
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
        plot_dict = self._get_plot_info(plot)
        # Obtiene informacion de la grafica clickeada

        if self._verify_point_click(plot, plot_index, new_x, new_y):
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

        self.buttonPanel.addPoint(plot_index, new_x, new_y, self.point_color_index)

    def _curve_clicked(self, event):
        """
        Funcion invocada cuando un elemento ScatterPlotItem es clickeado.
        """
        name = event.name()
        self.last_name = name

    def _plot_init(self):
        """
        Invocada al inicio de la ejecucion, genera la cantidad
        de graficas necesarias, con sus correspondientes propiedades.
        """
        for i in range(self.SAVE_RESPONSE):
            _ = self._read_stream()
        # Descarta una cierta cantidad de muestras
        # para asegurar que los primeros datos no 
        # influyan en la lectura

        for i in range(self.n_plots):
            self.plots[f"plot_{i}"] = self.layout.addPlot(row=i+1, col=0)

            new_plot = self.plots[f"plot_{i}"]
            new_plot.plot(np.zeros(self.SAMPLES), name=f"plot_{i}")
            new_plot.scene().sigMouseClicked.connect(self._on_plot_click)
            new_plot.setLabel("bottom", "Tiempo")
            new_plot.setLabel("left", "Tensión")
            new_plot.showAxes((True, False, False, True), showValues=(True, False, False, False))
            self._set_options(
                new_plot,
                **self.kwargs,
                setMouseEnabled=(False, True),
                setMenuEnabled=True,
                hideButtons=True,
                curveClickable=True,
                showGrid=True
            )
            self.layout.nextRow()
            self.scatter_plot_list.append(list())

    def _update_widget(self, plot, data):
        """
        Actualiza directamente los puntos sobre la grafica.
        """
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

    def _update(self, stream_data):
        """
        Funcion invocada en cada actualizacion de la grafica. Toma en cuenta
        el modo en el que esta funcionando.
        """
        if self.memory_mode:
            # Reviso si los valores recibidos estan dentro del margen de ruido
            if float(stream_data[0]) < 0 and float(stream_data[0]) < -self.NOISE_BAND or \
                float(stream_data[0]) > 0 and float(stream_data[0]) > self.NOISE_BAND:
                self.timer_memory_mode = QtCore.QTimer()
                self.timer_memory_mode.timeout.connect(self.disable_memory_mode)
                self.timer_memory_mode.start(self.memory_mode_time)
                self.memory_mode = False
            else:
                return

        if self.mode == self.SIMPLE:
            for data, plot in zip(stream_data, self.plots.values()):
                self._update_widget(plot, data)

        elif self.mode == self.A_PLUS_B:
            if self.n_plots > 1:
                self._update_widget(
                    list(self.plots.values())[0],
                    str(float(stream_data[0]) + float(stream_data[1]))
                )

        elif self.mode == self.A_MINUS_B:
            if self.n_plots > 1:
                self._update_widget(
                    list(self.plots.values())[0],
                    str(float(stream_data[0]) - float(stream_data[1]))
                )

        elif self.mode == self.A_X_B:
            if self.n_plots > 1:
                self._update_widget(
                    list(self.plots.values())[0],
                    str(float(stream_data[0]) * float(stream_data[1]))
                )

        elif self.mode == self.A_DIV_B:
            if self.n_plots > 1:
                self._update_widget(
                    list(self.plots.values())[0],
                    str(float(stream_data[0]) / float(stream_data[1]))
                )

        else:
            print("Fail on ComboBox")

    def start(self):
        """
        Funcion que inicia la adquisicion de datos.
        """
        self._open_stream()
        self._plot_init()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._read_stream)
        self.timer.start(1)

        self.addControlsButton()

        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            self.app.exec_()

    def stop_and_run(self):
        """
        Funcion que frena o reiniciar la adquisicion de datos.
        """
        self.running = not self.running
        # if self.timer.isActive():
        #     self.timer.stop()
        # else:
        #     self.stream.flushInput() # Descarto todo el contenido acumulado
        #     self.timer.start()
        
    def start_memory_mode(self, mode, time):
        """
        Funcion que inicia el modo de memoria que permite capturar
        transitorios en la entrada.

        La logica aplicada, es que los valores de ruido se descartan, hasta que ingresa
        un valor que aparenta ser una señal. Entonces se mide hasta que finaliza el tiempo
        determinado por "time".
        """
        self.memory_mode = mode
        self.memory_mode_time = time

    def disable_memory_mode(self):
        self.timer.stop()
        self.timer_memory_mode.stop()
        self.buttonPanel.disable_memory_mode()

    def _close(self, event=None):
        """
        Invocado al cerrar la interfaz.
        """
        self.timer.stop()
        self._close_stream()
        self.app.exit()

class SerialPlot(BasePlot):
    def __init__(self, app, com_port, baud_rate, n_plots, **kwargs):
        self.serial_port = serial.Serial()
        self.serial_port.baudrate = baud_rate
        self.serial_port.port = com_port
        self.serial_port.bytesize = serial.EIGHTBITS
        self.serial_port.parity = serial.PARITY_EVEN
        self.serial_port.stopbits = serial.STOPBITS_ONE
        super(SerialPlot, self).__init__(app, self.serial_port, n_plots, **kwargs)
