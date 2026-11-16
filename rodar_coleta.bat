@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Atlas Agrario e Politico - coleta de dados
echo.
echo  ==========================================================
echo   Atlas Agrario e Politico do Brasil - coleta de dados
echo   Pode deixar esta janela aberta. Leva de 1 a 3 horas.
echo  ==========================================================
echo.

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (where python >nul 2>nul && set "PY=python")
if not defined PY (
  echo Python nao encontrado. Instale o Python e rode este arquivo de novo.
  echo ERRO_PYTHON> coleta_status.txt
  pause
  exit /b 1
)

if not exist .venv (
  echo [1/4] Criando ambiente Python...
  %PY% -m venv .venv || (echo ERRO_VENV> coleta_status.txt & pause & exit /b 1)
)
call .venv\Scripts\activate.bat

echo [2/4] Instalando pacotes...
python --version > instalacao_log.txt 2>&1
python -m pip install --upgrade pip >> instalacao_log.txt 2>&1
python -m pip install -r requirements.txt >> instalacao_log.txt 2>&1 || (echo ERRO_PIP> coleta_status.txt & echo Erro na instalacao. Veja instalacao_log.txt & pause & exit /b 1)
python -m pip freeze >> instalacao_log.txt 2>&1

echo [3/4] Testando...
python -m pytest -q -p no:cacheprovider > testes_log.txt 2>&1
if errorlevel 1 (
  type testes_log.txt
  echo ERRO_TESTES> coleta_status.txt
  pause
  exit /b 1
)

echo [4/4] Coletando dados do IBGE...
python -m pipeline
echo.
echo  Terminou. Pode fechar esta janela.
pause
