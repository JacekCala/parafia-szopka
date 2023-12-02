%echo on

cd d:\projects\parafia-szopka

echo Directory: %CD%
echo Path: %PATH%

where /q poetry

if ERRORLEVEL 1 (
    echo Using venv
    .venv/Scripts/activate.bat
    python szopka_na_ruch.py
) else (
    echo Using poetry
    poetry run szopka_na_ruch.py
)

echo Done.
