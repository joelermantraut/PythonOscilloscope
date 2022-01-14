# -*- coding: utf-8 -*-

from SoftOscilloscope import SerialPlot
from buttonPanel import ButtonPanel

def main():
    plot = SerialPlot('COM4', 9600, ylim=.2)
    plot.start()

    # buttonPanel = ButtonPanel(plot)

if __name__ == "__main__":
    main()
