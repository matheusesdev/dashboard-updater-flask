"""
Exceções customizadas da aplicação
"""


class AppError(Exception):
    """Exceção base da aplicação"""
    status_code = 500
    
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(AppError):
    """Erro de validação"""
    status_code = 400


class FileValidationError(ValidationError):
    """Erro de validação de arquivo"""
    pass


class FileSizeError(FileValidationError):
    """Arquivo muito grande"""
    pass


class FileTypeError(FileValidationError):
    """Tipo de arquivo não permitido"""
    pass


class FileContentError(FileValidationError):
    """Conteúdo do arquivo inválido"""
    pass


class ProcessingError(AppError):
    """Erro durante processamento"""
    status_code = 500


class GoogleSheetsError(ProcessingError):
    """Erro relacionado ao Google Sheets"""
    pass


class RateLimitError(AppError):
    """Limite de taxa excedido"""
    status_code = 429
