#!/bin/bash

echo "================================"
echo "   SETUP ATUALIZADOR VCA"
echo "================================"
echo

echo "[1/5] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python 3 não encontrado!"
    echo "Instale Python 3.x antes de continuar."
    exit 1
fi
python3 --version

echo
echo "[2/5] Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Ambiente virtual criado com sucesso!"
else
    echo "Ambiente virtual já existe."
fi

echo
echo "[3/5] Ativando ambiente virtual..."
source venv/bin/activate

echo
echo "[4/5] Instalando dependências..."
pip install -r requirements.txt

echo
echo "[5/5] Configurando arquivos..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Arquivo .env criado! Edite-o com suas configurações."
    fi
else
    echo "Arquivo .env já existe."
fi

if [ ! -d "uploads" ]; then
    mkdir uploads
    echo "Pasta uploads criada."
fi

echo
echo "================================"
echo "   SETUP CONCLUÍDO!"
echo "================================"
echo
echo "PRÓXIMOS PASSOS:"
echo "1. Edite o arquivo .env com suas configurações"
echo "2. Adicione o arquivo credentials.json na raiz do projeto"
echo "3. Execute: python app.py"
echo
echo "Para ativar o ambiente virtual: source venv/bin/activate"
echo "Para executar a aplicação: python app.py"
echo
