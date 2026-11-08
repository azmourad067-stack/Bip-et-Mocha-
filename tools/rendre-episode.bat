@echo off
chcp 65001 >nul
rem ============================================================================
rem  Bip & Mocha - rend un episode en video MP4 (1080x1920, avec le son).
rem  Double-cliquer sur ce fichier, puis taper le numero de l'episode (ex. 06).
rem  Ou dans un terminal :  tools\rendre-episode.bat 06
rem  Guide complet : docs\10-rendu-sur-pc.md
rem ============================================================================
setlocal

rem --- 1. Trouver Blender (modifier la ligne suivante si Blender est ailleurs)
set "BLENDER="
for /d %%B in ("%ProgramFiles%\Blender Foundation\Blender*") do set "BLENDER=%%B\blender.exe"
if not defined BLENDER for %%B in (blender.exe) do set "BLENDER=%%~$PATH:B"
if not defined BLENDER (
  echo Blender introuvable. Ouvrir ce fichier avec le Bloc-notes et indiquer le chemin
  echo de blender.exe a la ligne  set "BLENDER=..."
  pause & exit /b 1
)

rem --- 2. Quel episode ?
cd /d "%~dp0.."
set "NUM=%~1"
if "%NUM%"=="" set /p NUM=Numero de l'episode a rendre (ex. 06) : 
rem   accepte 1, 01 ou " 6 " : espaces retires, zero ajoute devant un seul chiffre
if defined NUM set "NUM=%NUM: =%"
if defined NUM if "%NUM:~1%"=="" set "NUM=0%NUM%"
set "EP="
for /d %%D in ("episodes\%NUM%-*") do set "EP=%%D"
if not defined EP (
  echo Episode %NUM% introuvable dans le dossier episodes.
  pause & exit /b 1
)
if not exist "%EP%\animatique.py" (
  echo L'episode %NUM% n'a pas encore de script d'animation.
  pause & exit /b 1
)

rem --- 3. Rendu : scene animee + son + video MP4
echo.
echo Rendu de %EP% avec "%BLENDER%"
echo (comptez 1 a 2 heures avec une carte graphique ; laissez le PC branche)
echo.
"%BLENDER%" -b --python "%EP%\animatique.py" --python "tools\blender\rendre-video.py" -a
echo.
echo Termine : %EP%\rendu\episode-%NUM%.mp4
pause
