@echo off
REM create environment:
REM -------------------
REM cd one level above the project folder, then type:
REM python -m venv fpga_hw_sim_fwk_2_env
REM then execute this script which is assumed to be in fpga_hw_sim_fwk_2\python\hw_sim_fwk_2
REM -------------------
@echo about to create and run the executable file /dist/fpga_hw_sim_fwk_2.exe,
@echo the python environment is assumed to be 3 folder levels above
@echo (please adapt script otherwise!)
pause
REM ----------------------------------------------------------------------------------------------
REM cd <project_path>
REM (NOTE: you may need to enter the user profile path explicitely)
call ..\..\..\fpga_hw_sim_fwk_2_env\Scripts\activate.bat
REM (NOTE: you may need to get out of environment path e.g. if you have it open in a separate console)
..\..\..\fpga_hw_sim_fwk_2_env\Scripts\pip install --upgrade pip
REM ..\..\..\fpga_hw_sim_fwk_2_env\Scripts\pip install pipreqs
REM ..\..\..\fpga_hw_sim_fwk_2_env\Scripts\pip list
REM #############################################################################################
REM we comment the following line for now until we find out why we get autobahn_rce i.o. autobahn
REM and why it cannot be installed (we do NOT update requirements.txt for now):
REM ..\..\..\fpga_hw_sim_fwk_2_env\Scripts\python updateRequirements.py
REM #############################################################################################
REM not working with --user: ..\..\..\fpga_hw_sim_fwk_2_env\Scripts\pip install --user -r requirements.txt
..\..\..\fpga_hw_sim_fwk_2_env\Scripts\pip install -r requirements.txt
REM you may need to install pyinstaller
REM ..\..\..\fpga_hw_sim_fwk_2_env\Scripts\pip install pyinstaller
..\..\..\fpga_hw_sim_fwk_2_env\Scripts\pip install pyinstaller
..\..\..\fpga_hw_sim_fwk_2_env\Scripts\pyinstaller main_windows.spec
cd dist
.\fpga_hw_sim_fwk_2.exe
