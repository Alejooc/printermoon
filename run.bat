@echo off
echo Iniciando el ejecutable...
start "" "dist\printermoon.exe"
if errorlevel 1 (
    echo Hubo un error al intentar iniciar el ejecutable.
) else (
    echo Ejecutable lanzado.
)