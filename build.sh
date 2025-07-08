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

# Verificar arquivos estáticos
echo "🖼️ Verificando arquivos estáticos..."
ls -la static/
echo "📊 Arquivos em static/:"
for file in static/*; do
    if [ -f "$file" ]; then
        echo "  - $(basename "$file") ($(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "?") bytes)"
    fi
done

# Verificar instalações críticas
echo "✅ Verificando instalações..."
python -c "import flask; print(f'Flask: {flask.__version__}')"
python -c "import gspread; print(f'gspread: {gspread.__version__}')"
python -c "import pandas; print(f'pandas: {pandas.__version__}')"

echo "🎉 Build concluído com sucesso!"
echo "🌐 Aplicação pronta para deploy!"
