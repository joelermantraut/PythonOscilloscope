# -*- coding: utf-8 -*-

from SoftOscilloscope import SerialPlot
from buttonPanel import ButtonPanel
from PyQt5.QtWidgets import QApplication
import sys
import serial.tools.list_ports

def get_device_port():
    available_ports = [
        p.device
        for p in serial.tools.list_ports.comports()
        if 'CH340' in p.description  # may need tweaking to match new arduinos
    ]
    if not available_ports:
        raise IOError("No available port found")
    if len(available_ports) > 1:
        raise IOError("Multiple available ports found")
    
    return available_ports[0]

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else get_device_port()

    app = QApplication(sys.argv)

    plot = SerialPlot(app, port, 230400, n_plots=2, verbose=False, xlim=7001, ylim=100)
    buttonPanel = ButtonPanel(plot)
    plot.set_button_panel(buttonPanel)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
