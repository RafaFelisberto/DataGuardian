from cryptography.fernet import Fernet, InvalidToken
import os
import logging
import pandas as pd

# Configuração de logging
logging.basicConfig(level=logging.INFO)

class DataEncryptor:
    def __init__(self, key_path="encryption_key.key", use_env_key=False):
        """
        Inicializa o criptografador com opção de usar chave do ambiente
        """
        self.key_path = key_path
        self.use_env_key = use_env_key
        self.key = self._load_key()
        self.cipher = Fernet(self.key)

    def _load_key(self):
        """Carrega a chave de criptografia de diferentes fontes"""
        if self.use_env_key:
            env_key = os.getenv("DATAGUARDIAN_ENCRYPTION_KEY")
            if env_key:
                return env_key.encode()
            else:
                raise ValueError("Chave de criptografia não encontrada nas variáveis de ambiente")
        
        if not os.path.exists(self.key_path):
            self.generate_key()
        
        try:
            with open(self.key_path, "rb") as key_file:
                return key_file.read()
        except Exception as e:
            logging.error(f"Erro ao carregar chave: {e}")
            raise

    def generate_key(self):
        """Gera uma nova chave e salva em disco"""
        try:
            key = Fernet.generate_key()
            with open(self.key_path, "wb") as key_file:
                key_file.write(key)
            os.chmod(self.key_path, 0o600)  # Limita permissões do arquivo
            logging.info("Nova chave de criptografia gerada")
        except Exception as e:
            logging.error(f"Erro ao gerar chave: {e}")
            raise

    def encrypt_value(self, value):
        """Criptografa um único valor com tratamento de erros"""
        if pd.isnull(value):
            return value
            
        try:
            # Garante que o valor é string antes da criptografia
            str_value = str(value)
            return self.cipher.encrypt(str_value.encode()).decode()
        except InvalidToken as e:
            logging.error(f"Erro de criptografia: Token inválido - {e}")
        except Exception as e:
            logging.error(f"Erro de criptografia: {e}")
        return value  # Retorna valor original em caso de falha

    def encrypt_column(self, df, column):
        """Criptografa uma coluna do DataFrame sem modificar o original"""
        if column not in df.columns:
            raise ValueError(f"Coluna '{column}' não encontrada no DataFrame")
        
        try:
            result_df = df.copy()
            result_df[column] = result_df[column].apply(self.encrypt_value)
            return result_df
        except Exception as e:
            logging.error(f"Erro ao criptografar coluna: {e}")
            return df

    def decrypt_value(self, encrypted_value):
        """Descriptografa um valor criptografado"""
        if pd.isnull(encrypted_value):
            return encrypted_value
            
        try:
            decrypted = self.cipher.decrypt(encrypted_value.encode()).decode()
            return decrypted
        except InvalidToken:
            logging.warning("Tentativa de descriptografia falhou - token inválido")
            return "[ERRO: Dados inválidos ou corrompidos]"
        except Exception as e:
            logging.error(f"Erro de descriptografia: {e}")
            return encrypted_value

    def decrypt_column(self, df, column):
        """Descriptografa uma coluna do DataFrame"""
        if column not in df.columns:
            raise ValueError(f"Coluna '{column}' não encontrada no DataFrame")
        
        try:
            result_df = df.copy()
            result_df[column] = result_df[column].apply(self.decrypt_value)
            return result_df
        except Exception as e:
            logging.error(f"Erro ao descriptografar coluna: {e}")
            return df