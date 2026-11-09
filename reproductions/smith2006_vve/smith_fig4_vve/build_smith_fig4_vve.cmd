@echo off
setlocal
cd /d "C:\Users\xczhang\Desktop\papers\tools\vlab\L-studio-ATE-4.4.1-2976-VVe64\L-studio-ATE-4.4.1-2976-VVe64\bin"
call vvevars.bat
cd /d "%~dp0"
mingw32-make SHELL=cmd
endlocal
