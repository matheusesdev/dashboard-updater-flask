@echo off
echo ================================
echo   SETUP ATUALIZADOR VCA
echo ================================
echo.

echo [1/5] Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado!
    echo Instale Python 3.x antes de continuar.
    pause
    exit /b 1
)

echo.
echo [2/5] Criando ambiente virtual...
if not exist "venv" (
    python -m venv venv
    echo Ambiente virtual criado com sucesso!
) else (
    echo Ambiente virtual ja existe.
)

echo.
echo [3/5] Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo.
echo [4/5] Instalando dependencias...
pip install -r requirements.txt

echo.
echo [5/5] Configurando arquivos...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo Arquivo .env criado! Edite-o com suas configuracoes.
    )
) else (
    echo Arquivo .env ja existe.
)

if not exist "uploads" (
    mkdir uploads
    echo Pasta uploads criada.
)

echo.
echo ================================
echo   SETUP CONCLUIDO!
echo ================================
echo.
echo PROXIMOS PASSOS:
echo 1. Edite o arquivo .env com suas configuracoes
echo 2. Adicione o arquivo credentials.json na raiz do projeto
echo 3. Execute: python app.py
echo.
echo Para ativar o ambiente virtual: venv\Scripts\activate
echo Para executar a aplicacao: python app.py
echo.
pause
