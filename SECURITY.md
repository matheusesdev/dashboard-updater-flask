# === GUIA DE SEGURANÇA PARA GITHUB ===

## 🔒 SEGURANÇA IMPLEMENTADA

### Arquivos Protegidos
Os seguintes arquivos NÃO serão enviados ao GitHub:
- `credentials.json` - Credenciais do Google Sheets
- `.env` - Variáveis de ambiente sensíveis
- `uploads/` - Arquivos temporários
- `__pycache__/` - Cache do Python

### O que está seguro para commit:
- Código fonte (app.py, iniciar_processo.py)
- Templates e estilos (HTML, CSS)
- Dependências (requirements.txt)
- Documentação (README.md)
- Configurações de exemplo (.env.example)

## 🚨 ANTES DE FAZER O PRIMEIRO COMMIT

### 1. Verificar arquivos sensíveis
```bash
# Listar arquivos que serão commitados
git status

# Se você ver credentials.json ou .env na lista, PARE!
# Adicione-os ao .gitignore antes de continuar
```

### 2. Configurar o repositório
```bash
# Inicializar Git (se ainda não foi feito)
git init

# Adicionar origem remota
git remote add origin https://github.com/SEU_USUARIO/atualizador-web.git
```

### 3. Primeiro commit seguro
```bash
# Adicionar apenas arquivos seguros
git add .
git commit -m "feat: inicial commit do atualizador de dashboard VCA"
git push -u origin main
```

## 🔧 CONFIGURAÇÃO PARA NOVOS DESENVOLVEDORES

### Quando alguém clonar o repositório:

1. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variáveis de ambiente:**
   ```bash
   copy .env.example .env
   # Editar .env com valores reais
   ```

3. **Adicionar credenciais do Google:**
   - Baixar credentials.json do Google Cloud Console
   - Colocar na raiz do projeto
   - Compartilhar planilha com email da conta de serviço

## ⚠️ NUNCA FAÇA ISSO:

❌ `git add credentials.json`
❌ `git add .env`
❌ Commitar dados de API ou senhas
❌ Fazer push sem verificar o que está sendo enviado

## ✅ SEMPRE FAÇA ISSO:

✅ Verificar .gitignore antes do primeiro commit
✅ Usar variáveis de ambiente para configurações
✅ Documentar o processo de setup
✅ Revisar arquivos antes de commitar

## 🆘 SE VOCÊ COMMITOU ALGO SENSÍVEL POR ENGANO:

1. **NUNCA** faça push
2. Use `git reset HEAD~1` para desfazer o último commit
3. Adicione o arquivo ao .gitignore
4. Faça um novo commit

Se já fez push, considere:
- Revogar e recriar as credenciais
- Usar `git filter-branch` ou BFG Repo-Cleaner
- Em casos extremos, deletar e recriar o repositório
