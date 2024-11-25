@echo off

:: Make sure to run this script with Administrator privileges if needed.
:: Save this file as install_mmlab.bat and execute by double-clicking or from the command prompt.

echo Installing Python dependencies from requirements.txt...
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to install requirements.txt
    exit /b 1
)

echo Installing mmlab packages...
:: Update openmim and install mmengine
pip install --no-cache-dir -U openmim
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to install openmim
    exit /b 1
)

mim install mmengine
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to install mmengine
    exit /b 1
)

:: Install specific versions of mmlab components
mim install "mmcv==2.0.1"
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to install mmcv==2.0.1
    exit /b 1
)

mim install "mmdet==3.1.0"
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to install mmdet==3.1.0
    exit /b 1
)

mim install "mmpose==1.1.0"
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to install mmpose==1.1.0
    exit /b 1
)

:: Execute setupmodel.py if it exists
if exist "setupmodel.py" (
    echo Running setupmodel.py...
    python setupmodel.py
    IF %ERRORLEVEL% NEQ 0 (
        echo Failed to run setupmodel.py
        exit /b 1
    )
) else (
    echo setupmodel.py not found, skipping this step.
)

echo Installation completed successfully!
pause
