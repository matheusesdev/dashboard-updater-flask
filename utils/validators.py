"""
Validadores melhorados para upload de arquivos e segurança
"""
import os
import re
import mimetypes
from werkzeug.utils import secure_filename as werkzeug_secure_filename
from werkzeug.datastructures import FileStorage
from typing import Set

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

from exceptions.errors import (
    FileValidationError, FileSizeError, 
    FileTypeError, FileContentError, ValidationError
)


class FileValidator:
    """Validador robusto de arquivos para upload"""
    
    # Configurações de segurança
    ALLOWED_EXTENSIONS: Set[str] = {'.xlsx', '.xls', '.csv', '.ods'}
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
    MAX_FILENAME_LENGTH = 255
    
    # MIME types permitidos
    ALLOWED_MIME_TYPES = {
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
        'text/csv',  # .csv
        'application/csv',  # .csv (alternativo)
        'application/vnd.oasis.opendocument.spreadsheet',  # .ods
    }
    
    # Padrões perigosos em nomes de arquivo
    DANGEROUS_PATTERNS = [
        r'\.\./',  # Path traversal
        r'\\',     # Windows path separators
        r'[<>:"|?*]',  # Caracteres inválidos no Windows
        r'^\.',    # Arquivos ocultos
        r'\.exe$', r'\.bat$', r'\.cmd$', r'\.scr$',  # Executáveis
    ]
    
    def __init__(self, config=None):
        """Inicializa validador com configurações opcionais"""
        if config:
            self.ALLOWED_EXTENSIONS = getattr(config, 'ALLOWED_EXTENSIONS', self.ALLOWED_EXTENSIONS)
            self.MAX_FILE_SIZE = getattr(config, 'MAX_FILE_SIZE', self.MAX_FILE_SIZE)
    
    def validate_file(self, file: FileStorage) -> bool:
        """
        Valida arquivo de upload de forma robusta
        
        Args:
            file: Objeto FileStorage do Flask
            
        Returns:
            True se válido
            
        Raises:
            FileValidationError: Erro específico de validação
        """
        # 1. Verificar se arquivo existe
        if not file or not file.filename:
            raise FileValidationError("Nenhum arquivo foi fornecido")
        
        # 2. Validar nome do arquivo
        safe_filename = self._validate_filename(file.filename)
        
        # 3. Validar extensão
        self._validate_extension(safe_filename)
        
        # 4. Validar tamanho
        self._validate_size(file)
        
        # 5. Validar conteúdo (MIME type)
        self._validate_content(file)
        
        return True
    
    def _validate_filename(self, filename: str) -> str:
        """Valida e sanitiza nome do arquivo"""
        if not filename or filename.strip() == '':
            raise FileValidationError("Nome do arquivo não pode estar vazio")
        
        # Verificar comprimento
        if len(filename) > self.MAX_FILENAME_LENGTH:
            raise FileValidationError(f"Nome do arquivo muito longo (máximo {self.MAX_FILENAME_LENGTH} caracteres)")
        
        # Verificar padrões perigosos
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                raise FileValidationError(f"Nome do arquivo contém caracteres não permitidos")
        
        # Verificar nomes reservados do Windows
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in reserved_names:
            raise FileValidationError(f"Nome de arquivo reservado: {filename}")
        
        return filename
    
    def _validate_extension(self, filename: str) -> None:
        """Valida extensão do arquivo"""
        extension = os.path.splitext(filename)[1].lower()
        
        if not extension:
            raise FileTypeError("Arquivo deve ter uma extensão")
        
        if extension not in self.ALLOWED_EXTENSIONS:
            allowed = ', '.join(self.ALLOWED_EXTENSIONS)
            raise FileTypeError(f"Extensão '{extension}' não permitida. Permitidas: {allowed}")
    
    def _validate_size(self, file: FileStorage) -> None:
        """Valida tamanho do arquivo"""
        # Ir para o final do arquivo para obter o tamanho
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)  # Voltar ao início
        
        if size == 0:
            raise FileSizeError("Arquivo está vazio")
        
        if size > self.MAX_FILE_SIZE:
            size_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            raise FileSizeError(f"Arquivo muito grande. Máximo permitido: {size_mb:.1f}MB")
    
    def _validate_content(self, file: FileStorage) -> None:
        """Valida conteúdo do arquivo via MIME type"""
        # Ler uma pequena amostra para verificar o conteúdo
        file.seek(0)
        file_header = file.read(1024)
        file.seek(0)  # Voltar ao início
        
        # Tentar detectar MIME type
        mime_type = None
        
        if MAGIC_AVAILABLE:
            try:
                mime_type = magic.from_buffer(file_header, mime=True)
            except Exception:
                pass
        
        # Fallback para mimetypes do Python
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(file.filename)
        
        # Validar MIME type se detectado
        if mime_type and mime_type not in self.ALLOWED_MIME_TYPES:
            # Permitir alguns MIME types comuns para CSV
            csv_alternatives = {
                'text/plain', 'application/octet-stream'
            }
            
            # Se é CSV, ser mais flexível
            if file.filename.lower().endswith('.csv') and mime_type in csv_alternatives:
                return
            
            raise FileContentError(f"Tipo de arquivo não permitido: {mime_type}")
        
        # Verificações específicas por extensão
        extension = os.path.splitext(file.filename)[1].lower()
        
        if extension == '.csv':
            self._validate_csv_content(file_header)
        elif extension in ['.xlsx', '.xls']:
            self._validate_excel_content(file_header)
    
    def _validate_csv_content(self, header: bytes) -> None:
        """Validação específica para arquivos CSV"""
        try:
            # Tentar decodificar como texto
            text = header.decode('utf-8', errors='ignore')
            
            # Verificar se parece com CSV (tem vírgulas ou ponto-e-vírgula)
            if ',' not in text and ';' not in text and '\t' not in text:
                raise FileContentError("Arquivo CSV não parece ter delimitadores válidos")
                
        except Exception as e:
            raise FileContentError(f"Erro ao validar CSV: {str(e)}")
    
    def _validate_excel_content(self, header: bytes) -> None:
        """Validação específica para arquivos Excel"""
        # Verificar assinaturas de arquivo Excel
        excel_signatures = [
            b'PK\x03\x04',  # .xlsx (ZIP-based)
            b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',  # .xls (OLE2)
        ]
        
        for signature in excel_signatures:
            if header.startswith(signature):
                return
        
        raise FileContentError("Arquivo não parece ser um Excel válido")
    
    def secure_filename(self, filename: str) -> str:
        """
        Gera nome de arquivo seguro
        
        Args:
            filename: Nome original do arquivo
            
        Returns:
            Nome sanitizado e seguro
        """
        # Usar o secure_filename do Werkzeug como base
        safe_name = werkzeug_secure_filename(filename)
        
        # Verificações adicionais
        if not safe_name:
            safe_name = "file"
        
        # Garantir que tem extensão
        if '.' not in safe_name:
            original_ext = os.path.splitext(filename)[1]
            if original_ext:
                safe_name += original_ext.lower()
        
        # Adicionar timestamp se necessário para evitar conflitos
        import time
        timestamp = str(int(time.time()))
        name, ext = os.path.splitext(safe_name)
        
        return f"{name}_{timestamp}{ext}"
    
    @staticmethod
    def get_file_info(file: FileStorage) -> dict:
        """Obtém informações detalhadas do arquivo"""
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        info = {
            'filename': file.filename,
            'size': size,
            'size_mb': round(size / (1024 * 1024), 2),
            'extension': os.path.splitext(file.filename)[1].lower(),
            'content_type': file.content_type,
        }
        
        # Tentar detectar MIME type real
        if MAGIC_AVAILABLE:
            try:
                header = file.read(1024)
                file.seek(0)
                info['detected_mime'] = magic.from_buffer(header, mime=True)
            except Exception:
                pass
        
        return info


class InputValidator:
    """Validador para inputs gerais da aplicação"""
    
    @staticmethod
    def validate_string(value: str, min_length: int = 1, max_length: int = 1000) -> str:
        """Valida string de input"""
        if not isinstance(value, str):
            raise ValidationError("Valor deve ser uma string")
        
        value = value.strip()
        
        if len(value) < min_length:
            raise ValidationError(f"Valor muito curto (mínimo {min_length} caracteres)")
        
        if len(value) > max_length:
            raise ValidationError(f"Valor muito longo (máximo {max_length} caracteres)")
        
        return value
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """Remove HTML potencialmente perigoso"""
        import html
        return html.escape(value)
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Valida formato de email"""
        email = email.strip().lower()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            raise ValidationError("Formato de email inválido")
        
        return email
