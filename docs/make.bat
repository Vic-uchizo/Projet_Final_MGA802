@ECHO OFF

REM make.bat - equivalent Windows du Makefile pour la documentation Sphinx.
REM Usage : depuis le dossier docs\, lancer « make html » puis ouvrir
REM         _build\html\index.html dans un navigateur.

pushd %~dp0

REM On utilise « python » s'il est dispo, sinon on bascule sur « py » (lanceur Windows).
if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=python -m sphinx
)
set SOURCEDIR=.
set BUILDDIR=_build

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo La commande "python" est introuvable. Verifie que Python est installe
	echo et ajoute au PATH, ou utilise "py -m sphinx" a la place.
	echo Pense aussi a installer Sphinx :  pip install -e ".[docs]"
	exit /b 1
)

if "%1" == "" goto help
if "%1" == "help" goto help
if "%1" == "clean" goto clean

REM Construction HTML (et tout autre format passe en argument : html, latex, ...)
%SPHINXBUILD% -b %1 "%SOURCEDIR%" "%BUILDDIR%\%1"
echo.
echo Documentation generee : %BUILDDIR%\%1\index.html
goto end

:clean
if exist "%BUILDDIR%" rmdir /S /Q "%BUILDDIR%"
echo Dossier %BUILDDIR% supprime.
goto end

:help
echo make html   - construit la documentation HTML dans _build\html
echo make clean  - supprime le dossier _build
goto end

:end
popd
