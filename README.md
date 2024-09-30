# wSMA-Cryostat-Selector

Version: 1.0.0

This repository contains the motion controller code for the Galil DMC30000 motion controller in the wSMA Cryostat selector wheel controller box. and Python code for interfacing to the motion controller over TCP using Galil's gclib.

The motion controller is a [Galil DMC3x01x series](http://www.galilmc.com/motion-controllers/single-axis/dmc-3x01x) controller. The program is written in a Basic type language, and the motion controller is programmed via the [Galil Design Kit](http://www.galilmc.com/downloads/software/gdk) software package.

gclib should be installed following the guide at https://www.galil.com/sw/pub/all/doc/global/install/linux/.  The Python interface should then be installed in the in the relevant Python environment using the instructions at https://www.galil.com/sw/pub/all/doc/gclib/html/python.html