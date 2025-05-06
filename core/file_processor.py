import pandas as pd
import sqlparse
import json
import jsonlines
import logging
import os
from io import StringIO

logging.basicConfig(level=logging.INFO)

def process_file(uploaded_file):
    """
    Processa arquivos carregados via Streamlit (UploadedFile).
    """
    try:
        # Log do tipo do arquivo
        file_type = uploaded_file.type
        file_name = uploaded_file.name
        logging.info(f"Processando arquivo: {file_name} ({file_type})")

        # Carrega o conteúdo do arquivo para memória
        content = uploaded_file.read()
        if not content:
            logging.error("Arquivo vazio")
            return pd.DataFrame()

        # Reinicia o cursor do arquivo para leitura múltipla
        uploaded_file.seek(0)

        # Detecta tipo e processa
        if file_type == "text/csv" or file_name.endswith(".csv"):
            df = pd.read_csv(StringIO(content.decode("utf-8")), on_bad_lines='skip')

        elif file_type == "application/json" or file_name.endswith(".json"):
            data = [json.loads(line) for line in StringIO(content.decode("utf-8")) if line.strip()]
            df = pd.DataFrame(data)

        elif file_name.endswith(".jsonl"):
            with jsonlines.Reader(StringIO(content.decode("utf-8"))) as reader:
                data = list(reader)
            df = pd.DataFrame(data)

        elif file_type == "text/plain" or file_name.endswith(".txt"):
            df = pd.read_csv(StringIO(content.decode("utf-8")), delimiter='\t', on_bad_lines='skip')

        elif file_name.endswith(".sql"):
            sql_content = content.decode("utf-8")
            df = extract_sql_data(sql_content)

        else:
            raise ValueError(f"Formato de arquivo não suportado: {file_name}")

        # Padroniza nomes de colunas
        if not df.empty:
            df.columns = df.columns.str.lower()
        return df

    except Exception as e:
        logging.error(f"Erro ao processar {file_name}: {e}", exc_info=True)
        return pd.DataFrame()

def extract_sql_data(sql_content):
    """Extrai dados de INSERTs em arquivos SQL"""
    try:
        statements = sqlparse.parse(sql_content)
        data = []
        for stmt in statements:
            if stmt.get_type() == "INSERT":
                values = stmt.values()
                if values:
                    data.append(values)
        return pd.DataFrame(data)
    except Exception as e:
        logging.error(f"Erro ao processar SQL: {e}")
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