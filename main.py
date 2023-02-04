# -*- coding: utf-8 -*-

from SoftOscilloscope import SerialPlot
from buttonPanel import ButtonPanel
from PyQt5.QtWidgets import QApplication
import sys

def main():
    port = sys.argv[1]

    app = QApplication(sys.argv)

    plot = SerialPlot(app, port, 230400, n_plots=2, verbose=False, xlim=2000, ylim=100)
    buttonPanel = ButtonPanel(plot)
    plot.set_button_panel(buttonPanel)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
