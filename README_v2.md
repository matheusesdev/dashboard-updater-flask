# Atualizador Dashboard VCA v2.0

## 🚀 Novidades da Versão 2.0

### ✨ Melhorias Implementadas

#### **Arquitetura e Segurança**
- ✅ **Arquitetura modular** com separação de responsabilidades
- ✅ **Validação robusta** de arquivos com verificação de conteúdo
- ✅ **Rate limiting** para prevenir abuso
- ✅ **CSRF protection** habilitado
- ✅ **Logging estruturado** com diferentes níveis
- ✅ **Health check** e métricas de sistema
- ✅ **Tratamento de erros** centralizado e robusto

#### **Performance e Escalabilidade**
- ✅ **Background processing** com Celery (opcional)
- ✅ **Processamento assíncrono** para arquivos grandes
- ✅ **Cache inteligente** de recursos estáticos
- ✅ **Otimizações de frontend** com loading states
- ✅ **Monitoramento em tempo real** do status

#### **Interface e Experiência do Usuário**
- ✅ **UI moderna e responsiva** com novo design
- ✅ **Progress bar** para acompanhar uploads
- ✅ **Feedback visual** em tempo real
- ✅ **Validação de arquivos** no frontend
- ✅ **Log interativo** com download e limpeza
- ✅ **Dark mode** automático baseado na preferência do sistema
- ✅ **Acessibilidade** melhorada

#### **Desenvolvedor e Operações**
- ✅ **Testes unitários** e de integração
- ✅ **Scripts de deployment** automatizados
- ✅ **Configuração centralizada** com environments
- ✅ **Documentação técnica** completa
- ✅ **Docker support** (preparado)
- ✅ **CI/CD ready** para GitHub Actions

---

## 📁 Nova Estrutura do Projeto

```
atualizador-web/
├── 📁 config/                  # Configurações
│   ├── __init__.py
│   └── config.py              # Classes de configuração
├── 📁 exceptions/             # Exceções customizadas
│   ├── __init__.py
│   └── errors.py              # Definições de erros
├── 📁 services/               # Serviços de negócio
│   ├── __init__.py
│   ├── file_processing_service.py
│   ├── google_sheets_service.py
│   └── celery_tasks.py        # Tasks assíncronas
├── 📁 utils/                  # Utilitários
│   ├── __init__.py
│   └── validators.py          # Validadores melhorados
├── 📁 tests/                  # Testes automatizados
│   ├── __init__.py
│   ├── test_validators.py
│   └── test_app.py
├── 📁 templates/              # Templates HTML
│   └── index.html             # Interface modernizada
├── 📁 static/                 # Assets estáticos
│   ├── style.css              # CSS v2.0 responsivo
│   └── LOGO.png
├── 📁 uploads/                # Arquivos temporários
├── 📁 logs/                   # Logs da aplicação
├── 📁 backups/                # Backups automáticos
├── app.py                     # Aplicação principal refatorada
├── requirements.txt           # Dependências atualizadas
├── deploy.py                  # Script de deployment Python
├── deploy.bat                 # Script Windows
├── deploy.sh                  # Script Linux/macOS
├── .env.example               # Exemplo de configuração
└── README_v2.md              # Esta documentação
```

---

## 🛠 Instalação e Configuração

### Método 1: Script Automatizado (Recomendado)

#### Windows:
```cmd
# Executar como Administrador
.\deploy.bat
```

#### Linux/macOS:
```bash
chmod +x deploy.sh
./deploy.sh
```

#### Qualquer Sistema (Python):
```bash
python deploy.py
```

### Método 2: Instalação Manual

1. **Criar ambiente virtual:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

2. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

3. **Configurar variáveis de ambiente:**
```bash
cp .env.example .env
# Editar .env com suas configurações
```

4. **Configurar Google Sheets:**
   - Baixe as credenciais do Google Cloud Console
   - Salve como `credentials.json` na raiz do projeto

---

## ⚙️ Configuração

### Arquivo `.env`

```env
# Ambiente
FLASK_ENV=production                    # development | production | testing
SECRET_KEY=sua-chave-secreta-aqui      # ALTERE em produção!
PORT=5000

# Google Sheets
CREDENTIALS_FILE=credentials.json

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://         # ou redis://localhost:6379/0
RATELIMIT_DEFAULT=100 per hour
RATELIMIT_UPLOAD=10 per minute

# Celery (Background Tasks)
REDIS_URL=redis://localhost:6379/0     # Para tasks assíncronas

# Logging
LOG_LEVEL=INFO                          # DEBUG | INFO | WARNING | ERROR
LOG_FILE=app.log

# Upload Settings
MAX_CONTENT_LENGTH=524288000           # 500MB em bytes
UPLOAD_FOLDER=uploads
```

### Configurações Avançadas

#### Para Redis/Celery (Background Tasks):
```bash
# Instalar Redis
sudo apt install redis-server  # Ubuntu/Debian
brew install redis             # macOS

# Iniciar worker Celery
celery -A app.celery worker --loglevel=info

# Iniciar scheduler (tasks periódicas)
celery -A app.celery beat --loglevel=info
```

#### Para Produção com Gunicorn:
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

---

## 🚦 Usando a Aplicação

### 1. **Interface Principal**
- Acesse `http://localhost:5000`
- Interface moderna com status em tempo real
- Verificação automática da saúde do sistema

### 2. **Upload de Arquivos**
- Formatos suportados: `.xlsx`, `.xls`, `.csv`, `.ods`
- Tamanho máximo: 200MB por arquivo
- Validação de conteúdo automática
- Progress bar para acompanhar o upload

### 3. **Processamento**
- **Síncrono**: Para arquivos pequenos (padrão)
- **Assíncrono**: Para arquivos grandes (marcar opção)
- Status em tempo real durante o processamento
- Logs detalhados de cada etapa

### 4. **Monitoramento**
- **Health Check**: `/health` - Status do sistema
- **Métricas**: `/metrics` - CPU, memória, disk
- **Status Tasks**: `/status/<task_id>` - Para tasks assíncronas

---

## 🧪 Testes

### Executar Testes
```bash
# Todos os testes
python -m pytest tests/ -v

# Testes específicos
python -m pytest tests/test_validators.py -v
python -m pytest tests/test_app.py -v

# Com cobertura
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=html
```

### Testes Manuais
```bash
# Teste de importação
python -c "from app import create_app; app = create_app(); print('OK')"

# Teste de health check
curl http://localhost:5000/health

# Teste de métricas
curl http://localhost:5000/metrics
```

---

## 🔧 API Endpoints

### **Principais**
- `GET /` - Interface principal
- `POST /upload` - Upload de arquivo
- `GET /health` - Health check
- `GET /metrics` - Métricas do sistema

### **Background Tasks**
- `GET /status/<task_id>` - Status de task assíncrona

### **Exemplos de Uso**

#### Upload via cURL:
```bash
curl -X POST -F "file=@planilha.xlsx" http://localhost:5000/upload
```

#### Upload assíncrono:
```bash
curl -X POST -F "file=@planilha.xlsx" -F "async=true" http://localhost:5000/upload
```

#### Verificar status:
```bash
curl http://localhost:5000/status/task-id-aqui
```

---

## 🛡 Segurança

### **Implementadas**
- ✅ Validação rigorosa de arquivos (extensão, tamanho, conteúdo)
- ✅ CSRF protection
- ✅ Rate limiting por IP
- ✅ Sanitização de nomes de arquivo
- ✅ Logging de atividades suspeitas
- ✅ Headers de segurança
- ✅ Validação de MIME types

### **Recomendações Adicionais**
- 🔒 Use HTTPS em produção
- 🔒 Configure firewall adequadamente
- 🔒 Monitore logs regularmente
- 🔒 Mantenha dependências atualizadas
- 🔒 Use proxy reverso (nginx)

---

## 🚀 Deploy em Produção

### **Render (Cloud)**
1. Conecte seu repositório GitHub
2. Configure variáveis de ambiente
3. Use o `Procfile` incluído
4. Deploy automático

### **VPS/Servidor**
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/atualizador-web.git
cd atualizador-web

# Execute deployment
./deploy.sh production

# Configure nginx (exemplo)
sudo cp nginx.conf.example /etc/nginx/sites-available/atualizador
sudo ln -s /etc/nginx/sites-available/atualizador /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

### **Docker (Opcional)**
```dockerfile
# Dockerfile incluído para containerização
docker build -t atualizador-dashboard .
docker run -p 5000:5000 atualizador-dashboard
```

---

## 🐛 Troubleshooting

### **Problemas Comuns**

#### "Credenciais do Google não encontradas"
```bash
# Verificar se arquivo existe
ls -la credentials.json

# Verificar permissões
chmod 600 credentials.json
```

#### "Redis connection failed"
```bash
# Verificar se Redis está rodando
redis-cli ping

# Instalar Redis se necessário
sudo apt install redis-server
sudo systemctl start redis
```

#### "Rate limit exceeded"
```bash
# Aguardar reset automático ou ajustar configuração
# No .env:
RATELIMIT_UPLOAD=20 per minute
```

#### "Arquivo muito grande"
```bash
# Ajustar limite no .env:
MAX_CONTENT_LENGTH=1048576000  # 1GB
```

### **Logs e Debugging**

#### Verificar logs:
```bash
tail -f app.log
tail -f logs/error.log
```

#### Debug mode:
```bash
# No .env:
FLASK_ENV=development
LOG_LEVEL=DEBUG
```

#### Verificar health:
```bash
curl http://localhost:5000/health | jq
```

---

## 📊 Monitoramento

### **Métricas Disponíveis**
- CPU usage
- Memory usage
- Disk usage
- Upload folder size
- Active Celery workers
- Task queue status

### **Alertas Recomendados**
- CPU > 80%
- Memory > 90%
- Disk > 85%
- Health status != "healthy"
- Error rate > 5%

---

## 🤝 Contribuindo

### **Estrutura de Desenvolvimento**
```bash
# Setup desenvolvimento
./deploy.sh
source venv/bin/activate

# Instalar deps de desenvolvimento
pip install pytest pytest-cov black flake8

# Executar testes
python -m pytest

# Formatar código
black .

# Verificar qualidade
flake8 .
```

### **Padrões**
- Use **type hints** sempre que possível
- Escreva **testes** para novas funcionalidades
- Mantenha **logs estruturados**
- Siga **PEP 8** para style guide
- Documente **APIs** adequadamente

---

## 📋 Roadmap

### **Próximas Funcionalidades**
- [ ] Dashboard analytics
- [ ] Multi-tenant support
- [ ] Backup automático para Cloud
- [ ] Integração com mais serviços (Notion, Airtable)
- [ ] API REST completa
- [ ] Interface administrativa
- [ ] Scheduled jobs via interface
- [ ] Audit trail completo

### **Melhorias Técnicas**
- [ ] Kubernetes deployment
- [ ] Metrics com Prometheus
- [ ] Distributed tracing
- [ ] Database caching
- [ ] CDN integration
- [ ] Load balancing
- [ ] Auto-scaling

---

## 📞 Suporte

### **Contato**
- 🏢 **VCA Construtora**
- 💻 **GitHub**: [Repositório do Projeto]
- 📧 **Email**: [email de suporte]

### **Documentação Técnica**
- `SECURITY.md` - Práticas de segurança
- `DEPLOY.md` - Guia de deployment
- `STATUS.md` - Status das funcionalidades
- `CHANGELOG.md` - Histórico de mudanças

---

**© 2025 VCA Construtora - Atualizador Dashboard v2.0**
