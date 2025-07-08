from flask import Flask, render_template, request, jsonify, url_for
import os
import logging
from datetime import datetime
from iniciar_processo import iniciar_processo_de_atualizacao
from dotenv import load_dotenv
from utils.validators import FileValidator, SecurityValidator, FileValidationError

# --- CARREGAMENTO DAS VARIÁVEIS DE AMBIENTE ---
# Esta linha procura por um arquivo .env na pasta raiz e carrega
# as variáveis definidas nele para o ambiente do sistema operacional.
# É a primeira coisa a ser feita, antes da aplicação iniciar.
load_dotenv()

# --- INICIALIZAÇÃO DO FLASK ---
app = Flask(__name__)

# --- CONFIGURAÇÃO DE LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÃO ---
# Configuração para servir arquivos estáticos em produção
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 ano cache
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB máximo

if os.environ.get('FLASK_ENV') == 'production':
    # Em produção, garantir que arquivos estáticos sejam servidos
    app.static_url_path = '/static'
    app.static_folder = 'static'

# Define uma pasta para onde os arquivos serão enviados temporariamente
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Garante que a pasta de uploads exista. Se não existir, ela é criada.
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --- ROTAS DA APLICAÇÃO ---

# Rota de Health Check
@app.route('/health')
def health_check():
    """
    Health check endpoint para monitoramento
    """
    try:
        # Verificações básicas de saúde
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'upload_folder_exists': os.path.exists(app.config['UPLOAD_FOLDER']),
            'upload_folder_writable': os.access(app.config['UPLOAD_FOLDER'], os.W_OK)
        }
        
        # Verificar se pasta de upload está acessível
        if not health_status['upload_folder_exists'] or not health_status['upload_folder_writable']:
            health_status['status'] = 'degraded'
            logger.warning("Upload folder não está acessível")
        
        # Verificar variáveis de ambiente críticas
        required_env_vars = ['GOOGLE_CREDENTIALS_BASE64', 'GOOGLE_SHEET_NAME']
        missing_vars = []
        
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            health_status['status'] = 'degraded'
            health_status['missing_env_vars'] = missing_vars
            logger.warning(f"Variáveis de ambiente ausentes: {missing_vars}")
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal health check error'
        }), 503

# Rota de métricas básicas
@app.route('/metrics')
def metrics():
    """
    Endpoint de métricas básicas
    """
    try:
        import psutil
        
        metrics_data = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
            },
            'application': {
                'upload_folder_size_mb': sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(app.config['UPLOAD_FOLDER'])
                    for filename in filenames
                ) / (1024 * 1024),
                'log_file_exists': os.path.exists('app.log')
            }
        }
        
        return jsonify(metrics_data)
        
    except ImportError:
        # psutil não instalado
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'error': 'psutil not installed - limited metrics available',
            'application': {
                'upload_folder_exists': os.path.exists(app.config['UPLOAD_FOLDER'])
            }
        })
    except Exception as e:
        logger.error(f"Erro ao obter métricas: {str(e)}")
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'error': 'Error retrieving metrics'
        }), 500

# Rota para teste de arquivos estáticos
@app.route('/test-static')
def test_static():
    """
    Rota de teste para verificar se arquivos estáticos estão acessíveis
    """
    import os
    static_files = []
    for file in os.listdir(app.static_folder):
        static_files.append({
            'name': file,
            'url': url_for('static', filename=file)
        })
    return jsonify({'static_files': static_files})

# Rota principal (página inicial): '/'
@app.route('/')
def index():
    """
    Renderiza e exibe a página principal (index.html) quando o usuário
    acessa a URL raiz do site.
    """
    return render_template('index.html')


# Rota para o upload de arquivos: '/upload'
@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Lida com a requisição de envio de arquivo (POST) do formulário.
    Implementa validações de segurança rigorosas.
    """
    start_time = datetime.now()
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    
    logger.info(f"Upload iniciado - IP: {client_ip}")
    
    try:
        # 1. Validação básica da requisição
        if 'file' not in request.files:
            logger.warning(f"Upload sem arquivo - IP: {client_ip}")
            return jsonify({
                'success': False, 
                'error': 'Nenhum arquivo foi incluído na requisição.'
            }), 400

        file = request.files['file']
        
        # 2. Validação de segurança do arquivo
        is_valid, error_msg, secure_name = FileValidator.validate_file(file, file.filename)
        
        if not is_valid:
            logger.warning(f"Arquivo inválido - {error_msg} - IP: {client_ip} - Arquivo: {file.filename}")
            return jsonify({
                'success': False, 
                'error': error_msg
            }), 400

        # 3. Processamento do arquivo
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_name)
        
        try:
            # Salvar arquivo com nome seguro
            file.save(filepath)
            logger.info(f"Arquivo salvo: {secure_name} - IP: {client_ip}")
            
            # 4. Validação adicional do conteúdo
            content_valid, content_error = SecurityValidator.validate_file_content(filepath)
            if not content_valid:
                logger.warning(f"Conteúdo inválido - {content_error} - IP: {client_ip}")
                return jsonify({
                    'success': False, 
                    'error': f'Arquivo corrompido ou inválido: {content_error}'
                }), 400

            # 5. Execução da lógica de negócio
            logger.info(f"Iniciando processamento - Arquivo: {secure_name} - IP: {client_ip}")
            log_output = iniciar_processo_de_atualizacao(filepath)
            
            # Log de sucesso
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Upload processado com sucesso em {duration:.2f}s - IP: {client_ip} - Arquivo: {secure_name}")
            
            return jsonify({
                'success': True, 
                'log': log_output,
                'filename': secure_name,
                'processing_time': f"{duration:.2f}s"
            })

        except FileValidationError as e:
            logger.error(f"Erro de validação - {str(e)} - IP: {client_ip}")
            return jsonify({
                'success': False, 
                'error': f'Erro de validação: {str(e)}'
            }), 400
            
        except Exception as e:
            # Log detalhado do erro
            logger.error(f"Erro no processamento - {str(e)} - IP: {client_ip} - Arquivo: {secure_name}", exc_info=True)
            return jsonify({
                'success': False, 
                'error': 'Erro interno no processamento do arquivo. Tente novamente.'
            }), 500

        finally:
            # 6. Limpeza: Garantir que o arquivo seja sempre deletado
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    logger.info(f"Arquivo temporário removido: {secure_name}")
                except Exception as e:
                    logger.error(f"Erro ao remover arquivo temporário: {secure_name} - {str(e)}")
                    
    except Exception as e:
        # Erro geral não capturado
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Erro crítico não tratado em {duration:.2f}s - IP: {client_ip} - {str(e)}", exc_info=True)
        return jsonify({
            'success': False, 
            'error': 'Erro interno do servidor. Contate o administrador.'
        }), 500

# --- PONTO DE ENTRADA DO PROGRAMA ---
# Este bloco só é executado quando você roda "python app.py" diretamente
if __name__ == '__main__':
    # Configurações para produção e desenvolvimento
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    # Inicia o servidor
    # host='0.0.0.0' permite que a aplicação seja acessada externamente
    # port vem da variável de ambiente (Render usa 10000)
    # debug=False em produção por segurança
    app.run(host='0.0.0.0', port=port, debug=debug)