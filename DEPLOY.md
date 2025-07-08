# === CONFIGURAÇÃO PARA RENDER ===

## 🌐 Deploy no Render

### Pré-requisitos
- Conta no [Render](https://render.com)
- Repositório no GitHub (já configurado)
- Credenciais do Google Sheets

### 📋 Configuração Passo a Passo

#### 1. **Preparar Credenciais do Google**
```bash
# Converter credentials.json para string base64
# No Windows (PowerShell):
[Convert]::ToBase64String([IO.File]::ReadAllBytes("credentials.json"))

# No Linux/Mac:
base64 -w 0 credentials.json
```

#### 2. **Criar Web Service no Render**
1. Acesse [render.com](https://render.com)
2. Clique em "New +" → "Web Service"
3. Conecte seu repositório GitHub
4. Configure:
   - **Name**: `atualizador-vca`
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free` (para testes)

#### 3. **Configurar Variáveis de Ambiente**
No painel do Render, adicione:

```env
# Configurações do Flask
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=sua_chave_secreta_super_forte_aqui

# Google Sheets
GOOGLE_SHEET_NAME=IMOBILIARIAS CARUARU 03.06.2025
GOOGLE_SHEET_TAB=BaseDeDados
GOOGLE_CREDENTIALS_BASE64=sua_string_base64_aqui

# Configurações de servidor
HOST=0.0.0.0
PORT=10000
```

#### 4. **Configurações de Rede**
- **Port**: 10000 (padrão do Render)
- **Health Check Path**: `/` (opcional)

### 🔧 **Alternativas ao Render**

#### **Railway** (Muito fácil)
```bash
# Instalar CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

#### **PythonAnywhere** (Especialista em Python)
- Upload manual de arquivos
- Configuração via painel web
- Excelente para projetos Python

#### **Vercel** (Para sites estáticos principalmente)
```bash
# Instalar CLI
npm install -g vercel

# Deploy
vercel --prod
```

### 🚨 **IMPORTANTE - Segurança no Deploy**

#### ❌ **NUNCA faça:**
- Upload direto do credentials.json
- Commit de variáveis sensíveis
- Usar credenciais em texto plano

#### ✅ **SEMPRE faça:**
- Use variáveis de ambiente
- Converta credentials.json para Base64
- Configure HTTPS (automático no Render)
- Use chaves secretas fortes

### 📊 **Monitoramento**
- Render fornece logs em tempo real
- Métricas de performance
- Alertas de erro

### 💰 **Custos**
- **Render Free**: 750 horas/mês (suficiente para testes)
- **Render Starter**: $7/mês (para produção)
- **Railway**: $5/mês após trial
- **PythonAnywhere**: $5/mês

### 🔄 **Auto-Deploy**
Configure auto-deploy no GitHub:
- Push na branch `main` → Deploy automático
- Ideal para atualizações rápidas
