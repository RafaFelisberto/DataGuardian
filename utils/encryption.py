from cryptography.fernet import Fernet
import os

class DataEncryptor:
    def __init__(self, key_path="encryption_key.key"):
        self.key_path = key_path
        if not os.path.exists(key_path):
            self.generate_key()
        self.key = open(key_path, "rb").read()
        self.cipher = Fernet(self.key)
    
    def generate_key(self):
        with open(self.key_path, "wb") as key_file:
            key_file.write(Fernet.generate_key())
    
    def encrypt_column(self, df, column):
        df[column] = df[column].apply(
            lambda x: self.cipher.encrypt(x.encode()).decode() 
            if pd.notnull(x) else x
        )
        return df