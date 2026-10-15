@echo off
REM ====================================================================
REM  Mise a jour de l'onglet BEAMFORGE pour BeamCutSoft - double-cliquer
REM  Telecharge la derniere version depuis GitHub et la copie dans
REM  My Commands\beamforge. Garde config.ini (vos reglages).
REM  Ne touche a aucun fichier de Beamcut Soft.
REM ====================================================================
setlocal
set "CIBLE=C:\Users\Public\Documents\BeamCut\BeamCutSoft\My Commands\beamforge"
set "URL=https://github.com/Nc1fusion/beamforge-addon/archive/refs/heads/main.zip"
set "TMPD=%TEMP%\beamforge_maj"

echo.
echo  Mise a jour de l'onglet BEAMFORGE
echo  ---------------------------------
echo  Fermez BeamCutSoft avant de continuer.
echo.
pause

if exist "%TMPD%" rmdir /s /q "%TMPD%"
mkdir "%TMPD%"

echo  Telechargement...
curl -L -s -f -o "%TMPD%\addon.zip" "%URL%"
if errorlevel 1 (
  powershell -NoProfile -Command "Invoke-WebRequest -UseBasicParsing -Uri '%URL%' -OutFile '%TMPD%\addon.zip'"
)
if not exist "%TMPD%\addon.zip" goto echec

echo  Decompression...
tar -xf "%TMPD%\addon.zip" -C "%TMPD%"
if not exist "%TMPD%\beamforge-addon-main\beamforge\__init__.py" (
  powershell -NoProfile -Command "Expand-Archive -Force -Path '%TMPD%\addon.zip' -DestinationPath '%TMPD%'"
)
if not exist "%TMPD%\beamforge-addon-main\beamforge\__init__.py" goto echec

echo  Copie dans My Commands\beamforge...
if not exist "%CIBLE%" mkdir "%CIBLE%"
robocopy "%TMPD%\beamforge-addon-main\beamforge" "%CIBLE%" /E /XF config.ini journal.txt /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto echec
if not exist "%CIBLE%\config.ini" copy /y "%TMPD%\beamforge-addon-main\beamforge\config.ini" "%CIBLE%\config.ini" >nul

echo.
set /p V=<"%CIBLE%\VERSION.txt"
echo  OK : beamforge version %V% installee.
echo  Vous pouvez rouvrir BeamCutSoft.
echo.
rmdir /s /q "%TMPD%" 2>nul
pause
exit /b 0

:echec
echo.
echo  *** ECHEC de la mise a jour : prenez cet ecran en photo. ***
echo  (Rien n'a ete modifie si l'echec est survenu avant la copie.)
echo.
pause
exit /b 1
