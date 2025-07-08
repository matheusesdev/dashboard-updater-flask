# --- START OF FILE iniciar_processo.py ---

import pandas as pd
import gspread
import os
import json
import base64
import tempfile

def iniciar_processo_de_atualizacao(caminho_planilha_base):
    log_messages = []
    
    try:
        log_messages.append("Iniciando processo de sincronização...")
        
        # --- Configurações (usando variáveis de ambiente quando disponível) ---
        NOME_PLANILHA_GOOGLE = os.getenv('GOOGLE_SHEET_NAME', 'IMOBILIARIAS CARUARU 03.06.2025')
        NOME_ABA_GOOGLE = os.getenv('GOOGLE_SHEET_TAB', 'BaseDeDados')
        ARQUIVO_CREDENCIAIS = 'credentials.json'
        COLUNAS_PARA_LER_DA_BASE = ['Nome fantasia', 'Corretores', 'Estado', 'Cidade', 'Ativa no painel']
        MAPA_COLUNAS_DIRETAS = {'Nome fantasia': 'Imobiliária', 'Corretores': 'Quantidade de Corretores', 'Estado': 'Estado', 'Cidade': 'Cidade'}
        COLUNA_STATUS_BASE = 'Ativa no painel'
        COLUNA_STATUS_DASH = 'Ativa em sistema'
        COLUNA_CONTRATO_DASH = 'Contrato assinado'

        # <<< NOVA LÓGICA DE LEITURA DE ARQUIVO >>>
        log_messages.append(f"Lendo dados de: {os.path.basename(caminho_planilha_base)}")
        
        file_ext = os.path.splitext(caminho_planilha_base)[1].lower()

        if file_ext in ['.xlsx', '.xls']:
            df_base = pd.read_excel(caminho_planilha_base, usecols=COLUNAS_PARA_LER_DA_BASE).fillna('')
        elif file_ext == '.csv':
            try:
                df_base = pd.read_csv(caminho_planilha_base, usecols=COLUNAS_PARA_LER_DA_BASE, sep=';', encoding='utf-8-sig').fillna('')
            except (ValueError, UnicodeDecodeError):
                df_base = pd.read_csv(caminho_planilha_base, usecols=COLUNAS_PARA_LER_DA_BASE, sep=',', encoding='utf-8-sig').fillna('')
        else:
            raise ValueError("Formato de arquivo não suportado. Por favor, use .xlsx, .xls ou .csv.")
        
        df_base['chave_normalizada'] = df_base['Nome fantasia'].astype(str).str.strip().str.upper()
        df_base = df_base[df_base['chave_normalizada'] != '']
        df_base = df_base.set_index('chave_normalizada')
        log_messages.append("Dados locais carregados e normalizados com sucesso.")
        
        # ETAPA 2: Conectar ao Google Sheets
        log_messages.append("Autenticando com a API do Google...")
        
        # Verificar se estamos em produção (Render) ou desenvolvimento
        credentials_base64 = os.getenv('GOOGLE_CREDENTIALS_BASE64')
        
        if credentials_base64:
            # Produção: usar credenciais do Base64
            log_messages.append("Usando credenciais do ambiente de produção...")
            
            try:
                # Decodificar Base64 e criar arquivo temporário
                credentials_data = base64.b64decode(credentials_base64)
                
                # Criar arquivo temporário para as credenciais
                with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json', delete=False) as temp_file:
                    temp_file.write(credentials_data)
                    temp_credentials_path = temp_file.name
                
                # Usar arquivo temporário
                gc = gspread.service_account(filename=temp_credentials_path)
                
                # Limpar arquivo temporário
                os.unlink(temp_credentials_path)
                
            except Exception as e:
                log_messages.append(f"❌ Erro ao processar credenciais Base64: {str(e)}")
                raise
        else:
            # Desenvolvimento: usar arquivo local
            log_messages.append("Usando credenciais do arquivo local...")
            gc = gspread.service_account(filename=ARQUIVO_CREDENCIAIS)
        
        sh = gc.open(NOME_PLANILHA_GOOGLE)
        worksheet = sh.worksheet(NOME_ABA_GOOGLE)
        log_messages.append(f"Conectado à aba '{NOME_ABA_GOOGLE}'.")
        
        dados_dashboard = worksheet.get_all_values()
        if not dados_dashboard: raise ValueError("A planilha do Google Sheets está vazia.")
        
        cabecalhos = dados_dashboard[0]
        linhas_de_dados = dados_dashboard[1:]
        
        colunas_necessarias_dash = list(MAPA_COLUNAS_DIRETAS.values()) + [COLUNA_STATUS_DASH, COLUNA_CONTRATO_DASH]
        for col in colunas_necessarias_dash:
            if col not in cabecalhos:
                raise ValueError(f"Coluna '{col}' não encontrada no cabeçalho do Google Sheets.")
        
        indices_dashboard = {nome: cabecalhos.index(nome) for nome in cabecalhos}
        chave_imob_dash = MAPA_COLUNAS_DIRETAS['Nome fantasia']
        set_imobiliarias_dashboard = {str(linha[indices_dashboard[chave_imob_dash]]).strip().upper() for linha in linhas_de_dados if len(linha) > indices_dashboard[chave_imob_dash] and linha[indices_dashboard[chave_imob_dash]]}
        
        celulas_para_atualizar = []
        novas_linhas_para_adicionar = []

        # --- PASSO 1: ATUALIZAR REGISTROS EXISTENTES ---
        log_messages.append("\nIniciando Passo 1: Verificando atualizações...")
        for i, linha in enumerate(linhas_de_dados, start=2):
            if len(linha) <= indices_dashboard[chave_imob_dash] or not linha[indices_dashboard[chave_imob_dash]]: continue
            
            nome_original = linha[indices_dashboard[chave_imob_dash]]
            chave_normalizada = str(nome_original).strip().upper()
            
            if chave_normalizada in df_base.index:
                dados_base_linha = df_base.loc[chave_normalizada]
                if isinstance(dados_base_linha, pd.DataFrame): dados_base_linha = dados_base_linha.iloc[0]

                # 1.1 - Atualizações diretas
                for nome_base, nome_dash in MAPA_COLUNAS_DIRETAS.items():
                    if nome_base == 'Nome fantasia': continue
                    valor_novo, valor_antigo = dados_base_linha[nome_base], linha[indices_dashboard[nome_dash]]
                    if str(valor_novo) != str(valor_antigo):
                        # <--- MUDANÇA: Log detalhado da alteração de célula
                        log_messages.append(f"  [ATUALIZAÇÃO] '{nome_original}': Coluna '{nome_dash}' de '{valor_antigo}' para '{valor_novo}'.")
                        celulas_para_atualizar.append(gspread.Cell(i, indices_dashboard[nome_dash] + 1, str(valor_novo)))
                
                # 1.2 - Lógica condicional de status e contrato
                status_base = str(dados_base_linha[COLUNA_STATUS_BASE]).strip().upper()
                valor_antigo_status = linha[indices_dashboard[COLUNA_STATUS_DASH]]
                if str(dados_base_linha[COLUNA_STATUS_BASE]) != valor_antigo_status:
                    # <--- MUDANÇA: Log detalhado da alteração de status
                    log_messages.append(f"  [ATUALIZAÇÃO] '{nome_original}': Coluna '{COLUNA_STATUS_DASH}' de '{valor_antigo_status}' para '{dados_base_linha[COLUNA_STATUS_BASE]}'.")
                    celulas_para_atualizar.append(gspread.Cell(i, indices_dashboard[COLUNA_STATUS_DASH] + 1, str(dados_base_linha[COLUNA_STATUS_BASE])))

                valor_antigo_contrato = linha[indices_dashboard[COLUNA_CONTRATO_DASH]]
                if status_base == 'INATIVO':
                    if valor_antigo_contrato != 'Não Assinado':
                        # <--- MUDANÇA: Log detalhado da alteração de contrato
                        log_messages.append(f"  [ATUALIZAÇÃO] '{nome_original}': Coluna '{COLUNA_CONTRATO_DASH}' de '{valor_antigo_contrato}' para 'Não Assinado' (status INATIVO).")
                        celulas_para_atualizar.append(gspread.Cell(i, indices_dashboard[COLUNA_CONTRATO_DASH] + 1, 'Não Assinado'))
                elif status_base == 'ATIVO':
                    if valor_antigo_contrato != 'Assinado':
                        # <--- MUDANÇA: Log detalhado da alteração de contrato
                        log_messages.append(f"  [ATUALIZAÇÃO] '{nome_original}': Coluna '{COLUNA_CONTRATO_DASH}' de '{valor_antigo_contrato}' para 'Assinado' (status ATIVO).")
                        celulas_para_atualizar.append(gspread.Cell(i, indices_dashboard[COLUNA_CONTRATO_DASH] + 1, 'Assinado'))
                else:
                    if valor_antigo_contrato != 'Pendente':
                        # <--- MUDANÇA: Log detalhado da alteração de contrato
                        log_messages.append(f"  [ATUALIZAÇÃO] '{nome_original}': Coluna '{COLUNA_CONTRATO_DASH}' de '{valor_antigo_contrato}' para 'Pendente'.")
                        celulas_para_atualizar.append(gspread.Cell(i, indices_dashboard[COLUNA_CONTRATO_DASH] + 1, 'Pendente'))

        # --- PASSO 2: ADICIONAR NOVOS REGISTROS ---
        log_messages.append("\nIniciando Passo 2: Procurando novas imobiliárias...")
        chaves_ja_processadas = set()
        for chave_base, dados_base_linha in df_base.iterrows():
            if chave_base in chaves_ja_processadas: continue
            chaves_ja_processadas.add(chave_base)

            if chave_base not in set_imobiliarias_dashboard:
                if "(CARUARU)" in chave_base:
                    if isinstance(dados_base_linha, pd.DataFrame): dados_base_linha = dados_base_linha.iloc[0]
                    # <--- MUDANÇA: Log detalhado da nova adição
                    log_messages.append(f"  [NOVO] Imobiliária a ser adicionada: {dados_base_linha['Nome fantasia']} (Status: {dados_base_linha[COLUNA_STATUS_BASE]})")
                    
                    nova_linha = [''] * len(cabecalhos)
                    for nome_base, nome_dash in MAPA_COLUNAS_DIRETAS.items():
                        nova_linha[indices_dashboard[nome_dash]] = dados_base_linha[nome_base]
                    
                    status_base = str(dados_base_linha[COLUNA_STATUS_BASE]).strip().upper()
                    nova_linha[indices_dashboard[COLUNA_STATUS_DASH]] = dados_base_linha[COLUNA_STATUS_BASE]
                    
                    if status_base == 'INATIVO':
                        nova_linha[indices_dashboard[COLUNA_CONTRATO_DASH]] = 'Não Assinado'
                    elif status_base == 'ATIVO':
                        nova_linha[indices_dashboard[COLUNA_CONTRATO_DASH]] = 'Assinado'
                    else:
                        nova_linha[indices_dashboard[COLUNA_CONTRATO_DASH]] = 'Pendente'
                    
                    novas_linhas_para_adicionar.append(nova_linha)

        # --- PASSO 3: EXECUTAR ALTERAÇÕES ---
        if celulas_para_atualizar:
            log_messages.append(f"\nEnviando {len(celulas_para_atualizar)} atualizações de células...")
            worksheet.update_cells(celulas_para_atualizar, value_input_option='USER_ENTERED')
            log_messages.append("✅ Células atualizadas com sucesso!")
        else:
            log_messages.append("\nNenhuma célula precisou ser atualizada.")
            
        if novas_linhas_para_adicionar:
            log_messages.append(f"\nAdicionando {len(novas_linhas_para_adicionar)} novas linhas ao dashboard...")
            worksheet.append_rows(novas_linhas_para_adicionar, value_input_option='USER_ENTERED')
            log_messages.append("✅ Novas linhas adicionadas com sucesso!")
        else:
            log_messages.append("\nNenhuma nova imobiliária de Caruaru para adicionar.")
            
    except Exception as e:
        log_messages.append(f"\n❌ ERRO no processo: {e}")
        return "\n".join(log_messages)
    finally:
        log_messages.append("\nProcesso de sincronização finalizado.")

    return "\n".join(log_messages)