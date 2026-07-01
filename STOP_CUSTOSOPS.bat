@echo off
set ROOT=%~dp0
powershell.exe -ExecutionPolicy Bypass -File "%ROOT%scripts\stop-custosops.ps1"