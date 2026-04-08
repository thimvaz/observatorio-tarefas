import streamlit as st
import pandas as pd
import os
import re
from data_loader import carregar_todos_arquivos

st.set_page_config(page_title="Painel de Tarefas", page_icon="📚", layout="wide")

# ── Logo da Escola ───────────────────────────────────────────────────────────
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

# ── CSS mínimo ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
.alerta-card { background: #fff3cd; border-left: 5px solid #ff6b00; border-radius: 6px; padding: 12px 18px; margin-bottom: 8px; }
.alerta-card b { color: #7a3800; }
.alerta-card small { color: #555; }
</style>
""", unsafe_allow_html=True)

# ── Autenticação ─────────────────────────────────────────────────────────────
def verificar_senha():
    def senha_inserida():
        if st.session_state["senha_digitada"] == st.secrets["geral"]["senha_acesso"]:
            st.session_state["senha_correta"] = True
            del st.session_state["senha_digitada"]
        else:
            st.session_state["senha_correta"] = False

    if "senha_correta" not in st.session_state:
        st.text_input("🔑 Digite a senha de acesso da coordenação", type="password", on_change=senha_inserida, key="senha_digitada")
        return False
    elif not st.session_state["senha_correta"]:
        st.text_input("🔑 Digite a senha de acesso da coordenação", type="password", on_change=senha_inserida, key="senha_digitada")
        st.error("😕 Senha incorreta.")
        return False
    else:
        return True

if not verificar_senha():
    st.stop()

# ── Título Principal ─────────────────────────────────────────────────────────
st.title("🔭 Observatório das Tarefas")

PERCENTUAL_MINIMO = 50
MIN_TAREFAS_ALERTA = 3

@st.cache_data(ttl=300)
def get_dados():
    return carregar_todos_arquivos()

with st.spinner("Carregando dados... Aperte a tecla 'C' se a página travar no cache!"):
    df = get_dados()

if df.empty:
    st.error("Nenhum arquivo encontrado. Verifique a pasta do Drive.")
    st.stop()

# ── Pré-processamento ────────────────────────────────────────────────────────
df.columns = df.columns.str.strip()

colunas_perc = [col for col in df.columns if "percentual" in col.lower()]
if colunas_perc:
    df["percentual_num"] = df[colunas_perc[0]].astype(str).str.replace("%", "", regex=False).astype(float)
else:
    st.error("Erro Crítico: Coluna de percentual não encontrada.")
    st.stop()

df["Matrícula"] = df["Matrícula"].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '0')


# ── ALERTAS GLOBAIS ──────────────────────────────────────────────────────────
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

# ── ABAS ─────────────────────────────────────────────────────────────────────
aba_turma, aba_aluno = st.tabs(["📊 Comparativo Cruzado", "🔍 Buscar Aluno"])

# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — COMPARATIVO CRUZADO (Multi-Seleção)
# ══════════════════════════════════════════════════════════════════════════════
with aba_turma:
    # Linha 1: Filtros Estruturais
    c1, c2, c3 = st.columns(3)
    
    serie_sel = c1.selectbox("Série", sorted(df["serie"].unique()))
    df_serie = df[df["serie"] == serie_sel]

    turma_sel = c2.selectbox("Turma", ["Todas"] + list(sorted(df_serie["Turma"].dropna().unique())))
    tipo_sel = c3.selectbox("Tipo de Tarefa", ["Todos", "dose mínima", "dose para leão"])

    # Linha 2: Filtros de Cruzamento (Multi-seleção com mais espaço)
    c_mat, c_mod = st.columns(2)
    
    materias_disp = sorted(df_serie["materia"].unique())
    # O default será a primeira matéria da lista para a tabela não iniciar vazia
    materias_sel = c_mat.multiselect("📚 Matérias", materias_disp, default=materias_disp[:1])

    # A lista de módulos disponíveis muda dependendo das matérias escolhidas
    df_temp = df_serie[df_serie["materia"].isin(materias_sel)]
    modulos_disp = sorted(df_temp["etapa_nome"].unique(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
    
    # O default seleciona todos os módulos das matérias escolhidas
    modulos_sel = c_mod.multiselect("🎯 Módulos", modulos_disp, default=modulos_disp)

    # Aplica todos os filtros
    df_filtrado = df_temp[df_temp["etapa_nome"].isin(modulos_sel)].copy()
    if turma_sel != "Todas": df_filtrado = df_filtrado[df_filtrado["Turma"] == turma_sel]
    if tipo_sel != "Todos": df_filtrado = df_filtrado[df_filtrado["tipo"] == tipo_sel]

    if df_filtrado.empty:
        st.info("Nenhum dado encontrado. Selecione pelo menos uma Matéria e um Módulo.")
    else:
        # Cria uma coluna composta para a visualização (ex: "CIÊNCIAS - Módulo 2")
        df_filtrado["coluna_pivot"] = df_filtrado["materia"] + " - " + df_filtrado["etapa_nome"]

        # Cria a Tabela Dinâmica
        tabela_comparativa = df_filtrado.pivot_table(
            index=["nome"], 
            columns="coluna_pivot", 
            values="percentual_num",
            aggfunc="mean"
        ).reset_index()

        # Ordena as colunas alfabeticamente pela matéria e numericamente pelo módulo
        def chave_ordenacao(nome_coluna):
            if nome_coluna == "nome": return ("", 0)
            partes = nome_coluna.split(" - ")
            materia = partes[0]
            mod_num = int(re.search(r'\d+', partes[1]).group()) if len(partes)>1 and re.search(r'\d+', partes[1]) else 0
            return (materia, mod_num)

        colunas_ordenadas = sorted(tabela_comparativa.columns, key=chave_ordenacao)
        tabela_comparativa = tabela_comparativa[colunas_ordenadas]
        tabela_comparativa.rename(columns={"nome": "Aluno"}, inplace=True)

        colunas_dados = [col for col in tabela_comparativa.columns if col != "Aluno"]

        def colorir(val):
            if pd.isna(val): return "" # Células vazias
            if val == 0: return "background-color: #ffd6d6; color: black"
            if val < PERCENTUAL_MINIMO: return "background-color: #fff3cd; color: black"
            return "background-color: #d4edda; color: black"

        st.dataframe(
            tabela_comparativa.style.map(colorir, subset=colunas_dados)
                                    .format("{:.0f}%", na_rep="-", subset=colunas_dados),
            use_container_width=True, 
            height=600,
            hide_index=True
        )

# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — BUSCA POR ALUNO
# ══════════════════════════════════════════════════════════════════════════════
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

            colunas = {
                "materia": "Matéria", "etapa_nome": "Módulo", 
                "tipo": "Tipo", "percentual_num": "% Realizado"
            }
            df_hist = df_aluno[list(colunas.keys())].rename(columns=colunas).sort_values(["Matéria", "Módulo"])
            
            def colorir_simples(val):
                if val == 0: return "background-color: #ffd6d6; color: black"
                if val < PERCENTUAL_MINIMO: return "background-color: #fff3cd; color: black"
                return "background-color: #d4edda; color: black"

            st.dataframe(df_hist.style.map(colorir_simples, subset=["% Realizado"]).format({"% Realizado": "{:.0f}%"}).hide(axis="index"), use_container_width=True)
        else:
            st.warning("Nenhum aluno encontrado.")

# ── Rodapé ───────────────────────────────────────────────────────────────────
st.markdown("""
    <hr style='margin-top: 50px; margin-bottom: 20px;'>
    <div style='text-align: center; color: #888888; font-size: 14px; padding-bottom: 20px;'>
        Feito pelo Vaz
    </div>
""", unsafe_allow_html=True)
