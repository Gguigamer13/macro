@echo off
setlocal enabledelayedexpansion
title Auto Clicker - criar o executavel
cd /d "%~dp0"

echo.
echo  ==========================================================
echo     AUTO CLICKER  -  criar o .exe e instalar
echo     powered by nova era
echo  ==========================================================
echo.

REM ---------------------------------------------------------------
REM  1. procurar o Python
REM ---------------------------------------------------------------
set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    where python >nul 2>nul
    if not errorlevel 1 set "PY=python"
)
if not defined PY goto sem_python
echo  [1/4] Python encontrado.

REM ---------------------------------------------------------------
REM  2. PyInstaller (e quem transforma o programa em .exe)
REM ---------------------------------------------------------------
echo  [2/4] Preparando o PyInstaller. So demora na primeira vez...
%PY% -m pip install --upgrade --disable-pip-version-check --quiet pyinstaller
if errorlevel 1 goto sem_pyinstaller

REM ---------------------------------------------------------------
REM  3. icone
REM ---------------------------------------------------------------
echo  [3/4] Desenhando o icone...
set EXTRA=
%PY% "ferramentas\gerar_icone.py" "icone.ico" >nul
if errorlevel 1 (
    echo        [aviso] nao consegui gerar o icone; o .exe vai sair sem ele.
) else (
    REM caminho completo: o PyInstaller resolve caminhos relativos a partir
    REM da pasta do arquivo .spec, e nao da pasta onde o .bat esta rodando
    set EXTRA=--icon "%~dp0icone.ico" --add-data "%~dp0icone.ico;."
)

REM ---------------------------------------------------------------
REM  4. gerar o executavel
REM ---------------------------------------------------------------
echo  [4/4] Gerando o executavel. Isso leva de 1 a 3 minutos...
echo.
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name AutoClicker !EXTRA! --distpath "dist" --workpath "build\pyinstaller" --specpath "build" "%~dp0auto_clicker.py"
if errorlevel 1 goto falhou_build
if not exist "dist\AutoClicker.exe" goto falhou_build

echo.
echo  ==========================================================
echo     Pronto! O executavel esta em:
echo     %cd%\dist\AutoClicker.exe
echo  ==========================================================
echo.

REM ---------------------------------------------------------------
REM  5. instalar no disco escolhido
REM ---------------------------------------------------------------
echo  Discos disponiveis neste computador:
echo.
call :listar_discos
echo.

:perguntar_disco
set "LETRA="
set /p LETRA=  Letra do disco onde instalar (ENTER = C, ou N para nao instalar): 
if not defined LETRA set "LETRA=C"
if /i "!LETRA!"=="N" goto sem_instalar
set "LETRA=!LETRA:~0,1!"
if not exist "!LETRA!:\" (
    echo  [erro] Nao encontrei o disco !LETRA!: neste computador. Tente de novo.
    echo.
    goto perguntar_disco
)

set "PASTA="
set /p PASTA=  Nome da pasta [Auto Clicker]: 
if not defined PASTA set "PASTA=Auto Clicker"
set "DESTINO=!LETRA!:\!PASTA!"

if not exist "!DESTINO!" md "!DESTINO!" 2>nul
if not exist "!DESTINO!" goto sem_permissao
copy /y "dist\AutoClicker.exe" "!DESTINO!\" >nul
if errorlevel 1 goto sem_permissao
copy /y "README.md" "!DESTINO!\" >nul 2>nul

set "ATALHO="
set /p ATALHO=  Criar um atalho na area de trabalho? (S/N) [S]: 
if not defined ATALHO set "ATALHO=S"
if /i "!ATALHO!"=="S" call :criar_atalho "!DESTINO!"

echo.
echo  ==========================================================
echo     Instalado em: !DESTINO!
echo     E so dar dois cliques em AutoClicker.exe
echo  ==========================================================
echo.
echo  Observacao: como o .exe foi criado agora, no seu computador,
echo  o antivirus ou o Windows SmartScreen pode perguntar se confia
echo  no arquivo na primeira vez. E so escolher "mais informacoes"
echo  e depois "executar assim mesmo".
echo.
start "" explorer "!DESTINO!"
pause
exit /b 0

REM ---------------------------------------------------------------
REM  rotinas auxiliares
REM ---------------------------------------------------------------
:listar_discos
powershell -NoProfile -Command "Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 -or $_.DriveType -eq 2 } | ForEach-Object { '    {0}  {1,-18} {2,7:N1} GB livres de {3,6:N1} GB' -f $_.DeviceID, $_.VolumeName, ($_.FreeSpace/1GB), ($_.Size/1GB) }" 2>nul
if not errorlevel 1 exit /b 0
for %%d in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do if exist %%d:\ echo     %%d:
exit /b 0

:criar_atalho
powershell -NoProfile -Command "$atalho = (New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Auto Clicker.lnk'); $atalho.TargetPath = '%~1\AutoClicker.exe'; $atalho.WorkingDirectory = '%~1'; $atalho.IconLocation = '%~1\AutoClicker.exe,0'; $atalho.Description = 'Auto Clicker - powered by nova era'; $atalho.Save()" >nul 2>nul
if errorlevel 1 (
    echo  [aviso] nao consegui criar o atalho na area de trabalho.
) else (
    echo  Atalho criado na area de trabalho.
)
exit /b 0

REM ---------------------------------------------------------------
REM  mensagens de erro
REM ---------------------------------------------------------------
:sem_python
echo  [ERRO] Nao encontrei o Python neste computador.
echo.
echo  Instale o Python 3.10 ou mais novo em:
echo     https://www.python.org/downloads/windows/
echo  Durante a instalacao marque a opcao "Add Python to PATH".
echo.
pause
exit /b 1

:sem_pyinstaller
echo.
echo  [ERRO] Nao consegui instalar o PyInstaller.
echo  Verifique se o computador esta conectado a internet e tente de novo.
echo.
pause
exit /b 1

:falhou_build
echo.
echo  [ERRO] A criacao do executavel falhou. As mensagens acima dizem o motivo.
echo  Dica: feche o AutoClicker.exe se ele estiver aberto e rode de novo.
echo.
pause
exit /b 1

:sem_permissao
echo.
echo  [ERRO] Nao consegui gravar em !DESTINO!
echo  Escolha outra pasta ou clique com o botao direito neste arquivo
echo  e use "Executar como administrador".
echo.
pause
exit /b 1

:sem_instalar
echo.
echo  Tudo bem - o executavel continua em %cd%\dist\AutoClicker.exe
echo  Voce pode copiar esse arquivo para onde quiser, em qualquer disco.
echo.
pause
exit /b 0
