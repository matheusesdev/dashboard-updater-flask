"""
Testes unitários para validadores
"""
import unittest
import io
from werkzeug.datastructures import FileStorage

from utils.validators import FileValidator
from exceptions.errors import FileValidationError, FileSizeError, FileTypeError


class TestFileValidator(unittest.TestCase):
    """Testes para FileValidator"""
    
    def setUp(self):
        """Setup para cada teste"""
        self.validator = FileValidator()
    
    def create_test_file(self, filename: str, content: bytes = b'test content') -> FileStorage:
        """Cria arquivo de teste"""
        return FileStorage(
            stream=io.BytesIO(content),
            filename=filename,
            content_type='application/octet-stream'
        )
    
    def test_validate_valid_excel_file(self):
        """Testa validação de arquivo Excel válido"""
        # Simular cabeçalho Excel (.xlsx)
        excel_header = b'PK\x03\x04' + b'0' * 100
        file = self.create_test_file('test.xlsx', excel_header)
        
        try:
            result = self.validator.validate_file(file)
            self.assertTrue(result)
        except Exception as e:
            self.fail(f"Validação falhou inesperadamente: {e}")
    
    def test_validate_valid_csv_file(self):
        """Testa validação de arquivo CSV válido"""
        csv_content = b'nome,idade,cidade\nJoao,30,SP\nMaria,25,RJ'
        file = self.create_test_file('test.csv', csv_content)
        
        try:
            result = self.validator.validate_file(file)
            self.assertTrue(result)
        except Exception as e:
            self.fail(f"Validação falhou inesperadamente: {e}")
    
    def test_validate_empty_filename(self):
        """Testa validação com nome vazio"""
        file = self.create_test_file('')
        
        with self.assertRaises(FileValidationError):
            self.validator.validate_file(file)
    
    def test_validate_invalid_extension(self):
        """Testa validação com extensão inválida"""
        file = self.create_test_file('test.exe')
        
        with self.assertRaises(FileTypeError):
            self.validator.validate_file(file)
    
    def test_validate_large_file(self):
        """Testa validação de arquivo muito grande"""
        # Criar arquivo simulando tamanho muito grande
        large_content = b'0' * (self.validator.MAX_FILE_SIZE + 1)
        file = self.create_test_file('test.xlsx', large_content)
        
        with self.assertRaises(FileSizeError):
            self.validator.validate_file(file)
    
    def test_validate_empty_file(self):
        """Testa validação de arquivo vazio"""
        file = self.create_test_file('test.xlsx', b'')
        
        with self.assertRaises(FileSizeError):
            self.validator.validate_file(file)
    
    def test_secure_filename(self):
        """Testa geração de nome seguro"""
        dangerous_name = "../../../etc/passwd"
        safe_name = self.validator.secure_filename(dangerous_name)
        
        self.assertNotIn('..', safe_name)
        self.assertNotIn('/', safe_name)
        self.assertNotIn('\\', safe_name)
    
    def test_get_file_info(self):
        """Testa obtenção de informações do arquivo"""
        content = b'test content for info'
        file = self.create_test_file('test.xlsx', content)
        
        info = self.validator.get_file_info(file)
        
        self.assertEqual(info['filename'], 'test.xlsx')
        self.assertEqual(info['size'], len(content))
        self.assertEqual(info['extension'], '.xlsx')
        self.assertIn('size_mb', info)


class TestInputValidator(unittest.TestCase):
    """Testes para InputValidator"""
    
    def test_validate_string_normal(self):
        """Testa validação de string normal"""
        from utils.validators import InputValidator
        
        result = InputValidator.validate_string("  test string  ")
        self.assertEqual(result, "test string")
    
    def test_validate_string_too_short(self):
        """Testa string muito curta"""
        from utils.validators import InputValidator
        from exceptions.errors import ValidationError
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_string("", min_length=5)
    
    def test_validate_string_too_long(self):
        """Testa string muito longa"""
        from utils.validators import InputValidator
        from exceptions.errors import ValidationError
        
        long_string = "a" * 1001
        with self.assertRaises(ValidationError):
            InputValidator.validate_string(long_string, max_length=1000)
    
    def test_sanitize_html(self):
        """Testa sanitização de HTML"""
        from utils.validators import InputValidator
        
        html_input = "<script>alert('xss')</script>Hello"
        sanitized = InputValidator.sanitize_html(html_input)
        
        self.assertNotIn('<script>', sanitized)
        self.assertIn('Hello', sanitized)
    
    def test_validate_email_valid(self):
        """Testa validação de email válido"""
        from utils.validators import InputValidator
        
        valid_emails = [
            "test@example.com",
            "user.name+tag@domain.co.uk",
            "test123@test-domain.org"
        ]
        
        for email in valid_emails:
            result = InputValidator.validate_email(email)
            self.assertEqual(result, email.lower().strip())
    
    def test_validate_email_invalid(self):
        """Testa validação de email inválido"""
        from utils.validators import InputValidator
        from exceptions.errors import ValidationError
        
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "test@",
            "test..test@domain.com",
            ""
        ]
        
        for email in invalid_emails:
            with self.assertRaises(ValidationError):
                InputValidator.validate_email(email)


if __name__ == '__main__':
    unittest.main()
