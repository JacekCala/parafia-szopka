@echo off

cd d:\projects\parafia-szopka

rem # echo Directory: %CD%
rem # echo Path: %PATH%

where /q poetry

if ERRORLEVEL 1 (
    rem # echo Using venv
    .venv/Scripts/activate.bat
    python szopka_na_ruch.py
) else (
    rem # echo Using poetry
    poetry run szopka_na_ruch.py
)
