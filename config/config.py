"""
Configuração centralizada da aplicação
"""
import os
from typing import Dict, Any


class Config:
    """Configuração base da aplicação"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Upload settings
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv', '.ods'}
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB per file
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 7200  # 2 hours
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_UPLOAD = "10 per minute"
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'app.log'
    
    # Celery (Background tasks)
    CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Google Sheets API
    CREDENTIALS_FILE = 'credentials.json'
    
    @staticmethod
    def init_app(app):
        """Initialize app with config"""
        pass


class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in dev


class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    # Override with environment variables for production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key'
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        handler = StreamHandler()
        handler.setLevel(logging.WARNING)
        app.logger.addHandler(handler)


class TestingConfig(Config):
    """Configuração para testes"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = 'test_uploads'


# Configurações disponíveis
config: Dict[str, Any] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
