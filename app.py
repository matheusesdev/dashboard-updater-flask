"""
Aplicação Flask refatorada com arquitetura modular
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, url_for
from werkzeug.exceptions import RequestEntityTooLarge
from dotenv import load_dotenv

# Configurações e módulos locais
from config.config import config
from exceptions.errors import AppError, ValidationError, ProcessingError
from services.file_processing_service import FileProcessingService
from services.celery_tasks import process_file_async, CELERY_AVAILABLE
from utils.validators import FileValidator

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging estruturado
try:
    import structlog
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )
    logger = structlog.get_logger(__name__)
    STRUCTLOG_AVAILABLE = True
except ImportError:
    # Fallback para logging padrão se structlog não estiver disponível
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    STRUCTLOG_AVAILABLE = False


def create_app(config_name='default'):
    """Factory function para criar a aplicação Flask"""
    
    app = Flask(__name__)
    
    # Carregar configuração
    config_class = config.get(config_name, config['default'])
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    # Inicializar extensões
    init_extensions(app)
    
    # Registrar blueprints/rotas
    register_routes(app)
    
    # Registrar error handlers
    register_error_handlers(app)
    
    # Setup de logging
    setup_logging(app)
    
    logger.info("Aplicação inicializada", config=config_name)
    
    return app


def init_extensions(app):
    """Inicializa extensões da aplicação"""
    
    # Flask-Limiter para rate limiting
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=[app.config.get('RATELIMIT_DEFAULT', "100 per hour")]
        )
        app.limiter = limiter
        logger.info("Rate limiting configurado")
    except ImportError:
        logger.warning("Flask-Limiter não disponível, rate limiting desabilitado")
        app.limiter = None
    
    # Flask-WTF para CSRF protection
    try:
        from flask_wtf.csrf import CSRFProtect
        if app.config.get('WTF_CSRF_ENABLED', True):
            csrf = CSRFProtect(app)
            app.csrf = csrf
            logger.info("CSRF protection ativado")
    except ImportError:
        logger.warning("Flask-WTF não disponível, CSRF protection desabilitado")
        app.csrf = None
    
    # Celery para background tasks
    if CELERY_AVAILABLE:
        from services.celery_tasks import celery
        celery.conf.update(app.config)
        app.celery = celery
        logger.info("Celery configurado para background tasks")
    else:
        logger.warning("Celery não disponível, tasks executarão sincronamente")
        app.celery = None
    
    # Criar pasta de uploads
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Inicializar serviços
    app.file_service = FileProcessingService(
        upload_folder=upload_folder,
        credentials_file=app.config.get('CREDENTIALS_FILE', 'credentials.json')
    )
    
    app.file_validator = FileValidator(app.config)


def register_routes(app):
    """Registra rotas da aplicação"""
    
    @app.route('/')
    def index():
        """Página principal"""
        return render_template('index.html')
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        """Upload e processamento de arquivo"""
        try:
            # Rate limiting específico para upload
            if app.limiter:
                from flask_limiter.util import get_remote_address
                rate_limit = app.config.get('RATELIMIT_UPLOAD', "10 per minute")
                
            # Verificar se arquivo foi enviado
            if 'file' not in request.files:
                raise ValidationError("Nenhum arquivo foi enviado")
            
            file = request.files['file']
            
            if file.filename == '':
                raise ValidationError("Nenhum arquivo foi selecionado")
            
            # Validar arquivo
            app.file_validator.validate_file(file)
            
            # Obter metadados
            metadata = {
                'uploaded_at': datetime.now().isoformat(),
                'user_ip': request.remote_addr,
                'user_agent': request.user_agent.string,
                'file_info': app.file_validator.get_file_info(file)
            }
            
            # Processar baseado na disponibilidade do Celery
            if app.celery and request.form.get('async', 'false').lower() == 'true':
                # Processamento assíncrono
                file_data = file.read()
                file.seek(0)
                
                task = process_file_async.delay(
                    file_data=file_data,
                    filename=file.filename,
                    metadata=metadata
                )
                
                logger.info("Arquivo enviado para processamento assíncrono", 
                           task_id=task.id, filename=file.filename)
                
                return jsonify({
                    'success': True,
                    'message': 'Arquivo enviado para processamento',
                    'task_id': task.id,
                    'async': True
                })
            else:
                # Processamento síncrono
                result = app.file_service.process_file(file, metadata)
                
                logger.info("Arquivo processado com sucesso", 
                           filename=file.filename, result=result)
                
                return jsonify({
                    'success': True,
                    'message': 'Arquivo processado com sucesso',
                    'result': result,
                    'async': False
                })
        
        except ValidationError as e:
            logger.warning("Erro de validação no upload", error=str(e))
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': 'validation'
            }), 400
        
        except ProcessingError as e:
            logger.error("Erro de processamento", error=str(e))
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': 'processing'
            }), 500
        
        except Exception as e:
            logger.error("Erro inesperado no upload", error=str(e), exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor',
                'error_type': 'internal'
            }), 500
    
    @app.route('/status/<task_id>')
    def get_task_status(task_id):
        """Obtém status de uma task assíncrona"""
        if not app.celery:
            return jsonify({
                'error': 'Background tasks não disponíveis'
            }), 404
        
        try:
            from services.celery_tasks import celery
            task = celery.AsyncResult(task_id)
            
            response = {
                'task_id': task_id,
                'state': task.state,
                'ready': task.ready()
            }
            
            if task.state == 'PENDING':
                response['status'] = 'Aguardando processamento...'
            elif task.state == 'PROGRESS':
                response['status'] = task.info.get('status', 'Processando...')
                response['progress'] = task.info
            elif task.state == 'SUCCESS':
                response['status'] = 'Concluído'
                response['result'] = task.result
            else:  # FAILURE
                response['status'] = 'Erro no processamento'
                response['error'] = str(task.info)
            
            return jsonify(response)
        
        except Exception as e:
            logger.error("Erro ao obter status da task", task_id=task_id, error=str(e))
            return jsonify({
                'error': 'Erro ao obter status'
            }), 500
    
    @app.route('/health')
    def health_check():
        """Health check da aplicação"""
        try:
            # Informações básicas do sistema
            health_info = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'environment': app.config.get('ENV', 'unknown')
            }
            
            # Tentar obter informações do sistema se psutil estiver disponível
            try:
                import psutil
                health_info['system'] = {
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
                }
            except ImportError:
                health_info['system'] = {'status': 'metrics_unavailable'}
            
            # Verificar serviços
            services = {}
            
            # Verificar Google Sheets
            try:
                sheets_ok = app.file_service.sheets_service.test_connection()
                services['google_sheets'] = 'healthy' if sheets_ok else 'unhealthy'
            except Exception:
                services['google_sheets'] = 'error'
            
            # Verificar Celery
            if app.celery:
                try:
                    # Tentar inspecionar workers
                    from services.celery_tasks import celery
                    inspect = celery.control.inspect()
                    active_workers = inspect.active()
                    services['celery'] = 'healthy' if active_workers else 'no_workers'
                except Exception:
                    services['celery'] = 'error'
            else:
                services['celery'] = 'disabled'
            
            health_info['services'] = services
            
            # Determinar status geral
            unhealthy_services = [k for k, v in services.items() if v in ['unhealthy', 'error']]
            if unhealthy_services:
                health_info['status'] = 'degraded'
                health_info['issues'] = unhealthy_services
            
            return jsonify(health_info)
        
        except Exception as e:
            logger.error("Erro no health check", error=str(e))
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/metrics')
    def metrics():
        """Métricas básicas da aplicação"""
        try:
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'application': {
                    'upload_folder_size': get_folder_size(app.config.get('UPLOAD_FOLDER', 'uploads')),
                    'config_name': app.config.get('ENV', 'unknown')
                }
            }
            
            # Tentar obter métricas do sistema se psutil estiver disponível
            try:
                import psutil
                metrics_data['system'] = {
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory': {
                        'percent': psutil.virtual_memory().percent,
                        'used_gb': round(psutil.virtual_memory().used / (1024**3), 2),
                        'total_gb': round(psutil.virtual_memory().total / (1024**3), 2)
                    },
                    'disk': {
                        'percent': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
                        'free_gb': round(psutil.disk_usage('/').free / (1024**3), 2) if os.name != 'nt' else round(psutil.disk_usage('C:').free / (1024**3), 2)
                    }
                }
            except ImportError:
                metrics_data['system'] = {'status': 'psutil_not_available'}
            
            # Métricas do Celery se disponível
            if app.celery:
                try:
                    from services.celery_tasks import celery
                    inspect = celery.control.inspect()
                    stats = inspect.stats()
                    metrics_data['celery'] = {
                        'workers': len(stats) if stats else 0,
                        'active_tasks': sum(len(tasks) for tasks in inspect.active().values()) if inspect.active() else 0
                    }
                except Exception:
                    metrics_data['celery'] = {'error': 'Unable to get stats'}
            
            return jsonify(metrics_data)
        
        except Exception as e:
            logger.error("Erro ao obter métricas", error=str(e))
            return jsonify({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500


def register_error_handlers(app):
    """Registra handlers de erro"""
    
    @app.errorhandler(AppError)
    def handle_app_error(error):
        logger.warning("App error", error=str(error), status_code=error.status_code)
        return jsonify({
            'success': False,
            'error': error.message,
            'error_type': 'application'
        }), error.status_code
    
    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(error):
        logger.warning("File too large", max_size=app.config.get('MAX_CONTENT_LENGTH'))
        return jsonify({
            'success': False,
            'error': 'Arquivo muito grande',
            'error_type': 'file_size'
        }), 413
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error("Internal server error", error=str(error), exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'error_type': 'internal'
        }), 500
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({
            'success': False,
            'error': 'Endpoint não encontrado',
            'error_type': 'not_found'
        }), 404


def setup_logging(app):
    """Configura logging da aplicação"""
    if not app.debug:
        # Em produção, log para arquivo
        import logging
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            app.config.get('LOG_FILE', 'app.log'),
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Aplicação iniciada')


def get_folder_size(folder_path):
    """Calcula tamanho de uma pasta em MB"""
    try:
        if not os.path.exists(folder_path):
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        
        return round(total_size / (1024 * 1024), 2)  # MB
    except Exception:
        return 0


# Criar aplicação
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Configuração para desenvolvimento
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 5000))
    
    logger.info("Iniciando servidor", debug=debug_mode, port=port)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        threaded=True
    )
