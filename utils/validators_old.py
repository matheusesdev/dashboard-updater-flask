"""
Validadores para upload de arquivos e segurança
"""
import os
import re
import mimetypes
from werkzeug.utils import secure_filename as werkzeug_secure_filename
from werkzeug.datastructures import FileStorage
from typing import Tuple, Optional, Set

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

from exceptions.errors import (
    FileValidationError, FileSizeError, 
    FileTypeError, FileContentError
)


class FileValidator:
    """Validador de arquivos para upload"""
    
    # Configurações de segurança
    ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    MAX_FILENAME_LENGTH = 255
    
    @classmethod
    def validate_file(cls, file, filename: str) -> Tuple[bool, Optional[str], str]:
        """
        Valida um arquivo de upload
        
        Args:
            file: Objeto de arquivo do Flask
            filename: Nome do arquivo
            
        Returns:
            Tuple[bool, Optional[str], str]: (válido, erro_msg, nome_seguro)
        """
        try:
            # 1. Validar se arquivo foi fornecido
            if not file or not filename:
                raise FileValidationError("Nenhum arquivo foi fornecido")
            
            # 2. Verificar nome vazio
            if filename == '':
                raise FileValidationError("Nome do arquivo está vazio")
            
            # 3. Validar extensão
            if not cls._is_allowed_extension(filename):
                allowed = ', '.join(cls.ALLOWED_EXTENSIONS)
                raise FileTypeError(f"Tipo de arquivo não permitido. Aceitos: {allowed}")
            
            # 4. Validar tamanho do arquivo
            if not cls._is_valid_size(file):
                max_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
                raise FileSizeError(f"Arquivo muito grande. Máximo: {max_mb}MB")
            
            # 5. Validar tamanho do nome
            if len(filename) > cls.MAX_FILENAME_LENGTH:
                raise FileValidationError(f"Nome do arquivo muito longo. Máximo: {cls.MAX_FILENAME_LENGTH} caracteres")
            
            # 6. Criar nome seguro
            secure_name = secure_filename(filename)
            if not secure_name:
                raise FileValidationError("Nome do arquivo inválido após sanitização")
            
            return True, None, secure_name
            
        except FileValidationError as e:
            return False, str(e), filename
    
    @classmethod
    def _is_allowed_extension(cls, filename: str) -> bool:
        """Verifica se a extensão do arquivo é permitida"""
        if '.' not in filename:
            return False
        
        extension = '.' + filename.rsplit('.', 1)[1].lower()
        return extension in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def _is_valid_size(cls, file) -> bool:
        """Verifica se o tamanho do arquivo está dentro do limite"""
        # Salvar posição atual
        current_position = file.tell()
        
        # Ir para o final para obter tamanho
        file.seek(0, os.SEEK_END)
        size = file.tell()
        
        # Voltar para posição original
        file.seek(current_position)
        
        return size <= cls.MAX_FILE_SIZE


class SecurityValidator:
    """Validador de segurança geral"""
    
    @staticmethod
    def validate_file_content(filepath: str) -> Tuple[bool, Optional[str]]:
        """
        Validação básica do conteúdo do arquivo
        
        Args:
            filepath: Caminho para o arquivo
            
        Returns:
            Tuple[bool, Optional[str]]: (válido, erro_msg)
        """
        try:
            # Verificar se arquivo existe
            if not os.path.exists(filepath):
                return False, "Arquivo não encontrado"
            
            # Verificar se é realmente um arquivo
            if not os.path.isfile(filepath):
                return False, "Caminho não aponta para um arquivo válido"
            
            # Verificação básica de conteúdo por extensão
            ext = os.path.splitext(filepath)[1].lower()
            
            if ext in ['.xlsx', '.xls']:
                return SecurityValidator._validate_excel_content(filepath)
            elif ext == '.csv':
                return SecurityValidator._validate_csv_content(filepath)
            
            return True, None
            
        except Exception as e:
            return False, f"Erro na validação de conteúdo: {str(e)}"
    
    @staticmethod
    def _validate_excel_content(filepath: str) -> Tuple[bool, Optional[str]]:
        """Validação básica de arquivo Excel"""
        try:
            import pandas as pd
            
            # Tentar ler apenas o cabeçalho para verificar se é um Excel válido
            pd.read_excel(filepath, nrows=1)
            return True, None
            
        except Exception as e:
            return False, f"Arquivo Excel inválido: {str(e)}"
    
    @staticmethod
    def _validate_csv_content(filepath: str) -> Tuple[bool, Optional[str]]:
        """Validação básica de arquivo CSV"""
        try:
            import pandas as pd
            
            # Tentar ler apenas o cabeçalho para verificar se é um CSV válido
            pd.read_csv(filepath, nrows=1, encoding='utf-8-sig')
            return True, None
            
        except Exception as e:
            # Tentar com encoding diferente
            try:
                pd.read_csv(filepath, nrows=1, encoding='latin-1')
                return True, None
            except:
                return False, f"Arquivo CSV inválido: {str(e)}"
