Wiring for Encoder turn counter reset
-------------------------------------

We connect the Galil digital output DO1 - pin 29 to the VegaCNC P3-9 pin, in order 
to supply +5 to 25V to reset the turn counter.

The connections required are:
Galil J5 P33 Gnd --> VegaCNC P3-4 DC Ground Out
Galil J5 P29 DO1 --> VegaCNC P3-9 SSI Preset [sic]
Galil J5 P15 OPB (GND/PWR) --> Galil J5 P16 AGND
Galil J5 P43 OPA (PWR/GND) --> Galil J5 P18 +12V

