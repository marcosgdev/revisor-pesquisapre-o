@echo off
REM Script de Configuracao para Windows
REM Execute: configurar.bat

echo ========================================
echo CONFIGURADOR DO SISTEMA DE SCORING
echo ========================================
echo.

REM Verifica Python
echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale Python em: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK - Python encontrado
echo.

REM Verifica dependencias
echo [2/4] Verificando dependencias...
python -c "import openai" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    pip install openai pdfplumber PyPDF2 fastapi uvicorn python-multipart pydantic python-dotenv pandas numpy requests
) else (
    echo OK - Dependencias instaladas
)
echo.

REM Cria arquivo .env
echo [3/4] Configurando arquivo .env...
if exist .env (
    echo Arquivo .env ja existe
    choice /C SN /M "Deseja recriar? (S/N)"
    if errorlevel 2 goto pular_env
)

echo.
echo Voce precisa de uma chave da OpenAI
echo 1. Acesse: https://platform.openai.com/api-keys
echo 2. Faca login ou crie conta
echo 3. Clique em 'Create new secret key'
echo 4. Copie a chave (comeca com sk-)
echo.
set /p CHAVE="Cole sua chave OpenAI aqui: "

if "%CHAVE%"=="" (
    echo ERRO: Chave nao pode estar vazia
    pause
    exit /b 1
)

echo OPENAI_API_KEY=%CHAVE%> .env
echo OPENAI_MODEL=gpt-4o>> .env
echo.
echo OK - Arquivo .env criado!

:pular_env
echo.

REM Cria diretorios
echo [4/4] Criando diretorios...
if not exist uploads mkdir uploads
if not exist results mkdir results
if not exist logs mkdir logs
echo OK - Diretorios criados
echo.

echo ========================================
echo CONFIGURACAO COMPLETA!
echo ========================================
echo.
echo Proximos passos:
echo.
echo 1. Testar o sistema:
echo    python teste_sistema.py
echo.
echo 2. Iniciar API:
echo    python iniciar_api.bat
echo.
echo 3. Analisar PDF:
echo    python sistema_scoring.py seu_documento.pdf
echo.
pause
