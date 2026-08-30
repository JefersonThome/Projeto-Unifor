@echo off
chcp 65001 > nul
title ENADE Analytics
cd /d "%~dp0"

echo ================================================
echo        ENADE 2023 - INICIANDO PROJETO
echo ================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao foi encontrado.
    echo.
    echo Instale o Python e marque a opcao:
    echo "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    python -m venv .venv

    if errorlevel 1 (
        echo.
        echo ERRO: Nao foi possivel criar o ambiente virtual.
        pause
        exit /b 1
    )
)

echo Instalando ou verificando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel instalar as dependencias.
    echo Verifique sua conexao com a internet.
    pause
    exit /b 1
)

if not exist "data\enade.duckdb" (
    echo.
    echo Banco de dados nao encontrado.
    echo Executando o pipeline pela primeira vez...
    echo Esse processo pode demorar alguns minutos.
    echo.

    ".venv\Scripts\python.exe" -m src.pipeline

    if errorlevel 1 (
        echo.
        echo ERRO: O pipeline nao foi concluido.
        echo.
        echo Verifique se o arquivo abaixo esta presente:
        echo source_data\microdados_enade_2023.zip
        echo.
        pause
        exit /b 1
    )
) else (
    echo.
    echo Banco de dados encontrado.
    echo Nao sera necessario processar os microdados novamente.
)

echo.
echo ================================================
echo Dashboard disponivel em:
echo http://localhost:8501
echo ================================================
echo.
echo Nao feche esta janela enquanto estiver utilizando.
echo Para encerrar, pressione CTRL + C.
echo.

".venv\Scripts\python.exe" -m streamlit run dashboard\app.py

pause