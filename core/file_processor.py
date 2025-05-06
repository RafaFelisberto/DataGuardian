import pandas as pd
import sqlparse  # Para SQL dumps
import jsonlines  # Para arquivos .jsonl
import logging
import json

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

def process_file(file_path):
    try:
        if file_path.endswith('.csv'):
            logging.debug(f"Lendo CSV: {file_path}")
            df = pd.read_csv(file_path, on_bad_lines='skip')
        
        elif file_path.endswith('.json'):
            logging.debug(f"Lendo JSON: {file_path}")
            with open(file_path, 'r') as f:
                data = [json.loads(line) for line in f if line.strip()]
            df = pd.DataFrame(data)
        
        elif file_path.endswith('.jsonl'):
            logging.debug(f"Lendo JSONL: {file_path}")
            with jsonlines.open(file_path) as reader:
                data = list(reader)
            df = pd.DataFrame(data)
        
        elif file_path.endswith('.txt'):
            logging.debug(f"Lendo TXT: {file_path}")
            df = pd.read_csv(file_path, delimiter='\t', on_bad_lines='skip')
        
        elif file_path.endswith('.sql'):
            logging.debug(f"Lendo SQL: {file_path}")
            df = extract_sql_data(file_path)
        
        else:
            raise ValueError(f"Formato de arquivo não suportado: {file_path}")
        
        if df.empty:
            logging.warning("DataFrame vazio após leitura")
            return df
        
        df.columns = df.columns.str.lower()
        return df
    
    except Exception as e:
        logging.error(f"Erro ao processar {file_path}: {e}", exc_info=True)
        return pd.DataFrame()

def extract_sql_data(sql_file):
    """
    Extrai dados de INSERTs em arquivos SQL.
    """
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    statements = sqlparse.parse(sql_content)
    data = []
    
    for stmt in statements:
        if stmt.get_type() == 'INSERT':
            values = stmt.values()
            if values:
                data.append(values)
    
    return pd.DataFrame(data)