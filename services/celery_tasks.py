"""
Tasks assíncronas usando Celery
"""
import os
import time
import logging
from typing import Dict, Any

try:
    from celery import Celery
    from celery.schedules import crontab
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    # Mock para quando Celery não estiver disponível
    class Celery:
        def __init__(self, *args, **kwargs):
            pass
        def task(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        @property
        def conf(self):
            return type('conf', (), {'update': lambda x: None, 'beat_schedule': {}})()

from services.file_processing_service import FileProcessingService
from config.config import Config


# Configurar Celery
celery = Celery('atualizador_web')
celery.conf.update(
    broker_url=Config.CELERY_BROKER_URL,
    result_backend=Config.CELERY_RESULT_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
)

logger = logging.getLogger(__name__)


@celery.task(bind=True)
def process_file_async(self, file_data: bytes, filename: str, metadata: Dict[str, Any] = None):
    """
    Processa arquivo de forma assíncrona
    
    Args:
        file_data: Dados do arquivo em bytes
        filename: Nome do arquivo
        metadata: Metadados adicionais
        
    Returns:
        Resultado do processamento
    """
    try:
        # Atualizar status da task
        self.update_state(state='PROGRESS', meta={'status': 'Iniciando processamento...'})
        
        # Criar serviço de processamento
        service = FileProcessingService(
            upload_folder=Config.UPLOAD_FOLDER,
            credentials_file=Config.CREDENTIALS_FILE
        )
        
        # Salvar arquivo temporário
        temp_filepath = os.path.join(Config.UPLOAD_FOLDER, f"temp_{self.request.id}_{filename}")
        
        with open(temp_filepath, 'wb') as f:
            f.write(file_data)
        
        self.update_state(state='PROGRESS', meta={'status': 'Arquivo salvo, iniciando processamento...'})
        
        # Simular FileStorage para o serviço
        class TempFile:
            def __init__(self, filepath, filename):
                self.filepath = filepath
                self.filename = filename
            
            def save(self, destination):
                import shutil
                shutil.move(self.filepath, destination)
        
        temp_file = TempFile(temp_filepath, filename)
        
        # Processar arquivo
        result = service.process_file(temp_file, metadata)
        
        self.update_state(state='PROGRESS', meta={'status': 'Processamento concluído!'})
        
        logger.info(f"Task {self.request.id} concluída com sucesso")
        return result
        
    except Exception as e:
        logger.error(f"Erro na task {self.request.id}: {str(e)}")
        
        # Limpar arquivo temporário em caso de erro
        if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        
        self.update_state(
            state='FAILURE',
            meta={'status': f'Erro: {str(e)}', 'error': str(e)}
        )
        raise


@celery.task
def cleanup_old_files():
    """
    Task periódica para limpeza de arquivos antigos
    """
    try:
        upload_folder = Config.UPLOAD_FOLDER
        if not os.path.exists(upload_folder):
            return {'status': 'success', 'message': 'Pasta de upload não existe'}
        
        import time
        current_time = time.time()
        cleaned_count = 0
        
        # Remover arquivos com mais de 1 hora
        for filename in os.listdir(upload_folder):
            filepath = os.path.join(upload_folder, filename)
            
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getctime(filepath)
                
                # Se arquivo tem mais de 1 hora (3600 segundos)
                if file_age > 3600:
                    os.remove(filepath)
                    cleaned_count += 1
                    logger.info(f"Arquivo removido: {filename}")
        
        logger.info(f"Limpeza concluída: {cleaned_count} arquivos removidos")
        return {
            'status': 'success',
            'cleaned_files': cleaned_count,
            'message': f'{cleaned_count} arquivos antigos removidos'
        }
        
    except Exception as e:
        logger.error(f"Erro na limpeza de arquivos: {str(e)}")
        return {'status': 'error', 'error': str(e)}


@celery.task
def health_check():
    """
    Task de health check para Celery
    """
    try:
        from services.google_sheets_service import GoogleSheetsService
        
        # Testar conexão com Google Sheets
        sheets_service = GoogleSheetsService(Config.CREDENTIALS_FILE)
        sheets_ok = sheets_service.test_connection()
        
        return {
            'status': 'healthy',
            'timestamp': time.time(),
            'google_sheets': 'ok' if sheets_ok else 'error',
            'worker_id': 'celery_worker'
        }
        
    except Exception as e:
        logger.error(f"Health check falhou: {str(e)}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }


# Configurar tasks periódicas
if CELERY_AVAILABLE:
    from celery.schedules import crontab
    
    celery.conf.beat_schedule = {
        'cleanup-old-files': {
            'task': 'services.celery_tasks.cleanup_old_files',
            'schedule': crontab(minute=0),  # A cada hora
        },
        'health-check': {
            'task': 'services.celery_tasks.health_check',
            'schedule': 30.0,  # A cada 30 segundos
        },
    }
