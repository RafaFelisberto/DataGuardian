import pandas as pd
import json
import jsonlines
import logging
import re
from io import StringIO
from typing import List, Dict, Any, Tuple, Optional

logging.basicConfig(level=logging.INFO)


def process_file(uploaded_file) -> pd.DataFrame:
    """Processa arquivos carregados via Streamlit (UploadedFile)."""
    file_type = getattr(uploaded_file, "type", "")
    file_name = getattr(uploaded_file, "name", "uploaded")

    try:
        logging.info(f"Processando arquivo: {file_name} ({file_type})")

        content = uploaded_file.read()
        if not content:
            logging.error("Arquivo vazio")
            return pd.DataFrame()

        uploaded_file.seek(0)

        if file_type == "text/csv" or file_name.endswith(".csv"):
            df = pd.read_csv(StringIO(content.decode("utf-8", errors="replace")), on_bad_lines="skip")

        elif file_type == "application/json" or file_name.endswith(".json"):
            # Suporta JSONL disfarçado (um JSON por linha) e JSON lista/dict
            raw = content.decode("utf-8", errors="replace").strip()
            if not raw:
                return pd.DataFrame()
            if raw.startswith("[") or raw.startswith("{"):
                data = json.loads(raw)
                if isinstance(data, dict):
                    df = pd.DataFrame([data])
                else:
                    df = pd.DataFrame(data)
            else:
                data = [json.loads(line) for line in raw.splitlines() if line.strip()]
                df = pd.DataFrame(data)

        elif file_name.endswith(".jsonl"):
            with jsonlines.Reader(StringIO(content.decode("utf-8", errors="replace"))) as reader:
                data = list(reader)
            df = pd.DataFrame(data)

        elif file_type == "text/plain" or file_name.endswith(".txt"):
            df = pd.read_csv(StringIO(content.decode("utf-8", errors="replace")), delimiter="\t", on_bad_lines="skip")

        elif file_name.endswith(".sql"):
            sql_content = content.decode("utf-8", errors="replace")
            df = extract_sql_inserts_from_string(sql_content)

        else:
            raise ValueError(f"Formato de arquivo não suportado: {file_name}")

        if not df.empty:
            df.columns = df.columns.astype(str).str.lower().str.strip()
        return df

    except Exception as e:
        logging.error(f"Erro ao processar {file_name}: {e}", exc_info=True)
        return pd.DataFrame()


# --- SQL helpers (MVP) --------------------------------------------------------

_INSERT_RE = re.compile(
    r"INSERT\s+INTO\s+(?P<table>[`\"\[]?[\w\.]+[`\"\]]?)\s*(?:\((?P<cols>[^\)]*)\))?\s*VALUES\s*(?P<values>.+?);\s*",
    flags=re.IGNORECASE | re.DOTALL,
)


def extract_sql_inserts_from_string(sql_content: str) -> pd.DataFrame:
    """Extrai dados de INSERTs em SQL (suporta INSERT ... VALUES (...), (...);)."""
    rows: List[Dict[str, Any]] = []
    if not sql_content:
        return pd.DataFrame()

    for m in _INSERT_RE.finditer(sql_content):
        cols_raw = m.group("cols")
        cols = _parse_columns(cols_raw) if cols_raw else None
        tuples = _split_value_tuples(m.group("values"))

        for t in tuples:
            values = _split_fields(t)
            if cols and len(cols) == len(values):
                row = {c: _coerce_sql_value(v) for c, v in zip(cols, values)}
            else:
                # Sem colunas (ou mismatch): gera colunas genéricas
                row = {f"col_{i+1}": _coerce_sql_value(v) for i, v in enumerate(values)}
            rows.append(row)

    return pd.DataFrame(rows)


def _parse_columns(cols_raw: str) -> List[str]:
    cols = []
    for c in cols_raw.split(","):
        c = c.strip()
        c = c.strip("`\"[] ")
        if c:
            cols.append(c)
    return cols


def _split_value_tuples(values_block: str) -> List[str]:
    """Recebe a parte após VALUES e devolve uma lista de strings '(...)' sem os parênteses externos."""
    s = values_block.strip()
    out = []
    i = 0
    depth = 0
    start = None
    in_str = False
    str_char = ""
    while i < len(s):
        ch = s[i]
        if in_str:
            if ch == str_char:
                # trata escape por duplicação '' dentro de string SQL
                if i + 1 < len(s) and s[i + 1] == str_char:
                    i += 1
                else:
                    in_str = False
            i += 1
            continue

        if ch in ("'", '"'):
            in_str = True
            str_char = ch
            i += 1
            continue

        if ch == "(":
            if depth == 0:
                start = i + 1
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and start is not None:
                out.append(s[start:i])
                start = None
        i += 1
    return out


def _split_fields(tuple_content: str) -> List[str]:
    """Split por vírgula respeitando strings."""
    fields = []
    cur = []
    in_str = False
    str_char = ""
    i = 0
    while i < len(tuple_content):
        ch = tuple_content[i]
        if in_str:
            cur.append(ch)
            if ch == str_char:
                # escape '' ou ""
                if i + 1 < len(tuple_content) and tuple_content[i + 1] == str_char:
                    cur.append(tuple_content[i + 1])
                    i += 1
                else:
                    in_str = False
            i += 1
            continue

        if ch in ("'", '"'):
            in_str = True
            str_char = ch
            cur.append(ch)
            i += 1
            continue

        if ch == ",":
            fields.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1

    if cur:
        fields.append("".join(cur).strip())
    return fields


def _coerce_sql_value(v: str) -> Any:
    v = v.strip()
    if not v:
        return v
    if v.upper() == "NULL":
        return None
    # remove aspas
    if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
        inner = v[1:-1]
        # unescape duplicação de aspas
        inner = inner.replace("''", "'").replace('""', '"')
        return inner
    # tenta número
    try:
        if re.fullmatch(r"-?\d+", v):
            return int(v)
        if re.fullmatch(r"-?\d+\.\d+", v):
            return float(v)
    except Exception:
        pass
    return v
