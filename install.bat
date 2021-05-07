:: Windows installer

@echo off

:: update embeddable package from https://www.python.org/downloads/windows/
set PythonURL=https://www.python.org/ftp/python/3.9.5/python-3.9.5-embed-amd64.zip
set PythonPathFile=python39._pth

:: update from https://github.com/microsoft/terminal/releases
set WindowsTerminalURL=https://github.com/microsoft/terminal/releases/download/v1.7.1091.0/Microsoft.WindowsTerminal_1.7.1091.0_8wekyb3d8bbwe.msixbundle

:: update from https://pytorch.org/get-started/locally/
set TorchCudaPip=torch==1.8.1+cu111 -f https://download.pytorch.org/whl/torch_stable.html

:: in the future this might become: https://github.com/finetuneanon/transformers/archive/refs/heads/gpt-neo-dungeon-localattention1.zip
set TransformersPip=transformers==2.3.0


echo AIDungeon2 Clover Edition installer for Windows 10 64-bit
echo ----------------------------------------------------------------------------------------------
echo.
echo Using an Nvidia GPU requires 6 GB HDD space, 16 GB RAM, and at least 6 GB of VRAM on your GPU.
echo Using only your CPU requires 2 GB HDD space, 16 GB RAM.
echo Additionally, models require about 6 GB HDD space each, and you will need at least one later.
echo.
:selectcuda
echo 1) Install Nvidia GPU (CUDA) version
echo 2) Install CPU-only version
echo 0) Cancel
set /p usecuda="Enter your choice: "
if %usecuda%==1 (goto install)
if %usecuda%==2 (goto install)
if %usecuda%==0 (exit) else (goto selectcuda)

:install
echo.

:: Create /venv/
echo Creating ./venv/
if not exist "./venv" mkdir venv

cd venv

:: Download Python
echo Downloading Python...
curl "%PythonURL%" -o python.zip

:: Extract Python
echo Extracting Python
tar -xf "python.zip"

:: Get pip
echo Downloading pip...
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
echo Installing pip
python.exe get-pip.py --no-warn-script-location
echo Lib\site-packages>>%PythonPathFile%
echo ..>>%PythonPathFile%

:: Add \venv and \Scripts to path
SET PY="%CD%\python.exe"

:: Delete zip
echo Removing temporary files
del python.zip
del get-pip.py

cd ..

:: Install Prompt_Toolkit
echo Installing Prompt_Toolkit
%PY% -m pip install prompt_toolkit --no-color --no-warn-script-location

:: Install Transformers
echo Installing Transformers
%PY% -m pip install %TransformersPip% --no-color --no-warn-script-location

:: Install Torch
echo Installing PyTorch
if %usecuda%==1 (
  %PY% -m pip install %TorchCudaPip% --no-color --no-warn-script-location
)
if %usecuda%==2 (
  %PY% -m pip install torch --no-color --no-warn-script-location
)

:: Check for and offer to help install Windows Terminal
for %%X in (wt.exe) do (set FOUNDWT=%%~$PATH:X)
if defined FOUNDWT (goto models)
echo.
echo Microsoft Windows Terminal was not found.
echo It is highly recommended you install it.
:selectwt
set /p openwt="Would you like to install Microsoft Windows Terminal now? (y/n) "
if "%openwt%"=="y" (
  curl -L "%WindowsTerminalURL%" -o wt.msixbundle
  start "" /wait /b wt.msixbundle
  pause
  del wt.msixbundle
  goto models
)
if "%openwt%"=="n" (goto models) else (goto selectwt)

:models

echo.
echo You now need to download a model. See README.md for more details and links.
echo When you have a model, just double-click play.bat to play!
pause