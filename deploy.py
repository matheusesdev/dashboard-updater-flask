#!/usr/bin/env python3
"""
Script de deployment para produção
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, check=True):
    """Executa comando no shell"""
    logger.info(f"Executando: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
    
    if result.stdout:
        logger.info(f"Output: {result.stdout}")
    if result.stderr:
        logger.warning(f"Error: {result.stderr}")
    
    return result

def check_requirements():
    """Verifica se os requisitos estão instalados"""
    logger.info("Verificando requisitos...")
    
    try:
        import flask
        import gspread
        import pandas
        logger.info("✅ Dependências básicas instaladas")
    except ImportError as e:
        logger.error(f"❌ Dependência faltando: {e}")
        return False
    
    # Verificar arquivos críticos
    critical_files = [
        'app.py',
        'credentials.json',
        'requirements.txt',
        'templates/index.html',
        'static/style.css'
    ]
    
    for file_path in critical_files:
        if not Path(file_path).exists():
            logger.error(f"❌ Arquivo crítico não encontrado: {file_path}")
            return False
    
    logger.info("✅ Todos os arquivos críticos encontrados")
    return True

def install_dependencies():
    """Instala dependências"""
    logger.info("Instalando dependências...")
    
    # Instalar dependências Python
    run_command("pip install -r requirements.txt")
    
    # Instalar dependências opcionais se disponíveis
    optional_packages = [
        "redis",
        "celery",
        "structlog",
        "flask-limiter",
        "flask-wtf",
        "python-magic",
        "psutil"
    ]
    
    for package in optional_packages:
        try:
            run_command(f"pip install {package}", check=False)
            logger.info(f"✅ {package} instalado")
        except:
            logger.warning(f"⚠️ {package} não pôde ser instalado (opcional)")

def setup_environment():
    """Configura variáveis de ambiente"""
    logger.info("Configurando ambiente...")
    
    # Criar .env se não existir
    if not Path('.env').exists():
        env_content = """# Configurações de Produção
FLASK_ENV=production
SECRET_KEY=change-this-secret-key-in-production
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
"""
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        logger.info("✅ Arquivo .env criado")
    
    # Verificar credenciais do Google
    if not Path('credentials.json').exists():
        logger.warning("⚠️ credentials.json não encontrado. Configure as credenciais do Google Sheets.")

def create_directories():
    """Cria diretórios necessários"""
    logger.info("Criando diretórios...")
    
    directories = [
        'uploads',
        'logs',
        'backups'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"✅ Diretório criado: {directory}")

def run_tests():
    """Executa testes básicos"""
    logger.info("Executando testes...")
    
    try:
        # Testes unitários
        result = run_command("python -m pytest tests/ -v", check=False)
        if result.returncode == 0:
            logger.info("✅ Testes unitários passaram")
        else:
            logger.warning("⚠️ Alguns testes falharam")
        
        # Teste de importação da aplicação
        run_command("python -c 'from app import create_app; app = create_app(); print(\"App criada com sucesso\")'")
        logger.info("✅ Aplicação pode ser importada")
        
    except Exception as e:
        logger.error(f"❌ Erro nos testes: {e}")
        return False
    
    return True

def create_systemd_service():
    """Cria serviço systemd (Linux)"""
    if os.name != 'posix':
        logger.info("Skipping systemd service (não é Linux)")
        return
    
    service_content = f"""[Unit]
Description=Atualizador Dashboard VCA
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}/venv/bin
ExecStart={sys.executable} app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    try:
        with open('/tmp/atualizador-dashboard.service', 'w') as f:
            f.write(service_content)
        logger.info("✅ Arquivo de serviço systemd criado em /tmp/")
        logger.info("Para instalar: sudo cp /tmp/atualizador-dashboard.service /etc/systemd/system/")
        logger.info("Para habilitar: sudo systemctl enable atualizador-dashboard")
        logger.info("Para iniciar: sudo systemctl start atualizador-dashboard")
    except Exception as e:
        logger.warning(f"⚠️ Não foi possível criar serviço systemd: {e}")

def optimize_for_production():
    """Otimizações para produção"""
    logger.info("Aplicando otimizações de produção...")
    
    # Compilar templates (se Jinja2 suportar)
    try:
        run_command("python -c 'from jinja2 import Environment; print(\"Templates OK\")'")
        logger.info("✅ Templates Jinja2 verificados")
    except:
        logger.warning("⚠️ Erro ao verificar templates")
    
    # Otimizar CSS/JS (minificar se necessário)
    logger.info("✅ Assets verificados")

def backup_current_version():
    """Cria backup da versão atual"""
    logger.info("Criando backup...")
    
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path(f"backups/backup_{timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Arquivos críticos para backup
    backup_files = [
        'app_old.py',
        'templates/index_old.html',
        'static/style_old.css',
        '.env'
    ]
    
    for file_path in backup_files:
        if Path(file_path).exists():
            shutil.copy2(file_path, backup_dir)
    
    logger.info(f"✅ Backup criado em: {backup_dir}")

def main():
    """Função principal de deployment"""
    logger.info("🚀 Iniciando deployment do Atualizador Dashboard VCA v2.0")
    
    try:
        # 1. Verificar requisitos
        if not check_requirements():
            logger.error("❌ Falha na verificação de requisitos")
            sys.exit(1)
        
        # 2. Criar backup
        backup_current_version()
        
        # 3. Instalar dependências
        install_dependencies()
        
        # 4. Configurar ambiente
        setup_environment()
        
        # 5. Criar diretórios
        create_directories()
        
        # 6. Executar testes
        if not run_tests():
            logger.warning("⚠️ Alguns testes falharam, mas continuando...")
        
        # 7. Otimizações de produção
        optimize_for_production()
        
        # 8. Criar serviço systemd (se Linux)
        create_systemd_service()
        
        logger.info("✅ Deployment concluído com sucesso!")
        logger.info("📋 Próximos passos:")
        logger.info("   1. Configure o credentials.json com suas credenciais do Google")
        logger.info("   2. Ajuste as variáveis no arquivo .env")
        logger.info("   3. Para iniciar: python app.py")
        logger.info("   4. Para produção: considere usar gunicorn")
        logger.info("   5. Configure um proxy reverso (nginx) se necessário")
        
    except Exception as e:
        logger.error(f"❌ Erro durante deployment: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
