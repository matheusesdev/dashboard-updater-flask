from flask import Flask, render_template, request, jsonify, url_for
import os
from iniciar_processo import iniciar_processo_de_atualizacao
from dotenv import load_dotenv # Importa a função para carregar o .env

# --- CARREGAMENTO DAS VARIÁVEIS DE AMBIENTE ---
# Esta linha procura por um arquivo .env na pasta raiz e carrega
# as variáveis definidas nele para o ambiente do sistema operacional.
# É a primeira coisa a ser feita, antes da aplicação iniciar.
load_dotenv()

# --- INICIALIZAÇÃO DO FLASK ---
app = Flask(__name__)

# --- CONFIGURAÇÃO ---
# Configuração para servir arquivos estáticos em produção
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 ano cache
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
    Salva o arquivo, chama a lógica de backend e retorna o resultado.
    """
    # 1. Validação básica da requisição
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Nenhum arquivo foi incluído na requisição.'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Nenhum arquivo foi selecionado.'})

    # 2. Processamento do arquivo
    if file:
        # Cria um caminho seguro e salva o arquivo no servidor
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # 3. Execução da lógica de negócio
        try:
            # Chama a função principal do backend, passando o caminho do arquivo salvo
            log_output = iniciar_processo_de_atualizacao(filepath)
            
            # Retorna uma resposta JSON de sucesso com o log gerado
            return jsonify({'success': True, 'log': log_output})

        except Exception as e:
            # Em caso de qualquer erro inesperado, retorna uma mensagem JSON de erro
            return jsonify({'success': False, 'error': str(e)})

        finally:
            # 4. Limpeza: Garante que o arquivo enviado seja sempre deletado
            # após o uso, independentemente de sucesso ou falha.
            if os.path.exists(filepath):
                os.remove(filepath)

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