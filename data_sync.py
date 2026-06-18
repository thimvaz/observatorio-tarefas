"""
🔄 data_sync.py
Script que sincroniza dados do Google Drive para DuckDB.
Roda via GitHub Actions (3x/dia).

Fluxo:
1. Conecta ao Google Drive (credenciais via env var)
2. Carrega todos os arquivos xlsx da pasta designada
3. Processa e normaliza os dados
4. Salva em um banco DuckDB local
5. Registra timestamp da última atualização
"""

import os
import io
import re
import json
from datetime import datetime
import pandas as pd
import duckdb
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ─────────────────────────────────────────────────────────────────────────────
# ⚙️ CONFIGURAÇÕES
# ─────────────────────────────────────────────────────────────────────────────
PASTA_DRIVE_ID = '1Q1RlDAni03_7q8ypKG62hBG6jfa6yUAE'  # Substitua pelo seu
ARQUIVO_DUCKDB = 'dados_tarefas.duckdb'
ARQUIVO_METADATA = 'ultimo_update.json'

# ─────────────────────────────────────────────────────────────────────────────
# 🔐 CONECTAR AO GOOGLE DRIVE
# ─────────────────────────────────────────────────────────────────────────────
def conectar_drive():
    """Conecta ao Google Drive usando credenciais de serviço."""
    escopos = ["https://www.googleapis.com/auth/drive.readonly"]
    
    # Busca credenciais na variável de ambiente (GitHub Secrets)
    credenciais_json = os.getenv("GCP_SERVICE_ACCOUNT")
    if not credenciais_json:
        raise ValueError("⚠️  Variável GCP_SERVICE_ACCOUNT não encontrada!")
    
    credenciais_dict = json.loads(credenciais_json)
    creds = Credentials.from_service_account_info(credenciais_dict, scopes=escopos)
    return build('drive', 'v3', credentials=creds)

# ─────────────────────────────────────────────────────────────────────────────
# 📥 CARREGAR DADOS DO DRIVE
# ─────────────────────────────────────────────────────────────────────────────
def carregar_todos_arquivos():
    """
    Carrega todos os arquivos xlsx da pasta do Drive.
    Processa título para extrair: matéria, série, módulo, tipo.
    """
    print("🔗 Conectando ao Google Drive...")
    servico = conectar_drive()
    
    # Buscar arquivos xlsx na pasta
    query = f"'{PASTA_DRIVE_ID}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and trashed=false"
    arquivos = servico.files().list(q=query, fields="files(id, name)").execute().get('files', [])
    
    if not arquivos:
        print("⚠️  Nenhum arquivo encontrado na pasta!")
        return pd.DataFrame()
    
    print(f"📄 Encontrados {len(arquivos)} arquivo(s)")
    
    dfs = []
    for idx, arquivo in enumerate(arquivos, 1):
        try:
            print(f"  ⬇️  [{idx}/{len(arquivos)}] Baixando: {arquivo['name']}")
            
            # Baixar arquivo do Drive
            requisicao = servico.files().get_media(fileId=arquivo['id'])
            memoria = io.BytesIO()
            baixador = MediaIoBaseDownload(memoria, requisicao)
            concluido = False
            while not concluido:
                _, concluido = baixador.next_chunk()
            
            memoria.seek(0)
            df_temp = pd.read_excel(memoria)
            
            # ─── Processar título (primeira coluna) ───────────────────────────
            coluna_titulo = str(df_temp.columns[0])
            partes = [p.strip() for p in coluna_titulo.split('-')]
            
            materia = partes[0] if len(partes) > 0 else "Desconhecida"
            serie = partes[1] if len(partes) > 1 else "Desconhecida"
            
            titulo_lower = coluna_titulo.lower()
            
            # Extrair módulo
            match_modulo = re.search(r'm[óo]dulo\s*(\d+)', titulo_lower)
            if match_modulo:
                etapa_nome = f"Módulo {match_modulo.group(1)}"
                etapa_num = int(match_modulo.group(1))
            else:
                etapa_nome = "Desconhecida"
                etapa_num = 0
            
            # Extrair tipo (dose)
            if "mínima" in titulo_lower:
                tipo = "dose mínima"
            elif "leão" in titulo_lower:
                tipo = "dose para leão"
            else:
                tipo = "Padrão"
            
            # ─── Renomear colunas ───────────────────────────────────────────
            df_temp.rename(columns={df_temp.columns[0]: 'nome'}, inplace=True)
            
            # Encontrar coluna de percentual
            for col in df_temp.columns:
                if "percentual" in str(col).lower():
                    df_temp.rename(columns={col: "percentual_realizado"}, inplace=True)
                    break
            
            # ─── Adicionar metadados ─────────────────────────────────────────
            df_temp["materia"] = materia
            df_temp["serie"] = serie
            df_temp["tipo"] = tipo
            df_temp["etapa_nome"] = etapa_nome
            df_temp["etapa_num"] = etapa_num
            
            # Garantir que Matrícula seja string
            if "Matrícula" in df_temp.columns:
                df_temp["Matrícula"] = df_temp["Matrícula"].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '0')
            
            # Converter percentual para float
            if "percentual_realizado" in df_temp.columns:
                df_temp["percentual_realizado"] = (
                    df_temp["percentual_realizado"]
                    .astype(str)
                    .str.replace("%", "", regex=False)
                    .astype(float)
                )
            
            dfs.append(df_temp)
            print(f"    ✅ {arquivo['name']} processado ({len(df_temp)} linhas)")
            
        except Exception as erro:
            print(f"    ❌ Erro em {arquivo['name']}: {erro}")
    
    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)
        print(f"\n✅ Total: {len(df_final)} registros carregados")
        return df_final
    else:
        print("❌ Nenhum dado foi processado com sucesso")
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# 💾 SALVAR EM DUCKDB
# ─────────────────────────────────────────────────────────────────────────────
def salvar_em_duckdb(df):
    """Salva DataFrame em DuckDB, substituindo a tabela anterior."""
    print(f"\n📊 Salvando em DuckDB: {ARQUIVO_DUCKDB}")
    
    conn = duckdb.connect(ARQUIVO_DUCKDB)
    
    # Criar/substituir tabela
    conn.execute("DROP TABLE IF EXISTS tarefas")
    conn.execute("CREATE TABLE tarefas AS SELECT * FROM df")
    
    # Registrar timestamp
    timestamp_str = datetime.now().isoformat()
    print(f"⏰ Última atualização: {timestamp_str}")
    
    # Salvar metadados em JSON
    metadata = {
        "ultimo_update": timestamp_str,
        "total_registros": len(df),
        "materias": list(df["materia"].unique()),
        "series": list(df["serie"].unique()),
    }
    
    with open(ARQUIVO_METADATA, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    conn.close()
    print("✅ Dados salvos com sucesso!")
    
    return timestamp_str

# ─────────────────────────────────────────────────────────────────────────────
# 🚀 MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("🔄 SINCRONIZANDO DADOS — Google Drive → DuckDB")
    print("=" * 70)
    
    try:
        # Carregar dados do Drive
        df = carregar_todos_arquivos()
        
        if df.empty:
            print("⚠️  Nenhum dado para salvar")
        else:
            # Salvar em DuckDB
            timestamp = salvar_em_duckdb(df)
            print("\n" + "=" * 70)
            print(f"✅ SINCRONIZAÇÃO CONCLUÍDA em {timestamp}")
            print("=" * 70)
    
    except Exception as erro:
        print(f"\n❌ ERRO NA SINCRONIZAÇÃO: {erro}")
        exit(1)
