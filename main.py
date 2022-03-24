# -*- coding: utf-8 -*-

from SoftOscilloscope import SerialPlot
from buttonPanel import ButtonPanel
from PyQt5.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)

    plot = SerialPlot(app, 'COM4', 500000)
    buttonPanel = ButtonPanel(plot)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
