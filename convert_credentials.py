#!/usr/bin/env python3
"""
Script para converter credentials.json para Base64
Para uso no deploy no Render
"""

import base64
import os
import sys

def converter_credenciais():
    arquivo_credenciais = "credentials.json"
    
    if not os.path.exists(arquivo_credenciais):
        print(f"❌ Arquivo '{arquivo_credenciais}' não encontrado!")
        print("Certifique-se de que o arquivo está na raiz do projeto.")
        return False
    
    try:
        # Ler o arquivo JSON
        with open(arquivo_credenciais, 'rb') as file:
            conteudo = file.read()
        
        # Converter para Base64
        base64_string = base64.b64encode(conteudo).decode('utf-8')
        
        print("✅ Conversão realizada com sucesso!")
        print("\n" + "="*60)
        print("COPIE O TEXTO ABAIXO PARA A VARIÁVEL DE AMBIENTE:")
        print("GOOGLE_CREDENTIALS_BASE64")
        print("="*60)
        print(base64_string)
        print("="*60)
        print("\n📋 COMO USAR NO RENDER:")
        print("1. Vá em Settings > Environment")
        print("2. Adicione uma nova variável:")
        print("   Key: GOOGLE_CREDENTIALS_BASE64")
        print("   Value: [cole o texto acima]")
        print("3. Salve e faça redeploy")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao converter arquivo: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔄 Convertendo credentials.json para Base64...")
    
    if converter_credenciais():
        sys.exit(0)
    else:
        sys.exit(1)
