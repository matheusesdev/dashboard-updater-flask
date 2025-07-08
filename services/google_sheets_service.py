"""
Serviço do Google Sheets
"""
import os
import logging
from typing import Dict, Any, Optional
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

from exceptions.errors import GoogleSheetsError


logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """Serviço para integração com Google Sheets"""
    
    def __init__(self, credentials_file: str):
        self.credentials_file = credentials_file
        self._client = None
    
    @property
    def client(self):
        """Cliente do Google Sheets (lazy loading)"""
        if self._client is None:
            self._client = self._create_client()
        return self._client
    
    def _create_client(self):
        """Cria cliente do Google Sheets"""
        try:
            if not os.path.exists(self.credentials_file):
                raise GoogleSheetsError(f"Arquivo de credenciais não encontrado: {self.credentials_file}")
            
            # Escopo necessário para Google Sheets
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets'
            ]
            
            credentials = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=scope
            )
            
            return gspread.authorize(credentials)
            
        except Exception as e:
            logger.error(f"Erro ao criar cliente Google Sheets: {str(e)}")
            raise GoogleSheetsError(f"Erro na autenticação: {str(e)}")
    
    def upload_file(self, filepath: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Faz upload de arquivo para Google Sheets
        
        Args:
            filepath: Caminho do arquivo
            metadata: Metadados adicionais
            
        Returns:
            Informações do upload
            
        Raises:
            GoogleSheetsError: Erro durante o upload
        """
        try:
            # Ler arquivo baseado na extensão
            extension = os.path.splitext(filepath)[1].lower()
            
            if extension in ['.xlsx', '.xls']:
                df = pd.read_excel(filepath)
            elif extension == '.csv':
                df = pd.read_csv(filepath)
            elif extension == '.ods':
                df = pd.read_excel(filepath, engine='odf')
            else:
                raise GoogleSheetsError(f"Extensão não suportada: {extension}")
            
            # Nome da planilha baseado no arquivo e timestamp
            sheet_name = metadata.get('sheet_name', os.path.splitext(os.path.basename(filepath))[0])
            
            # Criar ou abrir planilha
            spreadsheet = self._get_or_create_spreadsheet(sheet_name)
            
            # Adicionar dados
            worksheet = spreadsheet.sheet1
            worksheet.clear()  # Limpar dados existentes
            
            # Converter DataFrame para lista de listas
            data = [df.columns.tolist()] + df.values.tolist()
            
            # Upload dos dados
            worksheet.update('A1', data)
            
            logger.info(f"Upload concluído: {sheet_name}, {len(df)} linhas")
            
            return {
                'url': spreadsheet.url,
                'sheet_name': sheet_name,
                'rows': len(df),
                'columns': len(df.columns)
            }
            
        except Exception as e:
            logger.error(f"Erro no upload para Google Sheets: {str(e)}")
            raise GoogleSheetsError(f"Erro no upload: {str(e)}")
    
    def _get_or_create_spreadsheet(self, name: str):
        """Obtém ou cria uma planilha"""
        try:
            # Tentar abrir planilha existente
            try:
                return self.client.open(name)
            except gspread.SpreadsheetNotFound:
                # Criar nova planilha
                logger.info(f"Criando nova planilha: {name}")
                return self.client.create(name)
                
        except Exception as e:
            logger.error(f"Erro ao obter/criar planilha: {str(e)}")
            raise GoogleSheetsError(f"Erro na planilha: {str(e)}")
    
    def get_spreadsheet_info(self, spreadsheet_id: str) -> Dict[str, Any]:
        """Obtém informações de uma planilha"""
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheets = spreadsheet.worksheets()
            
            return {
                'title': spreadsheet.title,
                'url': spreadsheet.url,
                'worksheets': [
                    {
                        'title': ws.title,
                        'rows': ws.row_count,
                        'cols': ws.col_count
                    }
                    for ws in worksheets
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter info da planilha: {str(e)}")
            raise GoogleSheetsError(f"Erro ao acessar planilha: {str(e)}")
    
    def test_connection(self) -> bool:
        """Testa conexão com Google Sheets"""
        try:
            # Tentar listar planilhas (operação simples)
            self.client.list_permissions()
            logger.info("Conexão com Google Sheets OK")
            return True
            
        except Exception as e:
            logger.error(f"Erro na conexão com Google Sheets: {str(e)}")
            return False
