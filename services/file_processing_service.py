"""
Serviço de processamento de arquivos
"""
import os
import logging
from typing import Dict, Any, Optional
from werkzeug.datastructures import FileStorage

from exceptions.errors import ProcessingError, GoogleSheetsError
from utils.validators import FileValidator
from .google_sheets_service import GoogleSheetsService


logger = logging.getLogger(__name__)


class FileProcessingService:
    """Serviço responsável pelo processamento de arquivos"""
    
    def __init__(self, upload_folder: str, credentials_file: str):
        self.upload_folder = upload_folder
        self.validator = FileValidator()
        self.sheets_service = GoogleSheetsService(credentials_file)
        
        # Criar pasta de upload se não existir
        os.makedirs(upload_folder, exist_ok=True)
    
    def process_file(self, file: FileStorage, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa um arquivo enviado
        
        Args:
            file: Arquivo enviado
            metadata: Metadados adicionais
            
        Returns:
            Resultado do processamento
            
        Raises:
            ProcessingError: Erro durante o processamento
        """
        try:
            # Validar arquivo
            self.validator.validate_file(file)
            
            # Salvar arquivo com nome seguro
            filename = self.validator.secure_filename(file.filename)
            filepath = os.path.join(self.upload_folder, filename)
            
            logger.info(f"Salvando arquivo: {filename}")
            file.save(filepath)
            
            # Processar arquivo baseado na extensão
            result = self._process_by_type(filepath, metadata or {})
            
            # Limpar arquivo após processamento
            self._cleanup_file(filepath)
            
            logger.info(f"Processamento concluído: {filename}")
            return {
                'status': 'success',
                'filename': filename,
                'result': result,
                'message': 'Arquivo processado com sucesso'
            }
            
        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}")
            if 'filepath' in locals():
                self._cleanup_file(filepath)
            raise ProcessingError(f"Erro no processamento: {str(e)}")
    
    def _process_by_type(self, filepath: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Processa arquivo baseado no tipo"""
        extension = os.path.splitext(filepath)[1].lower()
        
        if extension in ['.xlsx', '.xls', '.csv', '.ods']:
            return self._process_spreadsheet(filepath, metadata)
        else:
            raise ProcessingError(f"Tipo de arquivo não suportado: {extension}")
    
    def _process_spreadsheet(self, filepath: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Processa planilhas"""
        try:
            # Aqui você pode integrar com o código do iniciar_processo.py
            # Por enquanto, vamos fazer uma simulação
            logger.info(f"Processando planilha: {filepath}")
            
            # Simular upload para Google Sheets
            result = self.sheets_service.upload_file(filepath, metadata)
            
            return {
                'type': 'spreadsheet',
                'sheets_url': result.get('url'),
                'processed_rows': result.get('rows', 0)
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar planilha: {str(e)}")
            raise GoogleSheetsError(f"Erro no Google Sheets: {str(e)}")
    
    def _cleanup_file(self, filepath: str) -> None:
        """Remove arquivo após processamento"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.debug(f"Arquivo removido: {filepath}")
        except Exception as e:
            logger.warning(f"Erro ao remover arquivo {filepath}: {str(e)}")
    
    def get_processing_status(self, task_id: str) -> Dict[str, Any]:
        """Obtém status de processamento (para tasks assíncronas)"""
        # Implementar quando adicionar Celery
        return {'status': 'not_implemented'}
