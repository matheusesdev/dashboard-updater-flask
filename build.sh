#!/usr/bin/env bash
# Render build script - Versão completa

echo "🚀 Iniciando build do Atualizador VCA..."

# Verificar versão do Python
echo "🐍 Verificando Python..."
python --version

# Atualizar pip
echo "⬆️ Atualizando pip..."
pip install --upgrade pip

# Instalar dependências
echo "📦 Instalando dependências Python..."
pip install -r requirements.txt

# Criar pasta uploads se não existir
echo "📁 Criando pasta uploads..."
mkdir -p uploads

# Verificar instalações críticas
echo "✅ Verificando instalações..."
python -c "import flask; print(f'Flask: {flask.__version__}')"
python -c "import gspread; print(f'gspread: {gspread.__version__}')"
python -c "import pandas; print(f'pandas: {pandas.__version__}')"

echo "🎉 Build concluído com sucesso!"
echo "🌐 Aplicação pronta para deploy!"
