import pandas as pd
import json
import sqlparse

def process_file(file_path):
    """Processa diferentes formatos de arquivos"""
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.json'):
        with open(file_path) as f:
            return pd.DataFrame(json.load(f))
    elif file_path.endswith('.sql'):
        with open(file_path) as f:
            parsed = sqlparse.parse(f.read())
            # Lógica para extrair dados de INSERTs
            return extract_sql_data(parsed)
    return pd.read_csv(file_path, delimiter='\t')  # Para .txt logs