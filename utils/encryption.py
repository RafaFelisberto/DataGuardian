from __future__ import annotations

from cryptography.fernet import Fernet
import os
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)


class DataEncryptor:
    """Fernet-based encryption for dataframe columns.

    Safe-by-default:
    - By default, requires key via env DATAGUARDIAN_ENCRYPTION_KEY
    - File-based key is only allowed if allow_file_key=True
    """

    def __init__(
        self,
        *,
        use_env_key: bool = True,
        allow_file_key: bool = False,
        key_path: str = "encryption_key.key",
    ):
        self.use_env_key = use_env_key
        self.allow_file_key = allow_file_key
        self.key_path = key_path

        self.key = self._load_key()
        self.cipher = Fernet(self.key)

    def _load_key(self) -> bytes:
        if self.use_env_key:
            env_key = os.getenv("DATAGUARDIAN_ENCRYPTION_KEY")
            if env_key:
                return env_key.encode()
            raise ValueError("Chave não encontrada em DATAGUARDIAN_ENCRYPTION_KEY")

        if not self.allow_file_key:
            raise ValueError("Chave em arquivo desabilitada. Use DATAGUARDIAN_ENCRYPTION_KEY ou allow_file_key=True.")

        if not os.path.exists(self.key_path):
            self.generate_key()

        with open(self.key_path, "rb") as key_file:
            return key_file.read()

    def generate_key(self) -> None:
        if not self.allow_file_key:
            raise ValueError("Geração de chave em arquivo desabilitada (allow_file_key=False).")

        key = Fernet.generate_key()
        with open(self.key_path, "wb") as key_file:
            key_file.write(key)
        os.chmod(self.key_path, 0o600)
        logging.info("Nova chave de criptografia gerada em disco (arquivo protegido).")

    def encrypt_value(self, value):
        if pd.isnull(value):
            return value
        str_value = str(value)
        return self.cipher.encrypt(str_value.encode()).decode()

    def encrypt_column(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        if column not in df.columns:
            raise ValueError(f"Coluna '{column}' não existe no DataFrame")
        out = df.copy()
        out[column] = out[column].apply(self.encrypt_value)
        return out
