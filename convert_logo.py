#!/usr/bin/env python3
"""
Script para converter LOGO.png para Base64
Para uso como fallback no HTML
"""

import base64
import os

def converter_logo():
    arquivo_logo = "static/LOGO.png"
    
    if not os.path.exists(arquivo_logo):
        print(f"❌ Arquivo '{arquivo_logo}' não encontrado!")
        return False
    
    try:
        # Ler o arquivo PNG
        with open(arquivo_logo, 'rb') as file:
            conteudo = file.read()
        
        # Converter para Base64
        base64_string = base64.b64encode(conteudo).decode('utf-8')
        data_uri = f"data:image/png;base64,{base64_string}"
        
        print("✅ Conversão da logo realizada com sucesso!")
        print(f"📊 Tamanho original: {len(conteudo)} bytes")
        print(f"📊 Tamanho Base64: {len(data_uri)} caracteres")
        print("\n" + "="*60)
        print("DATA URI DA LOGO (para usar como fallback no HTML):")
        print("="*60)
        print(data_uri[:200] + "..." if len(data_uri) > 200 else data_uri)
        print("="*60)
        print("\n📋 COMO USAR NO HTML:")
        print('<img src="data_uri_acima" alt="Logo VCA" class="logo">')
        
        # Salvar em arquivo para referência
        with open("logo_base64.txt", "w") as f:
            f.write(data_uri)
        print("\n💾 Base64 completo salvo em: logo_base64.txt")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao converter logo: {str(e)}")
        return False

if __name__ == "__main__":
    print("🖼️ Convertendo LOGO.png para Base64...")
    converter_logo()
