@echo off
echo =========================================================
echo   LOS PRICE - Gerando o executavel (.exe)
echo =========================================================
echo.

echo [1/4] Instalando dependencias...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [2/4] Limpando builds antigos...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo.
echo [3/4] Gerando o executavel...
python -m PyInstaller LosPrice.spec --clean --noconfirm

echo.
echo [4/4] Conferindo...
if exist "dist\LosPrice\LosPrice.exe" (
    echo   OK - executavel gerado.
) else (
    echo   ERRO - o executavel nao foi criado. Veja as mensagens acima.
    pause
    exit /b 1
)

echo.
echo =========================================================
echo   PRONTO!
echo.
echo   O programa esta na pasta: dist\LosPrice\
echo   Copie a pasta "LosPrice" inteira para o pendrive ou
echo   para o computador da loja. Nao precisa ter Python la.
echo.
echo   Os dados ficam em:
echo     dist\LosPrice\dados\losprice.db
echo     dist\LosPrice\backups\
echo     dist\LosPrice\relatorios\
echo.
echo   Para atualizar o sistema depois, substitua so os
echo   arquivos do programa e mantenha essas tres pastas.
echo =========================================================
pause
