@echo off
setlocal
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dev.ps1" %*
set "_exit=%errorlevel%"
endlocal & exit /b %_exit%