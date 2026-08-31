@echo off

set L=
set /p L="Ingrese la longitud del vertedero en metros [L, default 55]: "
if "%L%"=="" set L=55

echo ========================================
echo Ejecutando parametrizacion.py...
echo ========================================
python parametrizacion.py %L%
if %errorlevel% neq 0 exit /b %errorlevel%
echo.

echo ========================================
echo Ejecutando laminacion100.py...
echo ========================================
python laminacion100.py %L%
if %errorlevel% neq 0 exit /b %errorlevel%
echo.

echo ========================================
echo Ejecutando laminacion10000.py...
echo ========================================
python laminacion10000.py %L%
if %errorlevel% neq 0 exit /b %errorlevel%
echo.

echo ========================================
echo Ejecutando laminacion100_lleno.py...
echo ========================================
python laminacion100_lleno.py %L%
if %errorlevel% neq 0 exit /b %errorlevel%
echo.

echo ========================================
echo Ejecutando laminacion10000_vaciamiento.py...
echo ========================================
python laminacion10000_vaciamiento.py %L%
if %errorlevel% neq 0 exit /b %errorlevel%
echo.

echo ========================================
echo Todas las simulaciones han finalizado con exito.
echo ========================================
pause
