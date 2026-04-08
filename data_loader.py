import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import re

def conectar_drive():
    escopos = ["https://www.googleapis.com/auth/drive.readonly"]
    credenciais_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(credenciais_dict, scopes=escopos)
    return build('drive', 'v3', credentials=creds)

def carregar_todos_arquivos():
    servico = conectar_drive()
    # COLE O ID DA SUA PASTA AQUI
    id_pasta = '1Q1RlDAni03_7q8ypKG62hBG6jfa6yUAE' 
    query = f"'{id_pasta}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and trashed=false"
    
    arquivos = servico.files().list(q=query, fields="files(id, name)").execute().get('files', [])
    if not arquivos: return pd.DataFrame()

    dfs = []
    for arquivo in arquivos:
        requisicao = servico.files().get_media(fileId=arquivo['id'])
        memoria = io.BytesIO()
        baixador = MediaIoBaseDownload(memoria, requisicao)
        concluido = False
        while not concluido: _, concluido = baixador.next_chunk()
        memoria.seek(0)
        
        try:
            df_temp = pd.read_excel(memoria)
            coluna_titulo = str(df_temp.columns[0])
            partes = [p.strip() for p in coluna_titulo.split('-')]
            
            materia = partes[0] if len(partes) > 0 else "Desconhecida"
            serie = partes[1] if len(partes) > 1 else "Desconhecida"
            
            titulo_lower = coluna_titulo.lower()
            
            # Caçador de Módulo
            match_modulo = re.search(r'm[óo]dulo\s*(\d+)', titulo_lower)
            if match_modulo:
                etapa_nome = f"Módulo {match_modulo.group(1)}"
                etapa_num = int(match_modulo.group(1))
            else:
                etapa_nome = "Desconhecida"
                etapa_num = 0

            # Caçador de Tipo (Dose)
            if "mínima" in titulo_lower:
                tipo = "dose mínima"
            elif "leão" in titulo_lower:
                tipo = "dose para leão"
            else:
                tipo = "Padrão"
            
            df_temp.rename(columns={df_temp.columns[0]: 'nome'}, inplace=True)
            
            # Vacina anti-KeyError (procura a coluna de percentual correta)
            for col in df_temp.columns:
                if "percentual" in str(col).lower():
                    df_temp.rename(columns={col: "Percentual Realizado"}, inplace=True)
                    break
            
            df_temp["materia"] = materia
            df_temp["serie"] = serie
            df_temp["tipo"] = tipo
            df_temp["etapa_nome"] = etapa_nome
            df_temp["etapa_num"] = etapa_num
            
            dfs.append(df_temp)
        except Exception as erro:
            st.warning(f"Erro ao ler {arquivo['name']}: {erro}")

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
