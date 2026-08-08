@echo off
setlocal EnableDelayedExpansion

rem ===========================================================
rem   LOS PRICE - Atualiza uma instalacao existente
rem
rem   Gera o executavel novo e substitui SO os arquivos do
rem   programa na pasta instalada. As pastas de dados nunca
rem   sao tocadas:
rem
rem       dados\        banco de dados
rem       backups\      copias do banco
rem       relatorios\   PDFs e planilhas gerados
rem
rem   Uso:
rem       atualizar.bat                    (usa %USERPROFILE%\LosPrice)
rem       atualizar.bat "D:\LosPrice"      (outra pasta)
rem ===========================================================

echo =========================================================
echo   LOS PRICE - Atualizando a instalacao
echo =========================================================
echo.

rem ---- destino ----------------------------------------------
set "DESTINO=%~1"
if "%DESTINO%"=="" set "DESTINO=%USERPROFILE%\LosPrice"
if "%DESTINO:~-1%"=="\" set "DESTINO=%DESTINO:~0,-1%"

echo   Instalacao: %DESTINO%
echo.

rem So atualiza o que ja e uma instalacao do LosPrice. Isso evita
rem apagar a pasta errada por engano no passo do robocopy.
if not exist "%DESTINO%\LosPrice.exe" (
    echo   ERRO: nao encontrei LosPrice.exe em:
    echo         %DESTINO%
    echo.
    echo   Essa pasta nao parece ser uma instalacao do LosPrice.
    echo   Para instalar do zero, rode build.bat e copie a pasta
    echo   dist\LosPrice para onde quiser.
    echo.
    pause
    exit /b 1
)

rem ---- 1. build ----------------------------------------------
echo [1/4] Gerando o executavel novo...
echo.
call python -m PyInstaller LosPrice.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo   ERRO: o PyInstaller falhou. Nada foi alterado na instalacao.
    pause
    exit /b 1
)

if not exist "dist\LosPrice\LosPrice.exe" (
    echo.
    echo   ERRO: o executavel nao foi gerado. Nada foi alterado.
    pause
    exit /b 1
)

rem ---- 2. backup do banco ------------------------------------
echo.
echo [2/4] Guardando uma copia do banco antes de mexer...

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set "CARIMBO=%%i"

if exist "%DESTINO%\dados\losprice.db" (
    if not exist "%DESTINO%\backups" mkdir "%DESTINO%\backups"
    copy /y "%DESTINO%\dados\losprice.db" "%DESTINO%\backups\antes_da_atualizacao_!CARIMBO!.db" >nul
    echo   OK - backups\antes_da_atualizacao_!CARIMBO!.db
) else (
    echo   Nenhum banco encontrado ainda. Seguindo.
)

rem ---- 3. substitui o programa -------------------------------
echo.
echo [3/4] Substituindo os arquivos do programa...

robocopy "dist\LosPrice\_internal" "%DESTINO%\_internal" /MIR /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 (
    echo   ERRO ao copiar _internal. A instalacao pode estar incompleta:
    echo   rode este arquivo de novo.
    pause
    exit /b 1
)

copy /y "dist\LosPrice\LosPrice.exe" "%DESTINO%\LosPrice.exe" >nul
if errorlevel 1 (
    echo   ERRO ao copiar LosPrice.exe. Feche o programa e tente de novo.
    pause
    exit /b 1
)

echo   OK - LosPrice.exe e _internal atualizados

rem ---- 4. confere --------------------------------------------
echo.
echo [4/4] Conferindo...

if exist "%DESTINO%\dados\losprice.db" (
    echo   OK - banco preservado em dados\losprice.db
) else (
    echo   AVISO - nao ha banco em dados\. O programa vai criar um novo.
)

echo.
echo =========================================================
echo   ATUALIZADO
echo.
echo   Programa : %DESTINO%\LosPrice.exe
echo   Seus dados continuam em dados\, backups\ e relatorios\.
echo.
echo   Se o programa estiver aberto, feche e abra de novo.
echo =========================================================
pause
