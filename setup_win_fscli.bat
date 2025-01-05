@echo off
set SCRIPT_DIR=%~dp0
echo Creating fscli batch script...
echo @echo off > "%SCRIPT_DIR%fscli.bat"
echo python "%SCRIPT_DIR%fscli.py" %%* >> "%SCRIPT_DIR%fscli.bat"
setlocal enabledelayedexpansion
set "PATH_LINE=set PATH=%%PATH%%;%SCRIPT_DIR%"
for /f "tokens=*" %%i in ('type "%SCRIPT_DIR%fscli.bat"') do (
    if "%%i"=="!PATH_LINE!" (
        set PATH_EXISTS=true
    )
)

if not defined PATH_EXISTS (
    echo Adding %SCRIPT_DIR% to PATH...
    setx PATH "%PATH%;%SCRIPT_DIR%"
) else (
    echo %SCRIPT_DIR% is already in PATH.
)

echo Setup complete. You can now use 'fscli' command.
