@echo off
REM Script de deployment para Windows
echo.
echo ========================================
echo  Atualizador Dashboard VCA v2.0
echo  Script de Deployment Windows
echo ========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao foi encontrado. Instale Python 3.8+ primeiro.
    pause
    exit /b 1
)

REM Verificar se pip está disponível
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: pip nao foi encontrado.
    pause
    exit /b 1
)

echo ✅ Python e pip encontrados
echo.

REM Criar ambiente virtual se não existir
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ERRO: Falha ao criar ambiente virtual
        pause
        exit /b 1
    )
    echo ✅ Ambiente virtual criado
) else (
    echo ✅ Ambiente virtual já existe
)

REM Ativar ambiente virtual
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERRO: Falha ao ativar ambiente virtual
    pause
    exit /b 1
)

REM Atualizar pip
echo Atualizando pip...
python -m pip install --upgrade pip

REM Instalar dependências
echo Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias
    pause
    exit /b 1
)

echo ✅ Dependências instaladas

REM Instalar dependências opcionais
echo.
echo Instalando dependencias opcionais...
pip install redis celery structlog flask-limiter flask-wtf psutil 2>nul
echo ⚠️ Algumas dependencias opcionais podem falhar (normal)

REM Criar diretórios necessários
echo.
echo Criando diretorios...
if not exist "uploads" mkdir uploads
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups
echo ✅ Diretórios criados

REM Criar arquivo .env se não existir
if not exist ".env" (
    echo Criando arquivo .env...
    (
        echo # Configurações de Desenvolvimento
        echo FLASK_ENV=development
        echo SECRET_KEY=dev-secret-key-change-in-production
        echo PORT=5000
        echo.
        echo # Google Sheets
        echo CREDENTIALS_FILE=credentials.json
        echo.
        echo # Rate Limiting
        echo RATELIMIT_STORAGE_URL=memory://
        echo.
        echo # Logging
        echo LOG_LEVEL=INFO
        echo LOG_FILE=app.log
    ) > .env
    echo ✅ Arquivo .env criado
) else (
    echo ✅ Arquivo .env já existe
)

REM Verificar credenciais
if not exist "credentials.json" (
    echo.
    echo ⚠️ ATENÇÃO: credentials.json não encontrado
    echo    Configure as credenciais do Google Sheets antes de usar
    echo.
)

REM Executar testes básicos
echo.
echo Executando testes básicos...
python -c "from app import create_app; app = create_app('development'); print('✅ App pode ser criada')" 2>nul
if errorlevel 1 (
    echo ⚠️ Erro ao importar aplicação
) else (
    echo ✅ Aplicação importada com sucesso
)

REM Verificar estrutura de arquivos
echo.
echo Verificando estrutura de arquivos...
set missing_files=0

if not exist "app.py" (
    echo ❌ app.py não encontrado
    set /a missing_files+=1
) else (
    echo ✅ app.py
)

if not exist "templates\index.html" (
    echo ❌ templates\index.html não encontrado
    set /a missing_files+=1
) else (
    echo ✅ templates\index.html
)

if not exist "static\style.css" (
    echo ❌ static\style.css não encontrado
    set /a missing_files+=1
) else (
    echo ✅ static\style.css
)

if not exist "requirements.txt" (
    echo ❌ requirements.txt não encontrado
    set /a missing_files+=1
) else (
    echo ✅ requirements.txt
)

if %missing_files% gtr 0 (
    echo.
    echo ❌ %missing_files% arquivo(s) crítico(s) não encontrado(s)
    echo Por favor verifique a estrutura do projeto
    pause
    exit /b 1
)

echo.
echo ========================================
echo  ✅ DEPLOYMENT CONCLUÍDO COM SUCESSO!
echo ========================================
echo.
echo 📋 Próximos passos:
echo.
echo 1. Configure o credentials.json:
echo    - Baixe as credenciais do Google Cloud Console
echo    - Salve como 'credentials.json' na pasta raiz
echo.
echo 2. Ajuste as configurações no arquivo .env:
echo    - Defina uma SECRET_KEY segura para produção
echo    - Configure outras variáveis conforme necessário
echo.
echo 3. Para iniciar a aplicação:
echo    - Execute: python app.py
echo    - Ou use: flask run
echo.
echo 4. Para produção:
echo    - Use gunicorn: pip install gunicorn
echo    - Execute: gunicorn app:app
echo.
echo 5. Acesse: http://localhost:5000
echo.
echo ========================================

REM Perguntar se quer iniciar a aplicação
echo.
set /p start_app="Deseja iniciar a aplicação agora? (s/n): "
if /i "%start_app%"=="s" (
    echo.
    echo Iniciando aplicação...
    echo Pressione Ctrl+C para parar
    echo.
    python app.py
)

echo.
echo Deployment finalizado.
pause
