# -*- coding: utf-8 -*-

from SoftOscilloscope import SerialPlot

def main():
    plot = SerialPlot('COM4', 9600, xlim=(0, 120), ylim=(0.2, 0.5))
    plot.start()

if __name__ == "__main__":
    main()
