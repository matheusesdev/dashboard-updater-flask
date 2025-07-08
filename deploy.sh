#!/bin/bash
# Script de deployment para Linux/macOS
set -e

echo ""
echo "========================================"
echo " Atualizador Dashboard VCA v2.0"
echo " Script de Deployment Linux/macOS"
echo "========================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de log
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 não foi encontrado. Instale Python 3.8+ primeiro."
    exit 1
fi

# Verificar se pip está disponível
if ! command -v pip3 &> /dev/null; then
    log_error "pip3 não foi encontrado."
    exit 1
fi

log_success "Python e pip encontrados"

# Verificar versão do Python
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
log_info "Versão do Python: $PYTHON_VERSION"

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    log_info "Criando ambiente virtual..."
    python3 -m venv venv
    log_success "Ambiente virtual criado"
else
    log_success "Ambiente virtual já existe"
fi

# Ativar ambiente virtual
log_info "Ativando ambiente virtual..."
source venv/bin/activate

# Atualizar pip
log_info "Atualizando pip..."
python -m pip install --upgrade pip

# Instalar dependências
log_info "Instalando dependências..."
pip install -r requirements.txt
log_success "Dependências instaladas"

# Instalar dependências opcionais
log_info "Instalando dependências opcionais..."
OPTIONAL_PACKAGES=("redis" "celery" "structlog" "flask-limiter" "flask-wtf" "python-magic" "psutil")

for package in "${OPTIONAL_PACKAGES[@]}"; do
    if pip install "$package" 2>/dev/null; then
        log_success "$package instalado"
    else
        log_warning "$package não pôde ser instalado (opcional)"
    fi
done

# Criar diretórios necessários
log_info "Criando diretórios..."
mkdir -p uploads logs backups
log_success "Diretórios criados"

# Criar arquivo .env se não existir
if [ ! -f ".env" ]; then
    log_info "Criando arquivo .env..."
    cat > .env << 'EOF'
# Configurações de Desenvolvimento
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
PORT=5000

# Google Sheets
CREDENTIALS_FILE=credentials.json

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://

# Redis (se disponível)
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=app.log
EOF
    log_success "Arquivo .env criado"
else
    log_success "Arquivo .env já existe"
fi

# Verificar credenciais
if [ ! -f "credentials.json" ]; then
    echo ""
    log_warning "credentials.json não encontrado"
    echo "   Configure as credenciais do Google Sheets antes de usar"
    echo ""
fi

# Executar testes básicos
log_info "Executando testes básicos..."
if python -c "from app import create_app; app = create_app('development'); print('App pode ser criada')" 2>/dev/null; then
    log_success "Aplicação importada com sucesso"
else
    log_warning "Erro ao importar aplicação"
fi

# Verificar estrutura de arquivos
log_info "Verificando estrutura de arquivos..."
MISSING_FILES=0

check_file() {
    if [ -f "$1" ]; then
        log_success "$1"
    else
        log_error "$1 não encontrado"
        ((MISSING_FILES++))
    fi
}

check_file "app.py"
check_file "templates/index.html"
check_file "static/style.css"
check_file "requirements.txt"

if [ $MISSING_FILES -gt 0 ]; then
    echo ""
    log_error "$MISSING_FILES arquivo(s) crítico(s) não encontrado(s)"
    echo "Por favor verifique a estrutura do projeto"
    exit 1
fi

# Executar testes unitários se existirem
if [ -d "tests" ]; then
    log_info "Executando testes unitários..."
    if python -m pytest tests/ -v 2>/dev/null; then
        log_success "Testes unitários passaram"
    else
        log_warning "Alguns testes falharam ou pytest não está instalado"
    fi
fi

# Verificar se é ambiente de produção
if [ "$1" = "production" ]; then
    log_info "Configurando para produção..."
    
    # Instalar gunicorn para produção
    pip install gunicorn
    
    # Criar script de início para produção
    cat > start_production.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
export FLASK_ENV=production
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
EOF
    chmod +x start_production.sh
    log_success "Script de produção criado: start_production.sh"
    
    # Criar serviço systemd
    if command -v systemctl &> /dev/null; then
        cat > /tmp/atualizador-dashboard.service << EOF
[Unit]
Description=Atualizador Dashboard VCA
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/start_production.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        log_success "Arquivo de serviço systemd criado em /tmp/"
        log_info "Para instalar: sudo cp /tmp/atualizador-dashboard.service /etc/systemd/system/"
        log_info "Para habilitar: sudo systemctl enable atualizador-dashboard"
        log_info "Para iniciar: sudo systemctl start atualizador-dashboard"
    fi
fi

echo ""
echo "========================================"
echo -e "${GREEN} ✅ DEPLOYMENT CONCLUÍDO COM SUCESSO!${NC}"
echo "========================================"
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Configure o credentials.json:"
echo "   - Baixe as credenciais do Google Cloud Console"
echo "   - Salve como 'credentials.json' na pasta raiz"
echo ""
echo "2. Ajuste as configurações no arquivo .env:"
echo "   - Defina uma SECRET_KEY segura para produção"
echo "   - Configure outras variáveis conforme necessário"
echo ""
echo "3. Para iniciar a aplicação:"
echo "   - Desenvolvimento: python app.py"
echo "   - Produção: ./start_production.sh (se criado)"
echo ""
echo "4. Para background tasks (opcional):"
echo "   - Instale Redis: sudo apt install redis-server"
echo "   - Inicie worker: celery -A app.celery worker"
echo ""
echo "5. Acesse: http://localhost:5000"
echo ""
echo "========================================"

# Perguntar se quer iniciar a aplicação
echo ""
read -p "Deseja iniciar a aplicação agora? (s/n): " START_APP
if [[ $START_APP =~ ^[Ss]$ ]]; then
    echo ""
    log_info "Iniciando aplicação..."
    echo "Pressione Ctrl+C para parar"
    echo ""
    python app.py
fi

echo ""
echo "Deployment finalizado."
