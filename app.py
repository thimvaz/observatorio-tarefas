import streamlit as st
import pandas as pd
import os
from data_loader import carregar_todos_arquivos

st.set_page_config(page_title="Painel de Tarefas", page_icon="📚", layout="wide")


# ── Logo da Escola ───────────────────────────────────────────────────────────
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

# ── Autenticação ─────────────────────────────────────────────────────────────
def verificar_senha():
    """Retorna True se o usuário digitar a senha correta."""
    
    def senha_inserida():
        """Verifica se a senha digitada bate com a do secrets.toml"""
        if st.session_state["senha_digitada"] == st.secrets["geral"]["senha_acesso"]:
            st.session_state["senha_correta"] = True
            del st.session_state["senha_digitada"]  # Apaga a senha da memória por segurança
        else:
            st.session_state["senha_correta"] = False

    if "senha_correta" not in st.session_state:
        # Primeira vez que abre a página: mostra o campo de senha
        st.text_input("🔑 Digite a senha de acesso da coordenação", type="password", on_change=senha_inserida, key="senha_digitada")
        return False
    elif not st.session_state["senha_correta"]:
        # Errou a senha: mostra o campo de novo com mensagem de erro
        st.text_input("🔑 Digite a senha de acesso da coordenação", type="password", on_change=senha_inserida, key="senha_digitada")
        st.error("😕 Senha incorreta.")
        return False
    else:
        # Senha correta: libera o acesso
        return True

# ── O GARGALO DE SEGURANÇA ──
if not verificar_senha():
    st.stop()  # O código morre aqui se a senha não for validada. Nada abaixo disso carrega.

# ... Daqui para baixo continua o seu código normal (CSS, carregamento de dados, etc.) ...

st.markdown("""
<style>
.alerta-card { background: #fff3cd; border-left: 5px solid #ff6b00; border-radius: 6px; padding: 12px 18px; margin-bottom: 8px; }
.alerta-card b { color: #7a3800; }
.alerta-card small { color: #555; }
</style>
""", unsafe_allow_html=True)

# ── Título Principal ─────────────────────────────────────────────────────────
st.title("🔭 Observatório das Tarefas")

PERCENTUAL_MINIMO = 50
MIN_TAREFAS_ALERTA = 3

@st.cache_data(ttl=300)
def get_dados():
    return carregar_todos_arquivos()

with st.spinner("Carregando dados do Drive..."):
    df = get_dados()

if df.empty:
    st.error("Nenhum arquivo encontrado.")
    st.stop()

# ── Pré-processamento ────────────────────────────────────────────────────────
df.columns = df.columns.str.strip()

# BUSCA DINÂMICA (Anti-KeyError)
# Procura qualquer coluna que tenha a palavra "percentual" no nome, não importa como a plataforma exportou
colunas_perc = [col for col in df.columns if "percentual" in col.lower()]

if colunas_perc:
    nome_col_exata = colunas_perc[0]
    df["percentual_num"] = df[nome_col_exata].astype(str).str.replace("%", "", regex=False).astype(float)
else:
    st.error(f"Erro Crítico: Não achamos a coluna de notas. O Excel veio com estas colunas: {list(df.columns)}")
    st.stop()

# Blinda a Matrícula e extrai a turma
df["Matrícula"] = df["Matrícula"].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '0')
df["turma_letra"] = df["Turma"].astype(str).str.extract(r"([A-Z])$")

# Alertas
tarefas_abaixo = df[df["percentual_num"] < PERCENTUAL_MINIMO]
acumulo = (
    tarefas_abaixo.groupby(["nome", "Matrícula", "serie", "Turma"])
    .size()
    .reset_index(name="qtd_tarefas")
    .query("qtd_tarefas >= @MIN_TAREFAS_ALERTA")
    .sort_values("qtd_tarefas", ascending=False)
)

if not acumulo.empty:
    with st.expander(f"🚨 {len(acumulo)} aluno(s) com {MIN_TAREFAS_ALERTA}+ tarefas abaixo de {PERCENTUAL_MINIMO}%", expanded=False):
        for _, row in acumulo.iterrows():
            st.markdown(f"<div class='alerta-card'><b>{row['nome']}</b> — RM {row['Matrícula']}<br><small>{row['Turma']} · {row['qtd_tarefas']} tarefas pendentes</small></div>", unsafe_allow_html=True)

st.divider()

aba_turma, aba_aluno = st.tabs(["📋 Por Turma / Avaliação", "🔍 Buscar Aluno"])

with aba_turma:
    c1, c2, c3, c4 = st.columns(4)
    
    serie_sel = c1.selectbox("Série", sorted(df["serie"].unique()))
    df_serie = df[df["serie"] == serie_sel]

    turma_sel = c2.selectbox("Turma", ["Todas"] + list(sorted(df_serie["turma_letra"].dropna().unique())))
    materia_sel = c3.selectbox("Matéria", ["Todas"] + list(sorted(df_serie["materia"].unique())))
    etapa_sel = c4.selectbox("Módulo / Ciclo", ["Todos"] + list(sorted(df_serie["etapa_nome"].unique())))

    tipo_sel = st.radio("Tipo de tarefa", ["Todos", "dose mínima", "dose para leão"], horizontal=True)

    # Aplica filtros
    df_filtrado = df_serie.copy()
    if turma_sel != "Todas": df_filtrado = df_filtrado[df_filtrado["turma_letra"] == turma_sel]
    if materia_sel != "Todas": df_filtrado = df_filtrado[df_filtrado["materia"] == materia_sel]
    if etapa_sel != "Todos": df_filtrado = df_filtrado[df_filtrado["etapa_nome"] == etapa_sel]
    if tipo_sel != "Todos": df_filtrado = df_filtrado[df_filtrado["tipo"] == tipo_sel]

    # Métricas
    if not df_filtrado.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Alunos", df_filtrado["nome"].nunique())
        m2.metric("Tarefas", len(df_filtrado))
        m3.metric("Média geral", f"{df_filtrado['percentual_num'].mean():.0f}%")
        m4.metric("Com 0%", f"{(df_filtrado['percentual_num'] == 0).mean() * 100:.0f}%")

    st.divider()

    colunas_exibir = {
        "nome": "Aluno", "Matrícula": "RM", "Turma": "Turma", 
        "materia": "Matéria", "etapa_nome": "Etapa", "tipo": "Tipo", "percentual_num": "% Realizado"
    }
    df_exib = df_filtrado[list(colunas_exibir.keys())].rename(columns=colunas_exibir).sort_values(["Turma", "Aluno"])

    def colorir(val):
        if val == 0: return "background-color: #ffd6d6; color: black"
        if val < PERCENTUAL_MINIMO: return "background-color: #fff3cd; color: black"
        return "background-color: #d4edda; color: black"

    st.dataframe(df_exib.style.map(colorir, subset=["% Realizado"]).format({"% Realizado": "{:.0f}%"}).hide(axis="index"), use_container_width=True, height=500)

with aba_aluno:
    busca = st.text_input("🔍 Digite o nome ou RM")
    if busca.strip():
        mask = df["nome"].str.contains(busca, case=False, na=False) | df["Matrícula"].str.contains(busca, case=False, na=False)
        df_aluno = df[mask]

        if not df_aluno.empty:
            nomes = df_aluno["nome"].unique()
            if len(nomes) > 1: df_aluno = df_aluno[df_aluno["nome"] == st.selectbox("Selecione o aluno", sorted(nomes))]

            info = df_aluno.iloc[0]
            st.subheader(f"📌 {info['nome']}")
            st.caption(f"RM: {info['Matrícula']} · {info['Turma']}")

            c1, c2, c3 = st.columns(3)
            c1.metric("Tarefas registradas", len(df_aluno))
            c2.metric("Média", f"{df_aluno['percentual_num'].mean():.0f}%")
            c3.metric(f"Abaixo de {PERCENTUAL_MINIMO}%", (df_aluno["percentual_num"] < PERCENTUAL_MINIMO).sum())

            colunas = {
                "serie": "Série", "materia": "Matéria", "etapa_nome": "Etapa", 
                "tipo": "Tipo", "percentual_num": "% Realizado"
            }
            # Se existirem as colunas de listas/questões (varia por arquivo), tenta puxar também
            if "Listas realizadas" in df_aluno.columns: colunas["Listas realizadas"] = "Listas feitas"
            if "Questões realizadas" in df_aluno.columns: colunas["Questões realizadas"] = "Questões feitas"

            df_hist = df_aluno[list(colunas.keys())].rename(columns=colunas).sort_values(["Série", "Matéria", "Etapa"])
            st.dataframe(df_hist.style.map(colorir, subset=["% Realizado"]).format({"% Realizado": "{:.0f}%"}).hide(axis="index"), use_container_width=True)
        else:
            st.warning("Nenhum aluno encontrado.")
# ── Rodapé ───────────────────────────────────────────────────────────────────
st.markdown("""
    <hr style='margin-top: 50px; margin-bottom: 20px;'>
    <div style='text-align: center; color: #888888; font-size: 14px; padding-bottom: 20px;'>
        Feito pelo Vaz
    </div>
""", unsafe_allow_html=True)
