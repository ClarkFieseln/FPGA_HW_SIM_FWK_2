# FPGA_HW_SIM_FWK_2  

FPGA Hardware Simulation Framework 2.0

  - includes generation of .exe file!
  - includes connection to [circuitjs](https://www.falstad.com/circuit/) over websockets!
  
    (the circuitjs simulation may even be run in a separate computer).
  - links:

    - [video](https://youtu.be/F2Q6Gl9-56A)
    - [old article in Code Project](https://www.codeproject.com/Articles/5329919/FPGA-Hardware-Simulation-Framework-FPGA-HW-SIM-FWK "FPGA_HW_SIM_FWK Article in Code Project")
    - [old project in GitHub](https://github.com/ClarkFieseln/FPGA_HW_SIM_FWK)

## Simulate hardware containing an FPGA programmed in VHDL interactively!

![plot](./img/simulation.png)

## Architecture overview

![plot](./img/architecture_overview.png)

## FPGA GUI

![plot](./img/fpga_gui.png)

## FPGA_HW_SIM_FWK (demo video)

[demo video](https://youtu.be/F2Q6Gl9-56A)

## Dependencies
To install dependencies go to python\hw_sim_fwk_2 and type:

  > pip_install_requirements.bat
  
To install the designer tool type:

  > pip install pygubu-designer
  
## Executable file (approx. 29MB, all included!)
To generate and run an executable file go to python\hw_sim_fwk_2 and type:

  > gen_and_run_exe.bat

This only takes a moment to complete.

## Summary
This tool provides the following features, usually not supported by standard simulation methods:
  - GUI
  - concurrent input / output
  - interactive user experience with emulated HW
  - communication interface between App and VHDL-Simulator based on named pipes (FIFOs)
  - communication interface between App and [circuitjs](https://www.falstad.com/circuit/) based on websockets
  
The stimulus and results exchanged between the Simulation App written in Python and the
VHDL Simulation Tool (any tool supporting VHDL 2008), are fast enough to produce a realistic and interactive HW behavior.
(The rate of data exchanged between Simulation App and circuitjs is also extremely high).

The current project is an improvement of an earlier project which has been optimized for performance,
achieving simulation rates of up to 40kHz! (faster signals will no longer be processed in real-time but the simulation will still be very fast).

In order to support simulation of "asynchronous" signals, the current rate of the simulation clock is reduced to approx. 10kHz. But the overall simulation rate continues to be 40kHz because signals are exchanged in 4 different clock phases within each clock period.
  
