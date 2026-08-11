@echo off
echo ========================================
echo Ejecutando parametrizacion.py...
echo ========================================
python parametrizacion.py
if %errorlevel% neq 0 exit /b %errorlevel%
echo.

echo ========================================
echo Ejecutando laminacion100.py...
echo ========================================
python laminacion100.py
if %errorlevel% neq 0 exit /b %errorlevel%
echo.

echo ========================================
echo Ejecutando laminacion10000.py...
echo ========================================
python laminacion10000.py
if %errorlevel% neq 0 exit /b %errorlevel%
echo.

echo ========================================
echo Todas las simulaciones han finalizado con exito.
echo ========================================
pause
