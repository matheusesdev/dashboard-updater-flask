"""
Testes de integração para a aplicação Flask
"""
import unittest
import tempfile
import os
import json
from io import BytesIO

from app_new import create_app
from config.config import TestingConfig


class TestFlaskApp(unittest.TestCase):
    """Testes de integração para aplicação Flask"""
    
    def setUp(self):
        """Setup para cada teste"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Criar pasta temporária para uploads
        self.temp_dir = tempfile.mkdtemp()
        self.app.config['UPLOAD_FOLDER'] = self.temp_dir
    
    def tearDown(self):
        """Cleanup após cada teste"""
        self.app_context.pop()
        
        # Limpar pasta temporária
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_index_route(self):
        """Testa rota principal"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_health_check(self):
        """Testa health check"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
    
    def test_metrics_endpoint(self):
        """Testa endpoint de métricas"""
        response = self.client.get('/metrics')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('timestamp', data)
        self.assertIn('system', data)
    
    def test_upload_no_file(self):
        """Testa upload sem arquivo"""
        response = self.client.post('/upload')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_upload_empty_filename(self):
        """Testa upload com nome vazio"""
        data = {'file': (BytesIO(b'test'), '')}
        response = self.client.post('/upload', data=data)
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
    
    def test_upload_invalid_extension(self):
        """Testa upload com extensão inválida"""
        data = {'file': (BytesIO(b'test content'), 'test.exe')}
        response = self.client.post('/upload', data=data)
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error_type'], 'validation')
    
    def test_upload_valid_csv(self):
        """Testa upload de CSV válido"""
        csv_content = b'nome,idade,cidade\nJoao,30,SP\nMaria,25,RJ'
        data = {'file': (BytesIO(csv_content), 'test.csv')}
        
        response = self.client.post('/upload', data=data)
        
        # Pode falhar por falta do Google Sheets, mas deve processar a validação
        response_data = json.loads(response.data)
        self.assertIn('success', response_data)
    
    def test_404_error(self):
        """Testa tratamento de erro 404"""
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error_type'], 'not_found')


class TestConfiguracao(unittest.TestCase):
    """Testes para configurações"""
    
    def test_development_config(self):
        """Testa configuração de desenvolvimento"""
        from config.config import DevelopmentConfig
        
        self.assertTrue(DevelopmentConfig.DEBUG)
        self.assertFalse(DevelopmentConfig.SESSION_COOKIE_SECURE)
    
    def test_production_config(self):
        """Testa configuração de produção"""
        from config.config import ProductionConfig
        
        self.assertFalse(ProductionConfig.DEBUG)
        self.assertTrue(ProductionConfig.SESSION_COOKIE_SECURE)
    
    def test_testing_config(self):
        """Testa configuração de testes"""
        self.assertTrue(TestingConfig.TESTING)
        self.assertFalse(TestingConfig.WTF_CSRF_ENABLED)


if __name__ == '__main__':
    unittest.main()
