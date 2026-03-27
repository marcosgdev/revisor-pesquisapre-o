@echo off
REM Script para iniciar a API
REM Execute: iniciar_api.bat

echo ========================================
echo INICIANDO API DO SISTEMA DE SCORING
echo ========================================
echo.

REM Verifica se .env existe
if not exist .env (
    echo ERRO: Arquivo .env nao encontrado!
    echo.
    echo Execute primeiro: configurar.bat
    echo.
    pause
    exit /b 1
)

echo Carregando configuracoes do .env...

REM Carrega variaveis do .env
for /f "tokens=1,2 delims==" %%a in (.env) do (
    set %%a=%%b
)

REM Verifica se chave foi carregada
if "%OPENAI_API_KEY%"=="" (
    echo ERRO: OPENAI_API_KEY nao encontrada no .env
    echo.
    echo Edite o arquivo .env e adicione sua chave:
    echo OPENAI_API_KEY=sk-proj-sua-chave-aqui
    echo.
    pause
    exit /b 1
)

echo OK - Chave OpenAI carregada
echo.

echo Iniciando servidor API...
echo.
echo Acesse: http://localhost:8000
echo Para parar: Ctrl+C
echo.

uvicorn api_scoring:app --reload --port 8000
