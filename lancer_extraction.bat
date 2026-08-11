@echo off
chcp 65001 > nul
title Extraction Ashera Chronologie

echo ==========================================
echo    Lancement de l'extraction Discord
echo ==========================================
echo.

python extract_du_serveur.py

echo.
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] L'extraction s'est terminee avec une erreur.
) else (
    echo [SUCCES] Extraction terminee avec succes !
)

echo.
pause
