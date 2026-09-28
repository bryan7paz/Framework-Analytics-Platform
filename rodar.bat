@echo off
cd /d "%~dp0"

rem Sobe o PostgreSQL se estiver parado (cluster local padrao)
set PGCTL=
if exist "C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe" set PGCTL=C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe
if exist "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" set PGCTL=C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe
if not "%PGCTL%"=="" if exist "%USERPROFILE%\pgdata\PG_VERSION" (
    "%PGCTL%" -D "%USERPROFILE%\pgdata" status >nul 2>&1
    if errorlevel 1 (
        echo Subindo o PostgreSQL...
        "%PGCTL%" -D "%USERPROFILE%\pgdata" -l pg_startup.log start
    )
)

if not exist "fap_env\Scripts\python.exe" (
    echo Ambiente nao encontrado - rode primeiro: python setup.py
    pause
    exit /b 1
)

echo Iniciando a FAP em http://127.0.0.1:5000 ...
"fap_env\Scripts\python.exe" src\app.py
