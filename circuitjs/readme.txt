1) download the offline version of circuitj from here:
   https://www.falstad.com/circuit/offline/

2) copy fpga_hw_sim_fwk.html, fpga_hw_sim_fwk.js, sensor.txt and favicon.ico from this folder to:
   circuitjs1/resources/app/war

3) set the following in configuration.py:
   DO_DIS = DO_CIRCUITJS_DIS

4) start the python application and the VHDL simulator

5) now, if you open the .html file directly in your browser that won't work!
   what you need to do is e.g.:
   a) open a console in the path circuitjs1/resources/app/war
   b) type:
      python -m http.server
   c) open your browser and type:
      http://127.0.0.1:8000/fpga_hw_sim_fwk.html
      (you may need to allow execution of javascripts and/or refresh your browser,
      *** use Ctrl + F5 to "force refresh" if required ***)

6) now you see the output voltage from the transformer "Ve" both in the python app and in the VHDL simulator.
   You shall be able to see the behavior in the python app (digital inputs at the left-bottom side) and 
   in your VHDL simulation tool (e.g. in the waveform). In addition, the digital outputs, controlled in VHDL, mirror the digital inputs.
   The frequency of the input voltage of the transformer may be changed with button B0 (again, the event is processed in VHDL and the corresponding frequency is set).
   If you change e.g. the coupling coefficient by hand you will see that the decrease in Ve is detected by the VHDL code and the LED L11 is turned on as a result.

NOTE:
Part of the files in this folder are adpatations from the original source code provided here:
https://github.com/pfalstad/circuitjs1
According to that project the terms of the GNU General Public License have to be considered:
"This program is free software; 
you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation;
either version 2 of the License, or (at your option) any later version."
