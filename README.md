# wSMA-Cryostat-Selector

Version: 0.2.0

This repository contains the motion controller code for the Galil DMC30000 motion controller in the wSMA Cryostat selector wheel controller box. and Python code for interfacing to the motion controller over TCP Modbus.

The motion controller is a [Galil DMC3x01x series](http://www.galilmc.com/motion-controllers/single-axis/dmc-3x01x) controller. The program is written in a Basic type language, and the motion controller is programmed via the [Galil Design Kit](http://www.galilmc.com/downloads/software/gdk) software package.

The Python code communicates with the controller using the Python PyModbus package.