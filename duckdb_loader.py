"""
📊 duckdb_loader.py
Carrega dados do DuckDB (gerado por data_sync.py).
Muito mais rápido que carregar do Google Drive a cada execução!
"""

import json
import pandas as pd
import duckdb
from datetime import datetime

ARQUIVO_DUCKDB = "dados_tarefas.duckdb"
ARQUIVO_METADATA = "ultimo_update.json"

# ─────────────────────────────────────────────────────────────────────────────
# 📥 CARREGAR DO DUCKDB
# ─────────────────────────────────────────────────────────────────────────────
def carregar_dados_duckdb():
    """
    Carrega dados do DuckDB.
    
    Returns:
        pd.DataFrame: Dados de tarefas dos alunos
        
    Raises:
        FileNotFoundError: Se o DuckDB não existir
    """
    try:
        conn = duckdb.connect(ARQUIVO_DUCKDB, read_only=True)
        df = conn.execute("SELECT * FROM tarefas").fetchdf()
        conn.close()
        return df
    except FileNotFoundError:
        raise FileNotFoundError(
            f"❌ Banco de dados {ARQUIVO_DUCKDB} não encontrado! "
            "Execute data_sync.py primeiro ou aguarde a próxima sincronização do GitHub Actions."
        )
    except Exception as erro:
        raise RuntimeError(f"❌ Erro ao carregar DuckDB: {erro}")

# ─────────────────────────────────────────────────────────────────────────────
# ⏰ OBTER TIMESTAMP DA ÚLTIMA ATUALIZAÇÃO
# ─────────────────────────────────────────────────────────────────────────────
def obter_ultimo_update():
    """
    Retorna data/hora da última sincronização dos dados.
    
    Returns:
        dict: {'timestamp': '2024-01-15T14:30:00', 'formatado': '15/01/2024 às 14:30', 'datetime': datetime_obj}
    """
    try:
        with open(ARQUIVO_METADATA, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        timestamp_str = metadata.get("ultimo_update", "Desconhecido")
        
        # Converter para datetime
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        # Formatar de forma amigável
        formatado = dt.strftime("%d/%m/%Y às %H:%M")
        
        return {
            "timestamp": timestamp_str,
            "formatado": formatado,
            "datetime": dt,
            "total_registros": metadata.get("total_registros", 0),
            "materias": metadata.get("materias", []),
            "series": metadata.get("series", []),
        }
    
    except FileNotFoundError:
        return {
            "timestamp": "Nunca",
            "formatado": "Nunca atualizado",
            "datetime": None,
            "total_registros": 0,
            "materias": [],
            "series": [],
        }
    except Exception as erro:
        return {
            "timestamp": f"Erro: {erro}",
            "formatado": "Erro ao ler metadados",
            "datetime": None,
            "total_registros": 0,
            "materias": [],
            "series": [],
        }

# ─────────────────────────────────────────────────────────────────────────────
# 🔍 FUNÇÃO COMPATÍVEL COM CÓDIGO EXISTENTE
# ─────────────────────────────────────────────────────────────────────────────
def carregar_todos_arquivos():
    """
    Compatibilidade com o nome original de data_loader.py.
    Simplesmente chama carregar_dados_duckdb().
    """
    return carregar_dados_duckdb()
